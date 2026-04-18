# Aave Mantle WETH Isolation Monitor Bot

Telegram-бот для мониторинга свободной ёмкости **WETH Isolated Debt Ceiling** на [Aave (Mantle)](https://app.aave.com/).

A Telegram bot that monitors free capacity in the **WETH Isolated Debt Ceiling** on [Aave (Mantle)](https://app.aave.com/).

---

## Как работает / How it works

Бот каждые 10 секунд запрашивает данные через Aave GraphQL API и сравнивает свободную ёмкость с порогом каждого пользователя.

The bot polls the Aave GraphQL API every 10 seconds and compares free capacity against each user's threshold.

| Событие / Event | Алерт / Alert |
|---|---|
| `free ≥ threshold` (переход / transition) | 🚨 Место есть / Capacity Available |
| `free < threshold` (переход / transition) | 🔒 Место закончилось / Capacity Filled |

Каждый переход срабатывает **ровно 1 раз** — без спама.
Each transition fires **exactly once** — no spam.

---

## Функции / Features

- 🔒 Доступ только для подписчиков канала `@qrqlcrypto`
- 🌍 Два языка: русский и английский
- 🎯 Индивидуальный порог уведомлений для каждого пользователя (по умолчанию $1,000)
- 📊 Кнопка статуса с индикатором 🟢/🔴
- 🗄️ SQLite база данных пользователей (дата входа, порог, язык)
- 🤖 Уведомление админа о каждом новом пользователе и при перезапуске
- ⚡ Systemd-сервис с автозапуском

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
cp aave-weth-isolation-monitor.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable --now aave-weth-isolation-monitor.service
```

Логи / Logs:
```bash
journalctl -u aave-weth-isolation-monitor.service -f
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
├── monitor.py      # Aave GraphQL fetcher
├── db.py           # SQLite user storage
├── i18n/
│   ├── __init__.py # t(lang, key) helper
│   ├── ru.py       # Russian strings
│   └── en.py       # English strings
├── settings.env.example
└── aave-weth-isolation-monitor.service
```

---

## Кнопки бота / Bot buttons

```
[ 📊 Статус ]  [ 🎯 Порог уведомлений ]  [ ❓ Помощь ]  [ 🇬🇧 EN ]
```

- **📊 Статус** — текущее состояние пула в реальном времени
- **🎯 Порог уведомлений** — настройка суммы для алерта
- **❓ Помощь** — подробная справка
- **🇬🇧 EN / 🇷🇺 RU** — переключение языка

---

## Требования / Requirements

- Python 3.11+
- `python-telegram-bot==21.6`
- `requests`
- `python-dotenv`

> Бот должен быть добавлен в канал `@qrqlcrypto` для проверки подписок.
> The bot must be a member of `@qrqlcrypto` to verify subscriptions.
