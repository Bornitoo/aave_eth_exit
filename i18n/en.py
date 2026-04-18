STRINGS = {
    # ── Buttons ──────────────────────────────────────────────────────────────
    "btn_status":    "📊 Status",
    "btn_threshold": "🎯 Alert Threshold",
    "btn_help":      "❓ Help",
    "placeholder":   "Choose an action…",

    # ── Help ─────────────────────────────────────────────────────────────────
    "help_text": (
        "📖 <b>Help — Aave Mantle WETH Monitor</b>\n\n"

        "This bot monitors the free capacity in the <b>WETH Isolated Debt Ceiling</b> "
        "on Aave (Mantle) and alerts you as soon as space becomes available.\n\n"

        "<b>📊 Status</b>\n"
        "Shows how much USD is available right now and your current alert threshold. "
        "🟢 — available exceeds threshold, 🔴 — below threshold.\n\n"

        "<b>🎯 Alert Threshold</b>\n"
        "The minimum available USD that triggers an alert. "
        "Default: <b>$1,000</b>. Can be changed at any time.\n\n"

        "<b>🔔 How alerts work</b>\n"
        "• Available ≥ threshold → 🚨 \"Capacity Available\" (once)\n"
        "• Available drops below threshold → 🔒 \"Capacity Filled\" (once)\n"
        "Each transition fires exactly once — no spam.\n\n"

        "<b>🌍 Language</b>\n"
        "Switch the interface language with the <b>🇬🇧 EN / 🇷🇺 RU</b> button.\n\n"

        "Support: @bornito"
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
        "👁 <b>Aave Mantle · WETH Isolation Monitor</b>\n\n"
        "I track the free space in the WETH Isolated Debt Ceiling on Aave (Mantle) "
        "and alert you the moment capacity opens up.\n\n"
        "Use the buttons below to check the current state or configure your alert."
    ),

    # ── Language switch ───────────────────────────────────────────────────────
    "lang_changed": "🇬🇧 Switched to English.",

    # ── Status ────────────────────────────────────────────────────────────────
    "status_text": (
        "📊 <b>{token} · Isolated Debt Ceiling</b>\n\n"
        "{indicator} Available: <b>${free:,.0f}</b>\n\n"
        "🎯 Alert threshold: <b>${threshold:,.0f}</b>"
    ),
    "status_error": "❌ Failed to fetch data: <code>{error}</code>",

    # ── Alert Threshold setup ────────────────────────────────────────────────────
    "threshold_prompt": (
        "<b>🎯Alert Threshold Setup.</b>\n\n"
        "Current alert threshold: <b>${threshold:,.0f}</b>\n"
        "Enter the minimum USD amount at which you want to receive an alert:"
    ),
    "threshold_saved":  "✅ Alert will fire when available ≥ <b>${value:,.0f}</b>",
    "threshold_invalid": (
        "❌ Invalid value. Please enter a positive number.\n"
        "Example: <code>500</code>"
    ),

    # ── Monitor alerts ────────────────────────────────────────────────────────
    "alert_open": (
        "🚨 <b>Aave Mantle WETH — Capacity Available!</b>\n\n"
        "🟢 Available: <b>${free:,.0f}</b>\n\n"
        "Alert threshold: <b>${threshold:,.0f}</b>"
    ),
    "alert_closed": (
        "🔒 <b>Aave Mantle WETH — Capacity Filled!</b>\n\n"
        "🔴 Available: <b>${free:,.0f}</b>\n\n"
        "Alert threshold: <b>${threshold:,.0f}</b>"
    ),
    "alert_recovered": "✅ Monitor recovered — data is fetching normally again.",
    "alert_error": (
        "⚠️ <b>Monitor error</b>\n\n"
        "10 consecutive failures fetching WETH Isolated Debt Ceiling data."
    ),
}
