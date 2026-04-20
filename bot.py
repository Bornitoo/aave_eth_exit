#!/usr/bin/env python3
"""
Aave Liquidity Monitor — Telegram bot.

Access control
--------------
Every interaction is gated behind a subscription check to CHANNEL (@qrqlcrypto).
If the user is not subscribed they see a gate message with a link to the channel
and an inline "Check subscription" button.  Only after confirmation does the
persistent reply keyboard appear.

Persistent reply keyboard:
  [📊 Status]  [⛓️ Monitor]  [🎯 Alert Threshold]
  [🇬🇧 EN / 🇷🇺 RU]          [❓ Help]

Network/asset selection uses a two-level inline keyboard:
  Level 1 — list of networks (tap to drill in)
  Level 2 — list of assets for the selected network (toggle + back)

Selections are stored as "net:asset" strings, e.g. ["ethereum:eth", "mantle:usdc"].

Monitor alerts are rate-limited to at most one message per ALERT_COOLDOWN seconds
per user per (network, asset) pair.  System messages bypass the cooldown.

Admin (ADMIN_ID) receives a one-time notification when each new user first interacts.
"""
import asyncio
import json
import logging
import os
import time
from decimal import Decimal, InvalidOperation

from dotenv import load_dotenv
from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
    Update,
)
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

import db
from monitor import NETWORKS, fetch_state
from i18n import t

# ── Config ────────────────────────────────────────────────────────────────────

load_dotenv("settings.env")

logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    level=logging.INFO,
)
log = logging.getLogger("aave-bot")

TOKEN           = os.environ["TELEGRAM_BOT_TOKEN"]
ADMIN_ID        = int(os.getenv("ADMIN_ID", "231918072"))
CHANNEL         = os.getenv("REQUIRED_CHANNEL", "@qrqlcrypto")
CHECK_INTERVAL  = int(os.getenv("CHECK_INTERVAL", "10"))
DEFAULT_THRESHOLD = Decimal(os.getenv("DEFAULT_MIN_FREE_USD", "1000"))
FAIL_ALERT_AFTER  = int(os.getenv("FAIL_ALERT_AFTER", "10"))
ALERT_COOLDOWN    = int(os.getenv("ALERT_COOLDOWN_SEC", "60"))
ERROR_ALERT_COOLDOWN = 300  # не спамить одной и той же ошибкой чаще раза в 5 мин

_AWAIT_KEY = "await_threshold"

_STATUS_LABELS  = {t("en", "btn_status"),    t("ru", "btn_status")}
_THRESHOLD_LABELS = {t("en", "btn_threshold"), t("ru", "btn_threshold")}
_MONITOR_LABELS   = {t("en", "btn_network"),   t("ru", "btn_network")}
_HELP_LABELS      = {t("en", "btn_help"),      t("ru", "btn_help")}

# ── Helpers ───────────────────────────────────────────────────────────────────


def _reply_keyboard(lang: str) -> ReplyKeyboardMarkup:
    lang_btn = "🇬🇧 EN" if lang == "ru" else "🇷🇺 RU"
    return ReplyKeyboardMarkup(
        [
            [
                KeyboardButton(t(lang, "btn_status")),
                KeyboardButton(t(lang, "btn_network")),
                KeyboardButton(t(lang, "btn_threshold")),
            ],
            [
                KeyboardButton(lang_btn),
                KeyboardButton(t(lang, "btn_help")),
            ],
        ],
        resize_keyboard=True,
        is_persistent=True,
        input_field_placeholder=t(lang, "placeholder"),
    )


def _lang_select_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("🇷🇺 Русский", callback_data="lang_ru"),
        InlineKeyboardButton("🇬🇧 English", callback_data="lang_en"),
    ]])


async def _send_lang_select(chat_id: int, bot) -> None:
    await bot.send_message(
        chat_id,
        "🇷🇺 Выберите язык интерфейса\n🇬🇧 Choose your language",
        reply_markup=_lang_select_keyboard(),
    )


