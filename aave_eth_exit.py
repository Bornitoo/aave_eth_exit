#!/usr/bin/env python3
import argparse
import subprocess
import sys
import time
from decimal import Decimal

import requests

AAVE_GQL = "https://api.v3.aave.com/graphql"
MANTLE_CHAIN_ID = 5000
MANTLE_MARKET = "0x458F293454fE0d67EC0655f3672301301DD51422"
WETH_MANTLE = "0xdeaddeaddeaddeaddeaddeaddeaddeaddead1111"

QUERY = """
query($req: ReserveRequest!) {
  reserve(request: $req) {
    underlyingToken { symbol address }
    isolationModeConfig {
      debtCeiling { usd amount { value } }
      totalBorrows { usd amount { value } }
      debtCeilingDecimals
    }
  }
}
"""


def fetch_state(timeout: int = 15):
    payload = {
        "query": QUERY,
        "variables": {
            "req": {
                "market": MANTLE_MARKET,
                "underlyingToken": WETH_MANTLE,
                "chainId": MANTLE_CHAIN_ID,
            }
        },
    }
    r = requests.post(AAVE_GQL, json=payload, timeout=timeout)
    r.raise_for_status()
    data = r.json()
    if data.get("errors"):
        raise RuntimeError(f"GraphQL errors: {data['errors']}")

    reserve = data["data"]["reserve"]
    cfg = reserve["isolationModeConfig"]
    debt_usd = Decimal(str(cfg["debtCeiling"]["usd"]))
    borrowed_usd = Decimal(str(cfg["totalBorrows"]["usd"]))
    free_usd = debt_usd - borrowed_usd
    return {
        "token": reserve["underlyingToken"]["symbol"],
        "debt_usd": debt_usd,
        "borrowed_usd": borrowed_usd,
        "free_usd": free_usd,
    }


def send_telegram_via_openclaw(chat_id: str, text: str):
    cmd = [
        "/home/tester01/.local/bin/openclaw",
        "message",
        "send",
        "--channel",
        "telegram",
        "--target",
        str(chat_id),
        "--message",
        text,
    ]
    subprocess.run(cmd, check=True)


def main():
    p = argparse.ArgumentParser(description="Monitor Aave Mantle WETH Isolated Debt Ceiling free space")
    p.add_argument("--interval", type=int, default=10, help="Polling interval seconds (default: 10)")
    p.add_argument("--chat-id", default="231918072", help="Telegram chat id")
    p.add_argument("--min-free-usd", type=Decimal, default=Decimal("1"), help="Alert threshold: free USD must be >= this (default: 1)")
    p.add_argument("--close-threshold-usd", type=Decimal, default=Decimal("100"), help="Send 'space ended' alert when free USD drops below this (default: 100)")
    p.add_argument("--cooldown", type=int, default=300, help="Seconds between repeated alerts while open (default: 300)")
    p.add_argument("--once", action="store_true", help="Check once and print state")
    args = p.parse_args()

    was_open = False
    fail_streak = 0
    fail_alert_sent = False

    while True:
        try:
            s = fetch_state()
            if fail_streak > 0 and fail_alert_sent:
                try:
                    send_telegram_via_openclaw(
                        args.chat_id,
                        "✅ Aave monitor: снова удалось получать данные по WETH Isolated Debt Ceiling.",
                    )
                except Exception as send_err:
                    print(f"[monitor-recovery-alert-error] {send_err}", file=sys.stderr, flush=True)
            fail_streak = 0
            fail_alert_sent = False
            free = s["free_usd"]
            debt = s["debt_usd"]
            borrowed = s["borrowed_usd"]

            is_open = free >= args.min_free_usd
            is_closed = free < args.close_threshold_usd

            line = (
                f"WETH Isolated Debt Ceiling | used ${borrowed:.2f} / ${debt:.2f} | free ${free:.2f}"
            )
            print(line, flush=True)

            if args.once:
                return

            if is_open and not was_open:
                msg = (
                    "⚠️ Aave Mantle WETH Isolated: свободное место появилось\n"
                    f"Порог открытия: ${args.min_free_usd:.2f}\n"
                    f"Занято: ${borrowed:.2f} / ${debt:.2f}\n"
                    f"Свободно: ${free:.2f}"
                )
                send_telegram_via_openclaw(args.chat_id, msg)
            elif was_open and is_closed:
                msg = (
                    "ℹ️ Aave Mantle WETH Isolated: свободное место снова закончилось\n"
                    f"Порог закрытия: < ${args.close_threshold_usd:.2f}\n"
                    f"Занято: ${borrowed:.2f} / ${debt:.2f}\n"
                    f"Свободно: ${free:.2f}"
                )
                send_telegram_via_openclaw(args.chat_id, msg)

            was_open = is_open

        except Exception as e:
            fail_streak += 1
            print(f"[monitor-error] {e}", file=sys.stderr, flush=True)
            if fail_streak >= 10 and not fail_alert_sent:
                try:
                    send_telegram_via_openclaw(
                        args.chat_id,
                        "⚠️ Aave monitor: 10 проверок подряд не удалось получить данные по WETH Isolated Debt Ceiling.",
                    )
                    fail_alert_sent = True
                except Exception as send_err:
                    print(f"[monitor-alert-error] {send_err}", file=sys.stderr, flush=True)

        time.sleep(args.interval)


if __name__ == "__main__":
    main()
