#!/usr/bin/env python3
"""Pure data-fetching layer — no Telegram, no side effects."""
from decimal import Decimal

import requests

AAVE_GQL = "https://api.v3.aave.com/graphql"

NETWORKS: dict[str, dict] = {
    "ethereum": {
        "label":           "Ethereum",
        "chainId":         1,
        "market":          "0x87870Bca3F3fD6335C3F4ce8392D69350B4fA4E2",
        "underlyingToken": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
    },
    "arbitrum": {
        "label":           "Arbitrum",
        "chainId":         42161,
        "market":          "0x794a61358D6845594F94dc1DB02A252b5b4814aD",
        "underlyingToken": "0x82aF49447D8a07e3bd95BD0d56f35241523fBab1",
    },
    "plasma": {
        "label":           "Plasma",
        "chainId":         9745,
        "market":          "0x925a2A7214Ed92428B5b1B090F80b25700095e12",
        "underlyingToken": "0x9895D81bB462A195b4922ED7De0e3ACD007c32CB",
    },
    "ink": {
        "label":           "Ink",
        "chainId":         57073,
        "market":          "0x2816cf15F6d2A220E789aA011D5EE4eB6c47FEbA",
        "underlyingToken": "0x4200000000000000000000000000000000000006",
    },
    "mantle": {
        "label":           "Mantle",
        "chainId":         5000,
        "market":          "0x458F293454fE0d67EC0655f3672301301DD51422",
        "underlyingToken": "0xdEAddEaDdeadDEadDEADDEAddEADDEAddead1111",
    },
}

_QUERY = """
query($req: ReserveRequest!) {
  reserve(request: $req) {
    underlyingToken { symbol }
    borrowInfo { availableLiquidity { usd } }
  }
}
"""


def fetch_network_state(network_key: str, timeout: int = 15) -> dict:
    """
    Returns:
        {token, available_usd, network_key, label}  — available_usd is Decimal
    Raises on any network / GraphQL error.
    """
    cfg = NETWORKS[network_key]
    payload = {
        "query": _QUERY,
        "variables": {
            "req": {
                "chainId":         cfg["chainId"],
                "market":          cfg["market"],
                "underlyingToken": cfg["underlyingToken"],
            }
        },
    }
    r = requests.post(AAVE_GQL, json=payload, timeout=timeout)
    r.raise_for_status()
    data = r.json()
    if data.get("errors"):
        raise RuntimeError(f"GraphQL errors: {data['errors']}")

    reserve = data["data"]["reserve"]
    available_usd = Decimal(str(reserve["borrowInfo"]["availableLiquidity"]["usd"]))
    return {
        "token":       reserve["underlyingToken"]["symbol"],
        "available_usd": available_usd,
        "network_key": network_key,
        "label":       cfg["label"],
    }