def _gate_keyboard(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(f"📢 {CHANNEL}", url=f"https://t.me/{CHANNEL.lstrip('@')}")],
        [InlineKeyboardButton(t(lang, "btn_check_sub"), callback_data="check_sub")],
    ])


def _monitor_net_keyboard(lang: str, selections: list[str]) -> InlineKeyboardMarkup:
    """Level 1 — network list with selection counts."""
    sel_set = set(selections)
    rows = []
    for net_key, net_cfg in NETWORKS.items():
        count = sum(1 for ak in net_cfg["assets"] if f"{net_key}:{ak}" in sel_set)
        if count > 0:
            label = f"✅ {net_cfg['label']} ({count})"
        else:
            label = net_cfg["label"]
        rows.append([InlineKeyboardButton(label, callback_data=f"mon_net_{net_key}")])
    rows.append([InlineKeyboardButton(t(lang, "mon_done_label"), callback_data="mon_done")])
    return InlineKeyboardMarkup(rows)


def _monitor_asset_keyboard(lang: str, net_key: str, selections: list[str]) -> InlineKeyboardMarkup:
    """Level 2 — asset list for a given network."""
    sel_set  = set(selections)
    net_cfg  = NETWORKS[net_key]
    rows = []
    for asset_key, asset_cfg in net_cfg["assets"].items():
        sel = f"{net_key}:{asset_key}" in sel_set
        label = f"✅ {asset_cfg['label']}" if sel else asset_cfg["label"]
        rows.append([InlineKeyboardButton(
            label,
            callback_data=f"mon_toggle_{net_key}:{asset_key}",
        )])
    rows.append([
        InlineKeyboardButton(t(lang, "mon_back_label"), callback_data="mon_back"),
        InlineKeyboardButton(t(lang, "mon_done_label"), callback_data="mon_done"),
    ])
    return InlineKeyboardMarkup(rows)


def _user_lang(user_id: int) -> str:
    row = db.get(user_id)
    return row["lang"] if row else "ru"


def _user_threshold(user_id: int) -> Decimal:
    row = db.get(user_id)
    if row and row.get("threshold"):
        return Decimal(row["threshold"])
    return DEFAULT_THRESHOLD


async def _is_subscribed(bot, user_id: int) -> bool:
    try:
        member = await bot.get_chat_member(CHANNEL, user_id)
        return member.status in ("member", "administrator", "creator")
    except Exception as exc:
        log.warning("get_chat_member error for %s: %s", user_id, exc)
        return False


async def _send_gate(message, lang: str) -> None:
    await message.reply_text(
        t(lang, "gate_message"),
        reply_markup=_gate_keyboard(lang),
        parse_mode=ParseMode.HTML,
    )


async def _notify_admin(bot, user) -> None:
    mention = f"@{user.username}" if user.username else user.first_name or "—"
    text = (
        f"🔐 <b>[ADMIN]</b>\n"
        f"🆕 <b>Новый пользователь</b>\n\n"
        f"👤 {mention}\n"
        f"🆔 <code>{user.id}</code>"
    )
    try:
        await bot.send_message(ADMIN_ID, text, parse_mode=ParseMode.HTML)
    except Exception as exc:
        log.error("admin notify failed: %s", exc)


