#!/usr/bin/env python3
"""
Aave Mantle WETH Isolation Monitor — Telegram bot.

Access control
--------------
Every interaction is gated behind a subscription check to CHANNEL (@qrqlcrypto).
If the user is not subscribed they see a gate message with a link to the channel
and an inline "Check subscription" button.  Only after confirmation does the
persistent reply keyboard appear.

Persistent reply keyboard (pinned to the bottom of the chat):
  [EN|RU]  [📊 Status / Статус]  [🎯 Entry Signal / Сигнал входа]

Monitor alerts are rate-limited to at most one message per ALERT_COOLDOWN seconds
per user.  System messages (recovery, error) bypass the cooldown.

Admin (@bornito, ADMIN_ID) receives a one-time notification when each new user
first interacts with the bot.
"""
import asyncio
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
from monitor import fetch_state
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
DEFAULT_THRESHOLD = Decimal(os.getenv("DEFAULT_MIN_FREE_USD", "1"))
CLOSE_THRESHOLD   = Decimal(os.getenv("CLOSE_THRESHOLD_USD", "100"))
FAIL_ALERT_AFTER  = int(os.getenv("FAIL_ALERT_AFTER", "10"))
ALERT_COOLDOWN    = int(os.getenv("ALERT_COOLDOWN_SEC", "60"))

# context.user_data key — waiting for threshold input
_AWAIT_KEY = "await_threshold"

# All possible reply-button labels for matching (both languages)
_STATUS_LABELS    = {t("en", "btn_status"),    t("ru", "btn_status")}
_THRESHOLD_LABELS = {t("en", "btn_threshold"), t("ru", "btn_threshold")}
_HELP_LABELS      = {t("en", "btn_help"),      t("ru", "btn_help")}

# ── Helpers ───────────────────────────────────────────────────────────────────


def _reply_keyboard(lang: str) -> ReplyKeyboardMarkup:
    """Persistent keyboard pinned to the bottom of the chat."""
    lang_btn = "🇬🇧 EN" if lang == "ru" else "🇷🇺 RU"
    return ReplyKeyboardMarkup(
        [[
            KeyboardButton(t(lang, "btn_status")),
            KeyboardButton(t(lang, "btn_threshold")),
            KeyboardButton(t(lang, "btn_help")),
            KeyboardButton(lang_btn),
        ]],
        resize_keyboard=True,
        is_persistent=True,
        input_field_placeholder=t(lang, "placeholder"),
    )


def _lang_select_keyboard() -> InlineKeyboardMarkup:
    """Inline keyboard for initial language selection."""
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
    """Inline keyboard shown when subscription is required."""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(f"📢 {CHANNEL}", url=f"https://t.me/{CHANNEL.lstrip('@')}")],
        [InlineKeyboardButton(t(lang, "btn_check_sub"), callback_data="check_sub")],
    ])


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
    """
    1. Upsert user to DB.
    2. Notify admin if not yet notified.
    3. Check channel subscription.
       - Not subscribed → send gate, return False.
       - Subscribed     → record, return True.
    """
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
    """Inline button: 'Check subscription'."""
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
    """Inline buttons: 🇷🇺 Русский / 🇬🇧 English — initial language selection."""
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
        try:
            s   = fetch_state()
            thr = _user_threshold(uid)
            reply = t(lang, "status_text",
                token=s["token"],
                debt=s["debt_usd"],
                borrowed=s["borrowed_usd"],
                free=s["free_usd"],
                threshold=thr,
                indicator="🟢" if s["free_usd"] >= thr else "🔴",
            )
        except Exception as exc:
            reply = t(lang, "status_error", error=str(exc))
        await update.message.reply_text(
            reply,
            reply_markup=_reply_keyboard(lang),
            parse_mode=ParseMode.HTML,
        )
        return

    # ── Help ─────────────────────────────────────────────────────────────────
    if text in _HELP_LABELS:
        await update.message.reply_text(
            t(lang, "help_text"),
            reply_markup=_reply_keyboard(lang),
            parse_mode=ParseMode.HTML,
        )
        return

    # ── Entry Signal — step 1: ask for value ─────────────────────────────────
    if text in _THRESHOLD_LABELS:
        context.user_data[_AWAIT_KEY] = True
        await update.message.reply_text(
            t(lang, "threshold_prompt", threshold=_user_threshold(uid)),
            reply_markup=_reply_keyboard(lang),
            parse_mode=ParseMode.HTML,
        )
        return

    # ── Entry Signal — step 2: receive value ──────────────────────────────────
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
    bypass_cooldown: bool = False,
) -> None:
    now = time.monotonic()
    if not bypass_cooldown and now - last_alert.get(uid, 0) < ALERT_COOLDOWN:
        log.info("cooldown active for user %s — message suppressed", uid)
        return
    await bot.send_message(uid, text, parse_mode=ParseMode.HTML)
    last_alert[uid] = now


