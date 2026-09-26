"""
Расширенная конфигурация для Hotel Price Tracker Bot
Используй эти параметры для настройки поведения бота
"""

# ⏰ ИНТЕРВАЛ ПРОВЕРКИ ЦЕН
# В минутах - как часто бот проверяет цены
CHECK_INTERVAL_MINUTES = 60  # По умолчанию каждый час

# 💾 СПОСОБ СОХРАНЕНИЯ ДАННЫХ
# 'json' - сохранение в JSON файл (простое, локальное)
# 'sqlite' - база данных SQLite (более надежно для больших объемов)
STORAGE_TYPE = 'json'

# 🌐 ПОЛЬЗОВАТЕЛЬСКИЕ СЕЛЕКТОРЫ ДЛЯ ПАРСИНГА
# Адаптируй под структуру реального сайта poehalisnami.ua
PRICE_SELECTORS = {
    'class_names': ['price', 'cost', 'hotel-price', 'room-price', 'total-price'],
    'tag_names': ['div', 'span', 'p'],
}

# 📲 НАСТРОЙКИ УВЕДОМЛЕНИЙ
class NotificationSettings:
    # Только сообщать об уменьшении цены
    ONLY_PRICE_DECREASE = False
    
    # Минимальное изменение цены для уведомления (в процентах)
    MIN_PRICE_CHANGE_PERCENT = 0  # 0 = любое изменение
    
    # Отправлять ежедневный отчет
    SEND_DAILY_REPORT = False
    
    # Время отправки ежедневного отчета (часы:минуты)
    DAILY_REPORT_TIME = "09:00"

# 📊 ЛОГИРОВАНИЕ
class LoggingSettings:
    # Уровень логирования: DEBUG, INFO, WARNING, ERROR
    LOG_LEVEL = 'INFO'
    
    # Сохранять логи в файл
    SAVE_LOGS_TO_FILE = False
    
    # Путь к файлу логов
    LOG_FILE = 'bot_logs.log'

# 🔧 ТЕХНИЧЕСКАЯ КОНФИГУРАЦИЯ
class TechnicalSettings:
    # Таймаут для HTTP запросов (в секундах)
    REQUEST_TIMEOUT = 10
    
    # Количество попыток переподключения
    MAX_RETRIES = 3
    
    # Максимальное количество отелей на пользователя
    MAX_HOTELS_PER_USER = 20
    
    # Максимальный размер истории цен (на отель)
    MAX_PRICE_HISTORY = 100

# 🗂️ ПУТИ К ФАЙЛАМ
class Paths:
    DATA_FILE = 'hotel_prices.json'
    DATABASE_FILE = 'hotel_tracker.db'
    LOG_FILE = 'bot_logs.log'
    BACKUP_DIR = 'backups'

# 📈 ТЕКСТОВЫЕ ШАБЛОНЫ
class MessageTemplates:
    PRICE_CHANGED = """
🔔 *Цена изменилась!*

📍 {hotel_name}
❌ Была: {old_price}
✅ Стала: {new_price}
📊 Изменение: {percent}%
🔗 [Смотреть отель]({url})
⏰ {timestamp}
"""
    
    PRICE_DECREASED = """
📉 *Цена упала!*

📍 {hotel_name}
❌ Была: {old_price}
✅ Стала: {new_price}
💰 Экономия: {savings}
📊 Скидка: {percent}%
🔗 [Смотреть отель]({url})
⏰ {timestamp}
"""
    
    DAILY_REPORT = """
📊 *Ежедневный отчет цен*

{hotels_summary}

Всего отелей: {total_hotels}
Изменилось сегодня: {changed_count}
Средняя цена: {avg_price}
"""

# 🎯 ФИЛЬТРЫ ДЛЯ УВЕДОМЛЕНИЙ
class PriceFilters:
    # Не отправлять уведомления если разница меньше этой суммы
    MIN_ABSOLUTE_CHANGE = 0  # в валюте сайта
    
    # Не отправлять уведомления если цена вышла за границы
    MIN_PRICE = 0
    MAX_PRICE = 999999
    
    # Игнорировать символы при парсинге цены
    PRICE_IGNORE_CHARS = ['$', '€', '₽', 'UAH', ' ']

# 🚀 ОПТИМИЗАЦИЯ
class OptimizationSettings:
    # Кэшировать результаты парсинга
    USE_CACHE = True
    
    # Время кэша в секундах
    CACHE_DURATION = 300
    
    # Использовать параллельные запросы
    USE_ASYNC = True
    
    # Максимум одновременных запросов
    MAX_CONCURRENT_REQUESTS = 5

# Функция для получения текущей конфигурации
def get_config():
    """Получить полную конфигурацию в виде словаря"""
    return {
        'check_interval': CHECK_INTERVAL_MINUTES,
        'storage_type': STORAGE_TYPE,
        'notifications': NotificationSettings.__dict__,
        'logging': LoggingSettings.__dict__,
        'technical': TechnicalSettings.__dict__,
        'optimization': OptimizationSettings.__dict__,
    }

# Функция для валидации конфигурации
def validate_config():
    """Проверить корректность конфигурации"""
    errors = []
    
    if CHECK_INTERVAL_MINUTES < 1:
        errors.append("CHECK_INTERVAL_MINUTES должен быть >= 1")
    
    if STORAGE_TYPE not in ['json', 'sqlite']:
        errors.append("STORAGE_TYPE должен быть 'json' или 'sqlite'")
    
    if TechnicalSettings.REQUEST_TIMEOUT < 1:
        errors.append("REQUEST_TIMEOUT должен быть >= 1")
    
    if TechnicalSettings.MAX_HOTELS_PER_USER < 1:
        errors.append("MAX_HOTELS_PER_USER должен быть >= 1")
    
    return errors

# Вывести конфигурацию
if __name__ == '__main__':
    errors = validate_config()
    if errors:
        print("❌ Ошибки в конфигурации:")
        for error in errors:
            print(f"  - {error}")
    else:
        print("✅ Конфигурация корректна!\n")
        print("Текущие параметры:")
        print(f"  ⏰ Интервал проверки: {CHECK_INTERVAL_MINUTES} минут")
        print(f"  💾 Способ хранения: {STORAGE_TYPE}")
        print(f"  📲 Уведомления об уменьшении: {NotificationSettings.ONLY_PRICE_DECREASE}")
        print(f"  🔧 Таймаут: {TechnicalSettings.REQUEST_TIMEOUT} сек")