async def _register_and_gate_check(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    user = update.effective_user
    uid  = user.id

    db.upsert(uid, user.username, user.first_name)

    row = db.get(uid)
    if row and not row["admin_notified"]:
        await _notify_admin(context.bot, user)
        db.mark_notified(uid)

    lang = _user_lang(uid)

    if not await _is_subscribed(context.bot, uid):
        await _send_gate(update.effective_message, lang)
        return False

    db.set_subscribed(uid)
    return True


# ── Handlers ──────────────────────────────────────────────────────────────────


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await _register_and_gate_check(update, context):
        return
    await _send_lang_select(update.effective_user.id, context.bot)


async def on_check_sub(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    uid   = update.effective_user.id
    lang  = _user_lang(uid)

    if await _is_subscribed(context.bot, uid):
        db.set_subscribed(uid)
        await query.answer()
        try:
            await query.message.delete()
        except Exception:
            pass
        await _send_lang_select(uid, context.bot)
    else:
        await query.answer(t(lang, "not_subscribed_yet"), show_alert=True)


async def on_lang_select(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    uid   = update.effective_user.id
    lang  = "ru" if query.data == "lang_ru" else "en"
    db.set_lang(uid, lang)
    await query.answer()
    try:
        await query.message.delete()
    except Exception:
        pass
    await context.bot.send_message(
        uid,
        t(lang, "welcome"),
        reply_markup=_reply_keyboard(lang),
        parse_mode=ParseMode.HTML,
    )


async def on_mon_net(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """User tapped a network — show asset selection (level 2)."""
    query     = update.callback_query
    uid       = update.effective_user.id
    lang      = _user_lang(uid)
    net_key   = query.data.removeprefix("mon_net_")
    net_label = NETWORKS[net_key]["label"]
    selections = db.get_selections(uid)

    await query.answer()
    try:
        await query.edit_message_text(
            t(lang, "mon_asset_title", net_label=net_label),
            reply_markup=_monitor_asset_keyboard(lang, net_key, selections),
            parse_mode=ParseMode.HTML,
        )
    except Exception:
        pass


async def on_mon_toggle(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Toggle an asset and refresh the asset keyboard."""
    query = update.callback_query
    uid   = update.effective_user.id
    lang  = _user_lang(uid)

    # callback_data: "mon_toggle_{net_key}:{asset_key}"
    net_key, asset_key = query.data.removeprefix("mon_toggle_").split(":", 1)

    selections = db.get_selections(uid)
    sel_str    = f"{net_key}:{asset_key}"
    if sel_str in selections:
        selections.remove(sel_str)
    else:
        selections.append(sel_str)
    db.set_selections(uid, selections)

    await query.answer()
    try:
        await query.edit_message_reply_markup(
            reply_markup=_monitor_asset_keyboard(lang, net_key, selections)
        )
    except Exception:
        pass


async def on_mon_back(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Go back from asset level to network list."""
    query      = update.callback_query
    uid        = update.effective_user.id
    lang       = _user_lang(uid)
    selections = db.get_selections(uid)

    await query.answer()
    try:
        await query.edit_message_text(
            t(lang, "mon_net_title"),
            reply_markup=_monitor_net_keyboard(lang, selections),
            parse_mode=ParseMode.HTML,
        )
    except Exception:
        pass


async def on_mon_done(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """User tapped Done — close the keyboard and confirm."""
    query      = update.callback_query
    uid        = update.effective_user.id
    lang       = _user_lang(uid)
    selections = db.get_selections(uid)

    await query.answer()
    try:
        await query.message.delete()
    except Exception:
        pass

    if selections:
        await context.bot.send_message(uid, t(lang, "mon_saved"), parse_mode=ParseMode.HTML)
    else:
        await context.bot.send_message(uid, t(lang, "mon_none_warning"), parse_mode=ParseMode.HTML)


async def on_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await _register_and_gate_check(update, context):
        return

    text = (update.message.text or "").strip()
    uid  = update.effective_user.id
    lang = _user_lang(uid)

    # ── Language toggle ───────────────────────────────────────────────────────
    if text in ("🇬🇧 EN", "🇷🇺 RU"):
        new_lang = "en" if text == "🇬🇧 EN" else "ru"
        if new_lang == lang:
            return
        db.set_lang(uid, new_lang)
        await update.message.reply_text(
            t(new_lang, "lang_changed"),
            reply_markup=_reply_keyboard(new_lang),
            parse_mode=ParseMode.HTML,
        )
        return

    # ── Status ────────────────────────────────────────────────────────────────
    if text in _STATUS_LABELS:
        selections = db.get_selections(uid)
        thr        = _user_threshold(uid)

        if not selections:
            reply = t(lang, "status_no_assets")
        else:
            sel_set = set(selections)
            rows    = [t(lang, "status_header")]
            for net_key, net_cfg in NETWORKS.items():
                net_assets = [
                    ak for ak in net_cfg["assets"]
                    if f"{net_key}:{ak}" in sel_set
                ]
                if not net_assets:
                    continue
                rows.append(t(lang, "status_net_row", net_label=net_cfg["label"]))
                for asset_key in net_assets:
                    try:
                        s = fetch_state(net_key, asset_key)
                        indicator = "🟢" if s["available_usd"] >= thr else "🔴"
                        rows.append(t(lang, "status_asset_row",
                            indicator=indicator,
                            asset_label=s["asset_label"],
                            available=s["available_usd"],
                        ))
                    except Exception as exc:
                        asset_label = net_cfg["assets"][asset_key]["label"]
                        rows.append(f"  ⚠️ {asset_label}: {exc}")
            rows.append(t(lang, "status_footer", threshold=thr))
            reply = "\n".join(rows)

        await update.message.reply_text(
            reply,
            reply_markup=_reply_keyboard(lang),
            parse_mode=ParseMode.HTML,
        )
        return

    # ── Monitor selection (level 1) ───────────────────────────────────────────
    if text in _MONITOR_LABELS:
        selections = db.get_selections(uid)
        await update.message.reply_text(
            t(lang, "mon_net_title"),
            reply_markup=_monitor_net_keyboard(lang, selections),
            parse_mode=ParseMode.HTML,
        )
        return

    # ── Help ──────────────────────────────────────────────────────────────────
    if text in _HELP_LABELS:
        await update.message.reply_text(
            t(lang, "help_text"),
            reply_markup=_reply_keyboard(lang),
            parse_mode=ParseMode.HTML,
        )
        return

    # ── Alert Threshold — step 1 ──────────────────────────────────────────────
    if text in _THRESHOLD_LABELS:
        context.user_data[_AWAIT_KEY] = True
        await update.message.reply_text(
            t(lang, "threshold_prompt", threshold=_user_threshold(uid)),
            reply_markup=_reply_keyboard(lang),
            parse_mode=ParseMode.HTML,
        )
        return

    # ── Alert Threshold — step 2 ──────────────────────────────────────────────
    if context.user_data.get(_AWAIT_KEY):
        context.user_data[_AWAIT_KEY] = False
        try:
            value = Decimal(text.replace(",", "."))
            if value <= 0:
                raise ValueError("non-positive")
            db.set_threshold(uid, str(value))
            await update.message.reply_text(
                t(lang, "threshold_saved", value=value),
                reply_markup=_reply_keyboard(lang),
                parse_mode=ParseMode.HTML,
            )
        except (InvalidOperation, ValueError):
            await update.message.reply_text(
                t(lang, "threshold_invalid"),
                reply_markup=_reply_keyboard(lang),
                parse_mode=ParseMode.HTML,
            )


# ── Background monitor ────────────────────────────────────────────────────────


async def _send_to_user(
    bot,
    uid: int,
    text: str,
    last_alert: dict,
    *,
    cooldown_key: object = None,
    bypass_cooldown: bool = False,
) -> None:
    key = cooldown_key if cooldown_key is not None else uid
    now = time.monotonic()
    if not bypass_cooldown and now - last_alert.get(key, 0) < ALERT_COOLDOWN:
        log.info("cooldown active for %s — message suppressed", key)
        return
    await bot.send_message(uid, text, parse_mode=ParseMode.HTML)
    last_alert[key] = now


async def _admin_error(bot, text: str, last_err: dict, key: str) -> None:
    """Send error notification to admin with per-key cooldown."""
    now = time.monotonic()
    if now - last_err.get(key, 0) < ERROR_ALERT_COOLDOWN:
        return
    last_err[key] = now
    try:
        await bot.send_message(
            ADMIN_ID,
            f"🔐 <b>[ADMIN]</b>\n⚠️ {text}",
            parse_mode=ParseMode.HTML,
        )
    except Exception as exc:
        log.error("admin error notify failed: %s", exc)


async def _monitor(app: Application) -> None:
    # was_open[(uid, net_key, asset_key)] = bool
    was_open:     dict[tuple, bool]  = {}
    last_alert:   dict[object, float] = {}
    last_err:     dict[str, float]   = {}
    fail_streak:  dict[tuple, int]   = {}
    fail_alerted: dict[tuple, bool]  = {}

    while True:
        await asyncio.sleep(CHECK_INTERVAL)
        try:
            users = db.active_users()
            if not users:
                continue

            # Collect all (net, asset) pairs any user monitors
            needed_pairs: set[tuple[str, str]] = set()
            for u in users:
                for sel in _parse_selections(u):
                    nk, ak = sel
                    if nk in NETWORKS and ak in NETWORKS[nk]["assets"]:
                        needed_pairs.add((nk, ak))

            # Fetch each pair once
            results: dict[tuple, dict | Exception] = {}
            for pair in needed_pairs:
                net_key, asset_key = pair
                net_label   = NETWORKS[net_key]["label"]
                asset_label = NETWORKS[net_key]["assets"][asset_key]["label"]
                try:
                    results[pair] = fetch_state(net_key, asset_key)
                    log.info("%s:%s | available=%.2f",
                             net_key, asset_key, results[pair]["available_usd"])

                    if fail_alerted.get(pair):
                        await _send_to_user(
                            app.bot, ADMIN_ID,
                            t("ru", "alert_recovered",
                              net_label=net_label, asset_label=asset_label),
                            last_alert, bypass_cooldown=True,
                        )
                        fail_alerted[pair] = False
                    fail_streak[pair] = 0

                except Exception as exc:
                    log.error("fetch error [%s:%s]: %s", net_key, asset_key, exc)
                    results[pair] = exc
                    fail_streak[pair] = fail_streak.get(pair, 0) + 1
                    if fail_streak[pair] >= FAIL_ALERT_AFTER and not fail_alerted.get(pair):
                        try:
                            await _send_to_user(
                                app.bot, ADMIN_ID,
                                t("ru", "alert_error",
                                  net_label=net_label, asset_label=asset_label),
                                last_alert, bypass_cooldown=True,
                            )
                        except Exception as send_err:
                            log.error("admin error alert failed: %s", send_err)
                        fail_alerted[pair] = True

            # Notify users
            for u in users:
                uid  = u["user_id"]
                lang = u["lang"]
                thr  = Decimal(u["threshold"] or str(DEFAULT_THRESHOLD))

                for pair in _parse_selections(u):
                    net_key, asset_key = pair
                    if net_key not in NETWORKS or asset_key not in NETWORKS[net_key]["assets"]:
                        continue
                    state = results.get(pair)
                    if isinstance(state, Exception) or state is None:
                        continue

                    free      = state["available_usd"]
                    net_label   = state["net_label"]
                    asset_label = state["asset_label"]
                    is_open   = free >= thr
                    uid_pair  = (uid, net_key, asset_key)
                    prev_open = was_open.get(uid_pair, False)

                    try:
                        if is_open and not prev_open:
                            await _send_to_user(
                                app.bot, uid,
                                t(lang, "alert_open",
                                  net_label=net_label, asset_label=asset_label,
                                  threshold=thr, free=free),
                                last_alert,
                                cooldown_key=uid_pair,
                            )
                        elif prev_open and not is_open:
                            await _send_to_user(
                                app.bot, uid,
                                t(lang, "alert_closed",
                                  net_label=net_label, asset_label=asset_label,
                                  threshold=thr, free=free),
                                last_alert,
                                cooldown_key=uid_pair,
                            )
                    except Exception as send_exc:
                        log.warning("alert send failed uid=%s: %s", uid, send_exc)
                        from telegram.error import Forbidden
                        if not isinstance(send_exc, Forbidden):
                            await _admin_error(
                                app.bot,
                                f"Сбой отправки алерта uid=<code>{uid}</code>: {send_exc}",
                                last_err, f"send_{uid}",
                            )

                    was_open[uid_pair] = is_open

        except Exception as loop_exc:
            log.error("monitor loop error: %s", loop_exc)
            await _admin_error(
                app.bot,
                f"Ошибка цикла монитора: <code>{loop_exc}</code>",
                last_err, "loop",
            )


def _parse_selections(u: dict) -> list[tuple[str, str]]:
    """Parse a user row's networks field into a deduplicated list of (net, asset) pairs."""
    try:
        raw = json.loads(u.get("networks") or '["mantle:eth"]')
    except (json.JSONDecodeError, TypeError):
        raw = ["mantle:eth"]
    seen   = set()
    result = []
    for item in raw:
        sel = item if ":" in item else f"{item}:eth"
        if sel not in seen:
            seen.add(sel)
            nk, ak = sel.split(":", 1)
            result.append((nk, ak))
    return result


async def _monitor_watchdog(app: Application) -> None:
    """Restart _monitor if it ever exits unexpectedly."""
    while True:
        try:
            await _monitor(app)
        except Exception as exc:
            log.error("_monitor exited unexpectedly: %s", exc)
            try:
                await app.bot.send_message(
                    ADMIN_ID,
                    f"🔐 <b>[ADMIN]</b>\n💀 Монитор неожиданно остановился: <code>{exc}</code>\n"
                    f"Перезапускаю через 10 сек...",
                    parse_mode=ParseMode.HTML,
                )
            except Exception:
                pass
            await asyncio.sleep(10)


async def _post_init(app: Application) -> None:
    db.init()
    try:
        await app.bot.set_my_description(
            "Мониторю доступную ликвидность для займа ETH и стейблкоинов на Aave "
            "в 8 сетях: Ethereum, Arbitrum, Plasma, Ink, Mantle, Linea, Avalanche, Base.\n\n"
            "I monitor available borrow liquidity for ETH and stablecoins on Aave "
            "across 8 networks: Ethereum, Arbitrum, Plasma, Ink, Mantle, Linea, Avalanche, Base.\n\n"
            "По вопросам / Support: @qrqlcrypto"
        )
        await app.bot.set_my_short_description(
            "Aave Liquidity Monitor — Ethereum, Arbitrum, Plasma, Ink, Mantle, Linea, Avalanche, Base"
        )
    except Exception as exc:
        log.warning("set description failed: %s", exc)
    try:
        await app.bot.send_message(
            ADMIN_ID,
            "🔐 <b>[ADMIN]</b>\n🤖 Aave Liquidity Monitor запущен (Ethereum, Arbitrum, Plasma, Ink, Mantle, Linea, Avalanche, Base)",
            parse_mode=ParseMode.HTML,
        )
    except Exception as exc:
        log.error("startup notify failed: %s", exc)
    asyncio.create_task(_monitor_watchdog(app))


# ── Entry point ───────────────────────────────────────────────────────────────


def main() -> None:
    app = (
        Application.builder()
        .token(TOKEN)
        .post_init(_post_init)
        .build()
    )
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CallbackQueryHandler(on_check_sub,   pattern="^check_sub$"))
    app.add_handler(CallbackQueryHandler(on_lang_select, pattern="^lang_(ru|en)$"))
    app.add_handler(CallbackQueryHandler(on_mon_net,     pattern="^mon_net_"))
    app.add_handler(CallbackQueryHandler(on_mon_toggle,  pattern="^mon_toggle_"))
    app.add_handler(CallbackQueryHandler(on_mon_back,    pattern="^mon_back$"))
    app.add_handler(CallbackQueryHandler(on_mon_done,    pattern="^mon_done$"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_text))
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