async def _monitor(app: Application) -> None:
    was_open:   dict[int, bool]  = {}
    last_alert: dict[int, float] = {}
    fail_streak  = 0
    fail_alerted = False

    while True:
        await asyncio.sleep(CHECK_INTERVAL)

        try:
            s = fetch_state()
            log.info(
                "%s | debt=%.2f  borrowed=%.2f  free=%.2f",
                s["token"], s["debt_usd"], s["borrowed_usd"], s["free_usd"],
            )

            users = db.active_users()

            if fail_alerted:
                for u in users:
                    await _send_to_user(
                        app.bot, u["user_id"],
                        t(u["lang"], "alert_recovered"),
                        last_alert, bypass_cooldown=True,
                    )
                fail_alerted = False
            fail_streak = 0

            for u in users:
                uid  = u["user_id"]
                lang = u["lang"]
                thr  = Decimal(u["threshold"] or str(DEFAULT_THRESHOLD))
                free = s["free_usd"]

                is_open   = free >= thr
                prev_open = was_open.get(uid, False)

                if is_open and not prev_open:
                    await _send_to_user(
                        app.bot, uid,
                        t(lang, "alert_open",
                          token=s["token"],
                          threshold=thr,
                          free=free),
                        last_alert,
                    )
                elif prev_open and not is_open:
                    await _send_to_user(
                        app.bot, uid,
                        t(lang, "alert_closed",
                          threshold=thr,
                          free=free),
                        last_alert,
                    )

                was_open[uid] = is_open

        except Exception as exc:
            log.error("fetch error: %s", exc)
            fail_streak += 1
            if fail_streak >= FAIL_ALERT_AFTER and not fail_alerted:
                for u in db.active_users():
                    try:
                        await _send_to_user(
                            app.bot, u["user_id"],
                            t(u["lang"], "alert_error"),
                            last_alert, bypass_cooldown=True,
                        )
                    except Exception as send_err:
                        log.error("send error for %s: %s", u["user_id"], send_err)
                fail_alerted = True


async def _post_init(app: Application) -> None:
    db.init()
    try:
        await app.bot.set_my_description(
            "Мониторю свободную ликвидность в WETH Isolated Debt Ceiling на Aave (Mantle) "
            "и уведомляю, как только появляется доступное место.\n\n"
            "I monitor free liquidity in the WETH Isolated Debt Ceiling on Aave (Mantle) "
            "and alert you when capacity becomes available.\n\n"
            "По вопросам / Support: @qrqlcrypto"
        )
        await app.bot.set_my_short_description(
            "Aave Mantle WETH Isolation Monitor — уведомления о свободной ликвидности / liquidity alerts"
        )
    except Exception as exc:
        log.warning("set description failed: %s", exc)
    try:
        await app.bot.send_message(
            ADMIN_ID,
            "🔐 <b>[ADMIN]</b>\n🤖 Aave Mantle Bot запущен",
            parse_mode=ParseMode.HTML,
        )
    except Exception as exc:
        log.error("startup notify failed: %s", exc)
    asyncio.create_task(_monitor(app))


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
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_text))
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
