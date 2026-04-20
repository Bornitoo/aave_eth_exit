#!/usr/bin/env python3
"""Pure data-fetching layer — no Telegram, no side effects."""
from decimal import Decimal

import requests

AAVE_GQL = "https://api.v3.aave.com/graphql"

NETWORKS: dict[str, dict] = {
    "ethereum": {
        "label":   "Ethereum",
        "chainId": 1,
        "market":  "0x87870Bca3F3fD6335C3F4ce8392D69350B4fA4E2",
        "assets": {
            "eth":  {"label": "ETH",  "underlyingToken": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"},
            "usdc": {"label": "USDC", "underlyingToken": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48"},
            "usdt": {"label": "USDT", "underlyingToken": "0xdAC17F958D2ee523a2206206994597C13D831ec7"},
            "usde": {"label": "USDe", "underlyingToken": "0x4c9EDD5852cd905f086C759E8383e09bff1E68B3"},
            "gho":  {"label": "GHO",  "underlyingToken": "0x40D16FC0246aD3160Ccc09B8D0D3A2cD28aE6C2f"},
            "usdg": {"label": "USDG", "underlyingToken": "0xe343167631d89B6Ffc58B88d6b7fB0228795491D"},
        },
    },
    "arbitrum": {
        "label":   "Arbitrum",
        "chainId": 42161,
        "market":  "0x794a61358D6845594F94dc1DB02A252b5b4814aD",
        "assets": {
            "eth":    {"label": "ETH",    "underlyingToken": "0x82aF49447D8a07e3bd95BD0d56f35241523fBab1"},
            "usdc_e": {"label": "USDC.e", "underlyingToken": "0xFF970A61A04b1cA14834A43f5dE4533eBDDB5CC8"},
            "usdc":   {"label": "USDC",   "underlyingToken": "0xaf88d065e77c8cC2239327C5EDb3A432268e5831"},
            "usdt0":  {"label": "USD₮0",  "underlyingToken": "0xFd086bC7CD5C481DCC9C85ebE478A1C0b69FCbb9"},
            "gho":    {"label": "GHO",    "underlyingToken": "0x7dfF72693f6A4149b17e7C6314655f6A9F7c8B33"},
        },
    },
    "plasma": {
        "label":   "Plasma",
        "chainId": 9745,
        "market":  "0x925a2A7214Ed92428B5b1B090F80b25700095e12",
        "assets": {
            "eth":   {"label": "ETH",   "underlyingToken": "0x9895D81bB462A195b4922ED7De0e3ACD007c32CB"},
            "usdt0": {"label": "USDT0", "underlyingToken": "0xB8CE59FC3717ada4C02eaDF9682A9e934F625ebb"},
            "gho":   {"label": "GHO",   "underlyingToken": "0xb77E872A68C62CfC0dFb02C067Ecc3DA23B4bbf3"},
            "usde":  {"label": "USDe",  "underlyingToken": "0x5d3a1Ff2b6BAb83b63cd9AD0787074081a52ef34"},
        },
    },
    "ink": {
        "label":   "Ink",
        "chainId": 57073,
        "market":  "0x2816cf15F6d2A220E789aA011D5EE4eB6c47FEbA",
        "assets": {
            "eth":   {"label": "ETH",   "underlyingToken": "0x4200000000000000000000000000000000000006"},
            "usdc":  {"label": "USDC",  "underlyingToken": "0x2D270e6886d130D724215A266106e6832161EAEd"},
            "usdt0": {"label": "USD₮0", "underlyingToken": "0x0200C29006150606B650577BBE7B6248F58470c1"},
            "gho":   {"label": "GHO",   "underlyingToken": "0xfc421aD3C883Bf9E7C4f42dE845C4e4405799e73"},
            "usde":  {"label": "USDe",  "underlyingToken": "0x5d3a1Ff2b6BAb83b63cd9AD0787074081a52ef34"},
            "usdg":  {"label": "USDG",  "underlyingToken": "0xe343167631d89B6Ffc58B88d6b7fB0228795491D"},
        },
    },
    "mantle": {
        "label":   "Mantle",
        "chainId": 5000,
        "market":  "0x458F293454fE0d67EC0655f3672301301DD51422",
        "assets": {
            "eth":   {"label": "ETH",   "underlyingToken": "0xdEAddEaDdeadDEadDEADDEAddEADDEAddead1111"},
            "usdc":  {"label": "USDC",  "underlyingToken": "0x09Bc4E0D864854c6aFB6eB9A9cdF58aC190D0dF9"},
            "usdt0": {"label": "USDT0", "underlyingToken": "0x779Ded0c9e1022225f8E0630b35a9b54bE713736"},
            "gho":   {"label": "GHO",   "underlyingToken": "0xfc421aD3C883Bf9E7C4f42dE845C4e4405799e73"},
            "usde":  {"label": "USDe",  "underlyingToken": "0x5d3a1Ff2b6BAb83b63cd9AD0787074081a52ef34"},
        },
    },
    "linea": {
        "label":   "Linea",
        "chainId": 59144,
        "market":  "0xc47b8C00b0f69a36fa203Ffeac0334874574a8Ac",
        "assets": {
            "eth":  {"label": "ETH",  "underlyingToken": "0xe5D7C2a44FfDDf6b295A15c148167daaAf5Cf34f"},
            "usdc": {"label": "USDC", "underlyingToken": "0x176211869cA2b568f2A7D4EE941E073a821EE1ff"},
            "usdt": {"label": "USDT", "underlyingToken": "0xA219439258ca9da29E9Cc4cE5596924745e12B93"},
        },
    },
    "avalanche": {
        "label":   "Avalanche",
        "chainId": 43114,
        "market":  "0x794a61358D6845594F94dc1DB02A252b5b4814aD",
        "assets": {
            "usdc": {"label": "USDC",  "underlyingToken": "0xB97EF9Ef8734C71904D8002F8b6Bc66Dd9c48a6E"},
            "usdt": {"label": "USDt",  "underlyingToken": "0x9702230A8Ea53601f5cD2dc00fDBc13d4dF4A8c7"},
            "gho":  {"label": "GHO",   "underlyingToken": "0xfc421aD3C883Bf9E7C4f42dE845C4e4405799e73"},
            "dai":    {"label": "DAI.e",  "underlyingToken": "0xd586E7F844cEa2F87f50152665BCbc2C279D8d70"},
            "weth_e": {"label": "WETH.e", "underlyingToken": "0x49D5c2BdFfac6CE2BFdB6640F4F80f226bc10bAB"},
        },
    },
    "base": {
        "label":   "Base",
        "chainId": 8453,
        "market":  "0xA238Dd80C259a72e81d7e4664a9801593F98d1c5",
        "assets": {
            "eth":   {"label": "ETH",   "underlyingToken": "0x4200000000000000000000000000000000000006"},
            "usdc":  {"label": "USDC",  "underlyingToken": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"},
            "eurc":  {"label": "EURC",  "underlyingToken": "0x60a3E35Cc302bFA44Cb288Bc5a4F316Fdb1adb42"},
            "gho":   {"label": "GHO",   "underlyingToken": "0x6Bb7a212910682DCFdbd5BCBb3e28FB4E8da10Ee"},
            "usdbc": {"label": "USDbC", "underlyingToken": "0xd9aAEc86B65D86f6A7B5B1b0c42FFA531710b6CA"},
        },
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


def fetch_state(net_key: str, asset_key: str, timeout: int = 15) -> dict:
    """
    Returns:
        {token, available_usd, net_key, asset_key, net_label, asset_label}
    Raises on any network / GraphQL error.
    """
    net_cfg   = NETWORKS[net_key]
    asset_cfg = net_cfg["assets"][asset_key]
    payload = {
        "query": _QUERY,
        "variables": {
            "req": {
                "chainId":         net_cfg["chainId"],
                "market":          net_cfg["market"],
                "underlyingToken": asset_cfg["underlyingToken"],
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
        "token":         reserve["underlyingToken"]["symbol"],
        "available_usd": available_usd,
        "net_key":       net_key,
        "asset_key":     asset_key,
        "net_label":     net_cfg["label"],
        "asset_label":   asset_cfg["label"],
    }
