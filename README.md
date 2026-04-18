# Aave Mantle WETH Isolation Monitor

Монитор для отслеживания свободного места в **Aave V3 Mantle WETH Isolated Debt Ceiling** с отправкой Telegram-алертов при открытии и закрытии окна свободной ёмкости.

## Что делает бот

Бот в цикле опрашивает Aave GraphQL API, получает текущее состояние `WETH`-резерва в Mantle и считает:

- общий `debt ceiling` в USD,
- текущий объём занятых заимствований в USD,
- остаток свободного места (`free_usd`).

После этого он определяет состояние рынка относительно заданных порогов и отправляет сообщения в Telegram только при **смене состояния**.

Сейчас логика такая:

- если свободное место стало **>= порога открытия**, бот шлёт alert, что окно открылось,
- если после этого свободное место падает **ниже порога закрытия**, бот шлёт alert, что окно снова закрылось,
- если API начинает сбоить, бот считает подряд неудачные попытки,
- после 10 неудачных проверок подряд шлёт alert о проблеме,
- после восстановления доступа к данным шлёт recovery-alert.

Это значит, что бот не спамит на каждом тике, а сообщает именно о значимых переходах.

---

## Что именно мониторится

Источник данных:

- **Aave GraphQL API**: `https://api.v3.aave.com/graphql`

Сеть и рынок:

- **Chain ID:** `5000` (Mantle)
- **Market:** `0x458F293454fE0d67EC0655f3672301301DD51422`
- **Underlying token:** `0xdeaddeaddeaddeaddeaddeaddeaddeaddead1111`
- **Token symbol:** `WETH`

Бот использует GraphQL-запрос к `reserve`, затем читает из `isolationModeConfig`:

- `debtCeiling.usd`
- `totalBorrows.usd`
- `debtCeilingDecimals`

Итоговая свободная ёмкость считается так:

```text
free_usd = debt_usd - borrowed_usd
```

---

## Основные сценарии алертов

### 1. Открытие окна

Если:

```text
free_usd >= min_free_usd
```

и до этого бот считал, что окно закрыто, отправляется сообщение вида:

```text
⚠️ Aave Mantle WETH Isolated: свободное место появилось
Порог открытия: $500.00
Занято: $29998891.17 / $30000000.00
Свободно: $1108.83
```

### 2. Закрытие окна

Если ранее окно было открыто, а потом:

```text
free_usd < close_threshold_usd
```

бот отправляет сообщение вида:

```text
ℹ️ Aave Mantle WETH Isolated: свободное место снова закончилось
Порог закрытия: < $100.00
Занято: $29999988.63 / $30000000.00
Свободно: $11.37
```

### 3. Ошибка API

Если бот 10 раз подряд не смог получить данные:

```text
⚠️ Aave monitor: 10 проверок подряд не удалось получить данные по WETH Isolated Debt Ceiling.
```

### 4. Восстановление после ошибок

Когда после серии ошибок API снова отвечает нормально:

```text
✅ Aave monitor: снова удалось получать данные по WETH Isolated Debt Ceiling.
```

---

## Почему два порога, а не один

Используются два разных порога:

- `min_free_usd` — порог открытия окна,
- `close_threshold_usd` — порог закрытия.

Это сделано для простого гистерезиса, чтобы бот не дёргался около одного и того же значения.

Пример:

- окно открывается при `>= 500 USD`,
- окно считается закрытым только при `< 100 USD`.

Такой подход убирает лишнюю болтанку в районе границы и делает алерты заметно чище.

---

## Текущая боевая конфигурация

Сервис сейчас запускается так:

```ini
ExecStart=/usr/bin/python3 /home/tester01/.openclaw/workspace/aave_weth_isolation_monitor.py --interval 10 --chat-id 231918072 --min-free-usd 500 --cooldown 5
```

Это означает:

- интервал проверки: **10 секунд**,
- Telegram chat id: `231918072`,
- порог открытия: **500 USD**,
- `cooldown`: **5 секунд**.

Важно: в текущей версии параметр `--cooldown` уже пробрасывается, но внутри логики почти не участвует, потому что бот работает в режиме алертов по смене состояния, а не по периодическому повтору сообщений.

---

## Аргументы CLI

Бот поддерживает следующие аргументы:

### `--interval`
Как часто опрашивать Aave API.

Пример:

```bash
--interval 10
```

### `--chat-id`
Куда отправлять Telegram-алерты через OpenClaw.

Пример:

```bash
--chat-id 231918072
```

