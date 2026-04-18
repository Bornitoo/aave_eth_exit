#!/usr/bin/env python3
"""Pure data-fetching layer — no Telegram, no side effects."""
from decimal import Decimal

import requests

AAVE_GQL = "https://api.v3.aave.com/graphql"
MANTLE_CHAIN_ID = 5000
MANTLE_MARKET = "0x458F293454fE0d67EC0655f3672301301DD51422"
WETH_MANTLE = "0xdeaddeaddeaddeaddeaddeaddeaddeaddead1111"

_QUERY = """
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


def fetch_state(timeout: int = 15) -> dict:
    """
    Returns:
        {token, debt_usd, borrowed_usd, free_usd}  — all Decimal
    Raises on any network / GraphQL error.
    """
    payload = {
        "query": _QUERY,
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
    return {
        "token": reserve["underlyingToken"]["symbol"],
        "debt_usd": debt_usd,
        "borrowed_usd": borrowed_usd,
        "free_usd": debt_usd - borrowed_usd,
    }
