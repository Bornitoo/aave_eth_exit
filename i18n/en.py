STRINGS = {
    # ── Buttons ──────────────────────────────────────────────────────────────
    "btn_status":    "📊 Status",
    "btn_threshold": "🎯 Alert Threshold",
    "btn_network":   "⛓️ Blockchain",
    "btn_help":      "❓ Help",
    "placeholder":   "Choose an action…",

    # ── Help ─────────────────────────────────────────────────────────────────
    "help_text": (
        "📖 <b>Help — Aave WETH Liquidity Monitor</b>\n\n"

        "This bot monitors available WETH borrow liquidity across selected Aave markets "
        "and alerts you the moment liquidity opens up.\n\n"

        "<b>📊 Status</b>\n"
        "Shows available USD liquidity for each selected network right now. "
        "🟢 — above threshold, 🔴 — below threshold.\n\n"

        "<b>⛓️ Blockchain</b>\n"
        "Choose which blockchains to monitor. You can select one or all five: "
        "Ethereum, Arbitrum, Plasma, Ink, Mantle.\n\n"

        "<b>🎯 Alert Threshold</b>\n"
        "The minimum available USD that triggers an alert. "
        "Default: <b>$1,000</b>. Applies to all selected networks.\n\n"

        "<b>🔔 How alerts work</b>\n"
        "• Available ≥ threshold → 🚨 \"Liquidity Available\" (once per network)\n"
        "• Available drops below threshold → 🔒 \"Liquidity Filled\" (once per network)\n"
        "Each alert always shows the network name first.\n\n"

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
        "👁 <b>Aave WETH Liquidity Monitor</b>\n\n"
        "I track available WETH borrow liquidity on Aave across multiple networks "
        "and alert you the moment liquidity opens up.\n\n"
        "Use the buttons below to check the current state or configure your alert."
    ),

    # ── Language switch ───────────────────────────────────────────────────────
    "lang_changed": "🇬🇧 Switched to English.",

    # ── Status ────────────────────────────────────────────────────────────────
    "status_header":      "📊 <b>WETH Available Liquidity</b>\n",
    "status_network_row": "{indicator} <b>{label}</b>: ${available:,.2f}",
    "status_no_networks": "⚠️ No blockchains selected. Tap ⛓️ Blockchain to choose.",
    "status_footer":      "\n🎯 Alert threshold: <b>${threshold:,.0f}</b>",
    "status_error":       "❌ Failed to fetch data: <code>{error}</code>",

    # ── Network selection ─────────────────────────────────────────────────────
    "net_select_title": "⛓️ <b>Select blockchains to monitor:</b>\n\nTap a blockchain to toggle, then tap Done.",
    "net_done_label":   "✓ Done",
    "net_saved":        "✅ Networks saved.",
    "net_none_warning": "⚠️ No networks selected — alerts are paused.",

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
        "🚨 <b>{label} WETH — Liquidity Available!</b>\n\n"
        "🟢 Available: <b>${free:,.2f}</b>\n\n"
        "Alert threshold: <b>${threshold:,.0f}</b>"
    ),
    "alert_closed": (
        "🔒 <b>{label} WETH — Liquidity Filled!</b>\n\n"
        "🔴 Available: <b>${free:,.2f}</b>\n\n"
        "Alert threshold: <b>${threshold:,.0f}</b>"
    ),
    "alert_recovered": "✅ Monitor recovered — data is fetching normally again.",
    "alert_error": (
        "⚠️ <b>Monitor error</b>\n\n"
        "10 consecutive failures fetching Aave WETH liquidity data."
    ),
}
