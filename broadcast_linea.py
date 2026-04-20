#!/usr/bin/env python3
"""
One-shot broadcast: notify all subscribed users that Linea network was added.
Run manually: python3 broadcast_linea.py
"""
import asyncio
import os
import sqlite3
from pathlib import Path

from dotenv import load_dotenv
from telegram import Bot
from telegram.constants import ParseMode

load_dotenv("settings.env")

TOKEN   = os.environ["TELEGRAM_BOT_TOKEN"]
DB_FILE = Path("users.db")

MSG = {
    "ru": (
        "🆕 <b>Бот обновлен!</b>\n\n"
        "Добавлена возможность мониторинга стейблов во всех сетях, где возникли проблемы с ликвидностью.\n"
        "Чтобы добавить стейблы — нажми <b>🔍 Мониторинг</b>, выбери блокчейн и отметь нужные активы.\n\n"
        "Если кнопки не обновились — напиши /start"
    ),
    "en": (
        "🆕 <b>Bot updated!</b>\n\n"
        "You can now monitor stablecoins across all networks where liquidity issues have occurred.\n"
        "To add stablecoins — tap <b>🔍 Monitor</b>, select a blockchain and toggle the assets you need.\n\n"
        "If the buttons didn't update — send /start"
    ),
}


def get_subscribed_users() -> list[dict]:
    con = sqlite3.connect(DB_FILE)
    con.row_factory = sqlite3.Row
    rows = con.execute(
        "SELECT user_id, lang FROM users WHERE subscribed_at IS NOT NULL"
    ).fetchall()
    con.close()
    return [dict(r) for r in rows]


async def broadcast() -> None:
    users = get_subscribed_users()
    print(f"Subscribed users: {len(users)}")

    bot = Bot(token=TOKEN)
    ok = 0
    fail = 0

    for u in users:
        uid  = u["user_id"]
        lang = u["lang"] or "ru"
        text = MSG.get(lang, MSG["ru"])
        try:
            await bot.send_message(uid, text, parse_mode=ParseMode.HTML)
            print(f"  ✅ {uid}")
            ok += 1
        except Exception as exc:
            print(f"  ❌ {uid}: {exc}")
            fail += 1
        await asyncio.sleep(0.05)  # ~20 msg/s, well within Telegram limits

    print(f"\nDone: {ok} sent, {fail} failed")


if __name__ == "__main__":
    asyncio.run(broadcast())
