# Aave WETH Liquidity Monitor Bot

Telegram-бот для мониторинга доступной ликвидности **WETH** на [Aave](https://app.aave.com/) в 5 блокчейнах: Ethereum, Arbitrum, Plasma, Ink, Mantle.

A Telegram bot that monitors available **WETH** borrow liquidity on [Aave](https://app.aave.com/) across 5 blockchains: Ethereum, Arbitrum, Plasma, Ink, Mantle.

По вопросам / Support: @qrqlcrypto

---

## Как работает / How it works

Бот каждые 5 секунд запрашивает данные через Aave GraphQL API и сравнивает доступную ликвидность с порогом каждого пользователя по каждому выбранному блокчейну.

The bot polls the Aave GraphQL API every 5 seconds and compares available liquidity against each user's threshold for each selected blockchain.

| Событие / Event | Алерт / Alert |
|---|---|
| `available ≥ threshold` (переход / transition) | 🚨 Ликвидность есть! / Liquidity Available! |
| `available < threshold` (переход / transition) | 🔒 Ликвидность закончилась! / Liquidity Filled! |

Каждый переход срабатывает **ровно один раз** на блокчейн. В каждом алерте первым делом указывается блокчейн.  
Each transition fires **exactly once** per blockchain. Every alert shows the blockchain name first.

---

## Функции / Features

- 🔒 Доступ только для подписчиков канала `@qrqlcrypto`
- 🌍 Два языка: русский и английский
- ⛓️ Выбор блокчейнов для мониторинга (1–5) для каждого пользователя отдельно
- 🎯 Индивидуальный порог уведомлений для каждого пользователя (по умолчанию $1,000)
- 📊 Статус с ликвидностью по всем выбранным блокчейнам в реальном времени
- ❓ Справка на двух языках
- 🗄️ SQLite база данных пользователей
- 🤖 Уведомление админа о каждом новом пользователе и при перезапуске
- ⚡ Systemd-сервис с автозапуском

---

## Поддерживаемые блокчейны / Supported blockchains

| Блокчейн | Chain ID | Токен | Market |
|---|---|---|---|
| Ethereum | 1 | WETH | `0x87870B...` |
| Arbitrum | 42161 | WETH | `0x794a61...` |
| Plasma | 9745 | WETH | `0x925a2A...` |
| Ink | 57073 | WETH | `0x2816cf...` |
| Mantle | 5000 | WETH | `0x458F29...` |

Данные берутся из: `reserve(request: ...) → borrowInfo.availableLiquidity.usd`

---

## Установка / Setup

```bash
git clone https://github.com/Bornitoo/aave_mantle_bot.git
cd aave_mantle_bot
pip install -r requirements.txt
cp settings.env.example settings.env
# заполни settings.env / fill in settings.env
```

### systemd

```bash
cp aave-eth-exit.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable --now aave-eth-exit.service
```

Логи / Logs:
```bash
journalctl -u aave-eth-exit.service -f
```

---

## Конфигурация / Configuration (`settings.env`)

| Переменная | По умолчанию | Описание |
|---|---|---|
| `TELEGRAM_BOT_TOKEN` | — | Токен бота от @BotFather |
| `ADMIN_ID` | `231918072` | Telegram ID администратора |
| `REQUIRED_CHANNEL` | `@qrqlcrypto` | Канал для проверки подписки |
| `CHECK_INTERVAL` | `10` | Интервал опроса Aave (сек) |
| `DEFAULT_MIN_FREE_USD` | `1000` | Порог по умолчанию для новых пользователей |
| `FAIL_ALERT_AFTER` | `10` | Ошибок подряд до алерта об ошибке |
| `ALERT_COOLDOWN_SEC` | `5` | Минимальный интервал между алертами (сек) |

---

## Структура / Structure

```
├── bot.py          # Telegram bot (handlers + monitor loop)
├── monitor.py      # Aave GraphQL fetcher (5 blockchains)
├── db.py           # SQLite user storage (lang, threshold, networks)
├── i18n/
│   ├── __init__.py # t(lang, key) helper
│   ├── ru.py       # Russian strings
│   └── en.py       # English strings
├── settings.env.example
└── aave-eth-exit.service
```

---

## Кнопки бота / Bot buttons

```
[ 📊 Статус ]  [ ⛓️ Блокчейн ]  [ 🎯 Порог уведомлений ]
[ 🇷🇺 RU ]    [ ❓ Помощь ]
```

- **📊 Статус** — доступная ликвидность по всем выбранным блокчейнам прямо сейчас
- **⛓️ Блокчейн** — выбор блокчейнов для мониторинга (чекбоксы, 1–5 сетей)
- **🎯 Порог уведомлений** — настройка суммы USD для алерта
- **🇬🇧 EN / 🇷🇺 RU** — переключение языка
- **❓ Помощь** — подробная справка

---

## Требования / Requirements

- Python 3.11+
- `python-telegram-bot==21.6`
- `requests`
- `python-dotenv`

> Бот должен быть добавлен в канал `@qrqlcrypto` для проверки подписок.  
> The bot must be a member of `@qrqlcrypto` to verify subscriptions.
