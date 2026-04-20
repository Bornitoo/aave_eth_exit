STRINGS = {
    # ── Buttons ──────────────────────────────────────────────────────────────
    "btn_status":    "📊 Status",
    "btn_threshold": "🎯 Alert Threshold",
    "btn_network":   "🔍 Monitor",
    "btn_help":      "❓ Help",
    "placeholder":   "Choose an action…",

    # ── Help ─────────────────────────────────────────────────────────────────
    "help_text": (
        "📖 <b>Help — Aave Liquidity Monitor</b>\n\n"

        "This bot monitors available borrow liquidity for ETH and stablecoins on Aave "
        "across 8 networks: Ethereum, Arbitrum, Plasma, Ink, Mantle, Linea, Avalanche, Base.\n\n"

        "<b>📊 Status</b>\n"
        "Shows available USD liquidity for each selected asset right now. "
        "🟢 — above threshold, 🔴 — below threshold.\n\n"

        "<b>⛓️ Monitor</b>\n"
        "Choose what to monitor. First select a network, then pick assets inside it. "
        "Use the Back button to return and configure other networks.\n\n"
        "Available assets per network:\n"
        "• Ethereum: ETH, USDC, USDT, USDe, GHO, USDG\n"
        "• Arbitrum: ETH, USDC.e, USDC, USD₮0, GHO\n"
        "• Plasma: ETH, USDT0, GHO, USDe\n"
        "• Ink: ETH, USDC, USD₮0, GHO, USDe, USDG\n"
        "• Mantle: ETH, USDC, USDT0, GHO, USDe\n"
        "• Linea: ETH, USDC, USDT\n"
        "• Avalanche: USDC, USDt, GHO, DAI.e\n"
        "• Base: ETH, USDC, EURC, GHO, USDbC\n\n"

        "<b>🎯 Alert Threshold</b>\n"
        "The minimum available USD that triggers an alert. "
        "Default: <b>$1,000</b>. Applies to all selected assets.\n\n"

        "<b>🔔 How alerts work</b>\n"
        "• Available ≥ threshold → 🚨 \"Liquidity Available\" (once per asset)\n"
        "• Available drops below threshold → 🔒 \"Liquidity Filled\" (once per asset)\n"
        "Each alert shows the network and asset name.\n\n"

        "<b>🌍 Language</b>\n"
        "Switch the interface language with the <b>🇬🇧 EN / 🇷🇺 RU</b> button.\n\n"

        "Support: @qrqlcrypto"
    ),

    # ── Subscription gate ─────────────────────────────────────────────────────
    "gate_message": (
        "Чтобы иметь доступ к боту, подпишитесь, пожалуйста, на канал @qrqlcrypto\n"
        "To access the bot, please subscribe to the @qrqlcrypto channel"
    ),
    "btn_check_sub":      "✅ Проверить подписку / Check subscription",
    "not_subscribed_yet": "❌ You're not subscribed yet. Subscribe to the channel and try again.",

    # ── /start ───────────────────────────────────────────────────────────────
    "welcome": (
        "👁 <b>Aave Liquidity Monitor</b>\n\n"
        "I track available borrow liquidity for ETH and stablecoins on Aave "
        "(Ethereum, Arbitrum, Plasma, Ink, Mantle, Linea, Avalanche, Base) "
        "and alert you the moment liquidity opens up.\n\n"
        "Use the buttons below to check the current state or configure your alerts."
    ),

    # ── Language switch ───────────────────────────────────────────────────────
    "lang_changed": "🇬🇧 Switched to English.",

    # ── Status ────────────────────────────────────────────────────────────────
    "status_header":    "📊 <b>Available Liquidity</b>\n",
    "status_net_row":   "\n🔷 <b>{net_label}</b>",
    "status_asset_row": "  {indicator} {asset_label}: ${available:,.2f}",
    "status_no_assets": "⚠️ No assets selected. Tap ⛓️ Monitor to choose.",
    "status_footer":    "\n🎯 Alert threshold: <b>${threshold:,.0f}</b>",
    "status_error":     "❌ Failed to fetch data: <code>{error}</code>",

    # ── Monitor selection ─────────────────────────────────────────────────────
    "mon_net_title":    "⛓️ <b>Select a network:</b>",
    "mon_asset_title":  "🔷 <b>{net_label}</b> — select assets:",
    "mon_back_label":   "← Back",
    "mon_done_label":   "✓ Done",
    "mon_saved":        "✅ Monitoring settings saved.",
    "mon_none_warning": "⚠️ No assets selected — alerts are paused.",

    # ── Alert Threshold ───────────────────────────────────────────────────────
    "threshold_prompt": (
        "<b>🎯 Alert Threshold Setup</b>\n\n"
        "Current threshold: <b>${threshold:,.0f}</b>\n"
        "Enter the minimum USD amount at which you want to receive an alert:"
    ),
    "threshold_saved":   "✅ Alert will fire when available ≥ <b>${value:,.0f}</b>",
    "threshold_invalid": (
        "❌ Invalid value. Please enter a positive number.\n"
        "Example: <code>500</code>"
    ),

    # ── Monitor alerts ────────────────────────────────────────────────────────
    "alert_open": (
        "🚨 <b>{net_label} · {asset_label} — Liquidity Available!</b>\n\n"
        "🟢 Available: <b>${free:,.2f}</b>\n\n"
        "Alert threshold: <b>${threshold:,.0f}</b>"
    ),
    "alert_closed": (
        "🔒 <b>{net_label} · {asset_label} — Liquidity Filled!</b>\n\n"
        "🔴 Available: <b>${free:,.2f}</b>\n\n"
        "Alert threshold: <b>${threshold:,.0f}</b>"
    ),
    "alert_recovered": "✅ <b>{net_label} · {asset_label}</b> — monitor recovered.",
    "alert_error": (
        "⚠️ <b>Monitor error</b>\n\n"
        "10 consecutive failures fetching <b>{net_label} · {asset_label}</b> data."
    ),
}
