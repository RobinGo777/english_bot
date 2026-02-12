# 📚 English Learning Telegram Bot

Автоматичний Telegram-канал для вивчення англійської мови.  
**4 пости на день, повністю безкоштовно.**

---

## 🗂 Структура проєкту

```
english_bot/
├── main.py                 ← головний файл (запуск тут)
├── config.py               ← налаштування та системний промпт
├── ai_client.py            ← Gemini + Groq з автоматичним fallback
├── fallback_posts.py       ← резервні пости (якщо AI недоступний)
├── requirements.txt
├── Procfile                ← для Railway
├── railway.toml            ← для Railway
├── content/
│   ├── post1_morning.py    ← 08:00 UTC Morning Boost
│   ├── post2_quiz.py       ← 10:00 UTC Daily Quiz (Quiz Mode)
│   ├── post3_exam.py       ← 12:00 UTC Exam Prep (4-day rotation)
│   └── post4_thematic.py   ← 14:00 UTC Vocab List / Travel English
└── utils/
    ├── redis_client.py     ← Redis (cloud.redis.io) для історії
    ├── telegram_sender.py  ← відправка постів та квізів
    └── transcription.py    ← IPA транскрипція (eng_to_ipa)
```

---

## ⚙️ Покрокове налаштування

### Крок 1 — Telegram Bot

1. Відкрий [@BotFather](https://t.me/BotFather) у Telegram
2. Надішли `/newbot` → вигадай назву та username (наприклад `EnglishDailyBot`)
3. Скопіюй **Bot Token** (виглядає як `1234567890:ABCdef...`)
4. Створи Telegram-канал (публічний або приватний)
5. Додай бота як **адміністратора** каналу з правом публікувати пости
6. Запам'ятай **Channel ID**: для публічного каналу це `@назваканалу`,  
   для приватного — цифровий ID (можна дізнатись через [@getidsbot](https://t.me/getidsbot))

---

### Крок 2 — API ключі

#### Google Gemini (основний, безкоштовно)
1. Перейди на [https://aistudio.google.com/](https://aistudio.google.com/)
2. Натисни **"Get API key"** → Create API key
3. Скопіюй ключ

#### Groq (резервний, безкоштовно)
1. Зареєструйся на [https://console.groq.com/](https://console.groq.com/)
2. Перейди у **API Keys** → Create New Key
3. Скопіюй ключ

---

### Крок 3 — Redis (cloud.redis.io)

1. Зареєструйся на [https://cloud.redis.io/](https://cloud.redis.io/) (безкоштовний план — 30MB, достатньо)
2. Створи нову базу даних
3. Скопіюй **Public endpoint** у форматі:  
   `redis://default:PASSWORD@redis-XXXXX.c1.us-east-1-2.ec2.cloud.redislabs.com:PORT`

---

### Крок 4 — GitHub

1. Створи новий репозиторій на [GitHub](https://github.com)
2. Завантаж всі файли проєкту:
```bash
git init
git add .
git commit -m "Initial bot setup"
git branch -M main
git remote add origin https://github.com/ТВІ_USERNAME/НАЗВА_РЕПО.git
git push -u origin main
```

---

### Крок 5 — Railway (хостинг)

1. Зареєструйся на [https://railway.app/](https://railway.app/) через GitHub
2. Натисни **"New Project"** → **"Deploy from GitHub repo"**
3. Вибери свій репозиторій
4. Перейди у **Variables** (змінні середовища) та додай:

| Variable | Value |
|----------|-------|
| `TELEGRAM_BOT_TOKEN` | `1234567890:ABCdef...` |
| `TELEGRAM_CHANNEL_ID` | `@назваканалу` або `-100123456789` |
| `GEMINI_API_KEY` | твій Gemini ключ |
| `GROQ_API_KEY` | твій Groq ключ |
| `REDIS_URL` | твій Redis URL |

5. Railway автоматично задеплоїть бота 🚀

---

## 🧪 Тестування локально

```bash
# Встановити залежності
pip install -r requirements.txt

# Встановити змінні середовища (PowerShell)
$env:TELEGRAM_BOT_TOKEN="твій_токен"
$env:TELEGRAM_CHANNEL_ID="@твій_канал"
$env:GEMINI_API_KEY="твій_ключ"
$env:GROQ_API_KEY="твій_ключ"
$env:REDIS_URL="твій_redis_url"

# Протестувати окремий пост
python main.py test morning
python main.py test quiz
python main.py test exam
python main.py test thematic
python main.py test welcome

# Запустити бота (з розкладом)
python main.py
```

---

## ⏰ Розклад публікацій

| UTC | Київ (зима) | Київ (літо) | Тип |
|-----|-------------|-------------|-----|
| 08:00 | 10:00 | 11:00 | 📌 Morning Boost |
| 10:00 | 12:00 | 13:00 | 🎯 Daily Quiz |
| 12:00 | 14:00 | 15:00 | 📚 Exam Prep |
| 14:00 | 16:00 | 17:00 | 🗂 Thematic Content |

---

## 🔄 Логіка ротації

| Пост | Ротація |
|------|---------|
| Morning Boost | Щодня (без ротації) |
| Daily Quiz | Grammar / Vocabulary через день |
| Exam Prep | 4 підтипи по колу (Vocab Upgrade → Tricky Pairs → Grammar Quiz → Speaking) |
| Thematic | Непарні дні → Тематичний список слів, парні → Travel English (8 підтем) |

---

## 📋 Перегляд логів

Логи зберігаються у файлі `bot.log` та виводяться у консоль Railway.  
Формат: `2024-01-15 08:00:01 | INFO     | main | ✅ OK | morning_boost`

---

## ❓ Часті проблеми

**Бот не публікує пости**
- Перевір, що бот є адміністратором каналу
- Перевір `TELEGRAM_CHANNEL_ID` (для приватного каналу потрібен числовий ID)

**Помилка Redis**
- Перевір `REDIS_URL` — має починатись з `redis://`
- Перевір, що free tier не вичерпано (30MB ліміт)

**AI не відповідає**
- Бот автоматично переключиться на Groq, потім на fallback пости
- Перевір API ключі у Railway Variables
