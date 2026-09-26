# 🤔 Часто Задаваемые Вопросы (FAQ)

## 🚀 Установка и Запуск

### ❓ Как установить бот?

**Шаг 1:** Получить токен
1. Отправь `/newbot` боту [@BotFather](https://t.me/botfather) в Telegram
2. Следуй инструкциям
3. Скопируй токен

**Шаг 2:** Установить Python и зависимости
```bash
# Linux/Mac
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Windows
python -m venv venv
venv\Scripts\activate.bat
pip install -r requirements.txt
```

**Шаг 3:** Запустить бот
```bash
export TELEGRAM_BOT_TOKEN='твой_токен'  # Linux/Mac
set TELEGRAM_BOT_TOKEN=твой_токен       # Windows

python hotel_price_tracker.py
```

### ❓ Нужна ли мне платная база данных?

Нет! Бот использует локальный JSON файл для хранения данных. Это бесплатно и работает на любом компьютере.

### ❓ Могу ли я запустить бот на своем сервере?

Да! Бот хорошо работает на:
- VPS (DigitalOcean, Linode, Hetzner, и т.д.)
- Облачных сервисах (AWS, Google Cloud, Azure)
- Raspberry Pi
- Обычном ноутбуке/ПК

## 🔧 Функциональность

### ❓ Как добавить отель?

1. Откройте сайт [poehalisnami.ua](https://www.poehalisnami.ua/)
2. Найдите нужный отель
3. Скопируйте ссылку из браузера
4. В Telegram боту отправьте:
   ```
   /add_hotel https://www.poehalisnami.ua/hotel/12345 "Мой любимый отель"
   ```

### ❓ Почему бот не может получить цену?

**Возможные причины:**

1. **Неправильный URL** - проверь, что ссылка открывается в браузере
2. **Структура сайта изменилась** - нужно обновить селектор CSS
3. **JavaScript на странице** - нужно использовать Selenium (см. раздел "Расширенное")

**Решение:**
1. Открой сайт отеля в браузере
2. Нажми F12 (Инструменты разработчика)
3. Найди элемент с ценой (правый клик → "Посмотреть код")
4. Обнови селектор в функции `fetch_hotel_price()` в файле `hotel_price_tracker.py`

### ❓ Как часто бот проверяет цены?

По умолчанию каждый час. Чтобы изменить:

```python
# В функции main():
scheduler.add_job(
    check_prices,
    trigger=IntervalTrigger(hours=2),  # Измени 2 на нужное количество часов
    ...
)
```

### ❓ Максимум отелей, которые я могу добавить?

Нет лимита! Бот может отслеживать неограниченное количество отелей.

## 📱 Уведомления

### ❓ Почему я не получаю уведомления?

1. **Проверь, что ты написал боту `/start`** - это необходимо для получения сообщений
2. **Проверь настройки Telegram** - включены ли уведомления?
3. **Посмотри логи бота** - есть ли ошибки?

### ❓ Могу ли я получить уведомления только при снижении цены?

Да! Отредактируй в `advanced_config.py`:

```python
class NotificationSettings:
    ONLY_PRICE_DECREASE = True  # Только при снижении
```

### ❓ Могу ли я установить минимальное изменение цены?

Да! В `advanced_config.py`:

```python
class NotificationSettings:
    MIN_PRICE_CHANGE_PERCENT = 5  # Только если цена изменилась на 5% и более
```

## 💾 Данные

### ❓ Где хранятся мои данные?

В файле `hotel_prices.json` в текущей папке. Это простой текстовый файл.

Структура:
```json
{
  "123456789": {
    "hotels": {
      "0": {
        "url": "https://www.poehalisnami.ua/hotel/123",
        "name": "Отель Море",
        "last_price": "1500",
        "added_date": "2024-01-15T10:30:00",
        "last_check": "2024-01-15T11:30:00"
      }
    }
  }
}
```

### ❓ Могу ли я экспортировать данные?

Да! Используй утилиту `DataExporter`:

```python
from utils import DataExporter
import json

# Загрузить данные
with open('hotel_prices.json', 'r') as f:
    data = json.load(f)

# Экспортировать в CSV
DataExporter.export_to_csv(data, 'export.csv')

# Создать резервную копию
DataExporter.export_to_json(data, 'backup.json')
```

### ❓ Как сделать резервную копию?

Просто скопируй файл `hotel_prices.json` в безопасное место.

Или автоматизируй через крон (Linux):
```bash
# Ежедневная резервная копия в 3:00 ночи
0 3 * * * cp /path/to/hotel_prices.json /path/to/backups/hotel_prices_$(date +\%Y-\%m-\%d).json
```

## 🐛 Решение Проблем

### ❓ Я получаю ошибку "ModuleNotFoundError: No module named 'telegram'"

Установи зависимости:
```bash
pip install -r requirements.txt
```

Если не помогает:
```bash
pip install --upgrade python-telegram-bot aiohttp beautifulsoup4 apscheduler
```

### ❓ Ошибка "telegram.error.Unauthorized"

Проблема с токеном:
1. Проверь, что токен скопирован правильно
2. Убедись, что переменная окружения установлена:
   ```bash
   echo $TELEGRAM_BOT_TOKEN  # Linux/Mac
   echo %TELEGRAM_BOT_TOKEN% # Windows
   ```

### ❓ Бот запускается, но не реагирует на команды

1. Отправь боту `/start`
2. Проверь, что ты написал самому боту (не в группу)
3. Попробуй `/help`

### ❓ Ошибка "aiohttp.ClientError"

Это ошибка сети:
1. Проверь интернет-соединение
2. Проверь, что URL сайта правильный
3. Может быть сайт временно недоступен

### ❓ Бот потребляет много памяти

Это нормально для долгоживущих процессов. Если критично:
1. Уменьши интервал проверки
2. Уменьши количество отелей
3. Перезапусти бот время от времени

## 🔒 Безопасность

### ❓ Мой токен скомпрометирован, что делать?

1. Немедленно останови бот
2. Открой [@BotFather](https://t.me/botfather)
3. Найди своего бота и выбери "Revoke current token"
4. Создай новый токен
5. Обнови переменную окружения

### ❓ Мои данные безопасны?

Да:
- Данные хранятся локально (не на сервере)
- Используется HTTPS для всех запросов к сайту
- Токен находится в переменной окружения (не в коде)

## 🚀 Продвинутые Вопросы

### ❓ Как использовать Selenium для парсинга?

Если сайт использует JavaScript:

```python
from selenium import webdriver
from selenium.webdriver.common.by import By

async def fetch_hotel_price_selenium(url):
    driver = webdriver.Chrome()
    driver.get(url)
    
    # Подожди загрузки
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    
    price_elem = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CLASS_NAME, "price"))
    )
    
    price = price_elem.text
    driver.quit()
    return price
```

### ❓ Как запустить бот в фоне?

**Linux:**
```bash
# Используй screen
screen -S bot
python hotel_price_tracker.py
# Ctrl+A, D для выхода

# Или используй systemd
# Создай файл /etc/systemd/system/hotel-bot.service
```

**Windows:**
```batch
# Создай task в Task Scheduler
# Запусти python hotel_price_tracker.py
```

### ❓ Как добавить функцию X?

Отредактируй `hotel_price_tracker.py`:
1. Добавь функцию
2. Добавь обработчик команды в `main()`
3. Перезапусти бот

Пример (команда `/stats`):
```python
async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_hotels = tracker.get_user_hotels(update.effective_user.id)
    await update.message.reply_text(f"Отелей: {len(user_hotels)}")

# В main():
application.add_handler(CommandHandler("stats", stats))
```

## 📞 Получить Помощь

Если твой вопрос не решен:

1. **Посмотри логи**: запусти бот и посмотри вывод консоли
2. **Проверь код**: комментарии в `hotel_price_tracker.py` объясняют каждый раздел
3. **Попробуй примеры**: в файле `utils.py` есть примеры использования

---

**Приятного использования бота! 🎉**