### `--min-free-usd`
Порог, начиная с которого считается, что свободное окно появилось.

Пример:

```bash
--min-free-usd 500
```

### `--close-threshold-usd`
Порог, ниже которого окно считается снова закрытым.

По умолчанию:

```bash
--close-threshold-usd 100
```

### `--cooldown`
Параметр оставлен в интерфейсе запуска. Исторически использовался для ограничения частоты алертов.

### `--once`
Один раз запросить текущее состояние, вывести строку в stdout и завершиться.

Пример:

```bash
python3 aave_weth_isolation_monitor.py --once
```

---

## Пример ручного запуска

```bash
python3 /home/tester01/.openclaw/workspace/aave_weth_isolation_monitor.py \
  --interval 10 \
  --chat-id 231918072 \
  --min-free-usd 500 \
  --close-threshold-usd 100
```

Одноразовая проверка:

```bash
python3 /home/tester01/.openclaw/workspace/aave_weth_isolation_monitor.py --once
```

---

## Systemd unit

Текущий unit-файл:

```ini
[Unit]
Description=Aave Mantle WETH Isolated Debt Ceiling monitor
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
ExecStart=/usr/bin/python3 /home/tester01/.openclaw/workspace/aave_weth_isolation_monitor.py --interval 10 --chat-id 231918072 --min-free-usd 500 --cooldown 5
Restart=always
RestartSec=5
WorkingDirectory=/home/tester01/.openclaw/workspace

[Install]
WantedBy=default.target
```

Если нужен отдельный проектный репозиторий, обычно достаточно положить рядом:

- `aave_weth_isolation_monitor.py`
- `README.md`
- `aave-weth-isolation-monitor.service`
- при желании `requirements.txt`

---

## Зависимости

Минимально нужны:

- Python 3
- `requests`
- локальный установленный `openclaw`, если алерты шлются через него

Фактически бот импортирует:

- `argparse`
- `json`
- `subprocess`
- `sys`
- `time`
- `decimal.Decimal`
- `requests`

Если выносить проект в отдельный репозиторий, можно использовать такой `requirements.txt`:

```txt
requests>=2.31.0
```

---

## Как бот отправляет алерты

Алерты сейчас идут не напрямую через Telegram Bot API, а через локальный OpenClaw:

```bash
openclaw message send --channel telegram --target <chat_id> --message <text>
```

Это значит, что для работы уведомлений на машине должны быть:

- установлен OpenClaw,
- настроен Telegram-канал/бот,
- доступен `openclaw` по пути:

```text
/home/tester01/.local/bin/openclaw
```

Если хочется сделать бот полностью автономным, этот участок можно заменить на прямую отправку в Telegram Bot API.

---

## Поведение при ошибках

Если API временно отваливается:

- бот не падает сразу,
- пишет ошибку в stderr,
- продолжает опрос,
- после 10 подряд провалов шлёт alert,
- при восстановлении шлёт recovery.

Такой режим удобен для продового процесса под systemd: даже при временных сетевых сбоях сервис не надо поднимать вручную.

---

## Что можно улучшить дальше

Если развивать проект, полезно добавить:

1. **Логи в файл** через systemd `StandardOutput/StandardError`.
2. **SQLite-историю**, если захочется график по свободной ёмкости.
3. **Отдельный стартовый alert**, если нужно подтверждение запуска.
4. **Настоящий cooldown**, если появится режим повторных reminder-алертов.
5. **ENV-конфиг**, чтобы не хардкодить `chat-id` и путь к `openclaw`.
6. **Unit-файл внутри репозитория**, а не только в `~/.config/systemd/user/`.
7. **Прямую интеграцию с Telegram API**, если бот будет разворачиваться без OpenClaw.
8. **Healthcheck endpoint** или heartbeat-файл для внешнего мониторинга.

---

## Структура проекта, которую я бы рекомендовал для отдельного репо

```text
aave-mantle-weth-isolation-monitor/
├── README.md
├── aave_weth_isolation_monitor.py
├── requirements.txt
└── deploy/
    └── aave-weth-isolation-monitor.service
```

---

## Кратко

Это бот, который следит за свободным местом в **Aave Mantle WETH Isolated Debt Ceiling** и шлёт Telegram-алерты, когда:

- окно свободной ёмкости открылось,
- окно снова закрылось,
- Aave API начал сбоить,
- Aave API восстановился.

Текущий рабочий режим:

- проверка каждые **10 секунд**,
- порог открытия **500 USD**,
- порог закрытия **100 USD**,
- доставка алертов через **OpenClaw → Telegram**.
