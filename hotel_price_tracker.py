import os
import json
import asyncio
from datetime import datetime
from bs4 import BeautifulSoup
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackQueryHandler,
    ContextTypes, filters
)
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
import logging
from requests_html import HTMLSession
import time

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Файл для хранения данных
DATA_FILE = 'hotel_prices.json'

class HotelPriceTracker:
    def __init__(self):
        self.data = self.load_data()
    
    def load_data(self):
        """Загрузить данные из файла"""
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    def save_data(self):
        """Сохранить данные в файл"""
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)
    
    def add_hotel(self, user_id, hotel_url, hotel_name):
        """Добавить отель для отслеживания"""
        user_id = str(user_id)
        if user_id not in self.data:
            self.data[user_id] = {'hotels': {}}
        
        hotel_id = len(self.data[user_id]['hotels'])
        self.data[user_id]['hotels'][str(hotel_id)] = {
            'url': hotel_url,
            'name': hotel_name,
            'last_price': None,
            'added_date': datetime.now().isoformat()
        }
        self.save_data()
        return hotel_id
    
    def remove_hotel(self, user_id, hotel_id):
        """Удалить отель из отслеживания"""
        user_id = str(user_id)
        if user_id in self.data and str(hotel_id) in self.data[user_id]['hotels']:
            del self.data[user_id]['hotels'][str(hotel_id)]
            self.save_data()
            return True
        return False
    
    def get_user_hotels(self, user_id):
        """Получить все отели пользователя"""
        user_id = str(user_id)
        if user_id in self.data:
            return self.data[user_id]['hotels']
        return {}
    
    def update_price(self, user_id, hotel_id, price):
        """Обновить цену отеля"""
        user_id = str(user_id)
        hotel_id = str(hotel_id)
        if user_id in self.data and hotel_id in self.data[user_id]['hotels']:
            old_price = self.data[user_id]['hotels'][hotel_id]['last_price']
            self.data[user_id]['hotels'][hotel_id]['last_price'] = price
            self.data[user_id]['hotels'][hotel_id]['last_check'] = datetime.now().isoformat()
            self.save_data()
            return old_price
        return None

tracker = HotelPriceTracker()

async def fetch_hotel_price(url):
    """Получить цену отеля - использует requests-html для загрузки JavaScript"""
    try:
        logger.info(f"📡 Загружаю страницу: {url}")
        
        # Используй requests-html с JavaScript рендерингом
        session = HTMLSession()
        
        try:
            # Загрузи страницу с выполнением JavaScript
            logger.info("⏳ Рендерю JavaScript...")
            response = session.get(url, timeout=60)
            
            # Выполни JavaScript и ждём загрузки
            logger.info("⏳ Жду загрузки контента...")
            response.html.render(sleep=25, timeout=60)  # Подожди 2 секунды на загрузку
            logger.info("✅ Страница загружена и отрендерена")
            
            # Ищем элемент с ценой
            price_elem = response.html.find('.jsTourPrice', first=True)
            
            if price_elem:
                price_text = price_elem.text.strip()
                logger.info(f"Найден элемент .jsTourPrice, текст: '{price_text}'")
                
                if price_text:  # Если не пустой
                    # Извлечь числа
                    price = ''.join(filter(lambda x: x.isdigit() or x in ',.', price_text.replace(' ', '')))
                    
                    if price and price != '0':
                        price = price.replace(',', '.')
                        logger.info(f"✅ Цена найдена: {price}")
                        session.close()
                        return price
            
            # Если первый способ не сработал, ищем число с валютой
            logger.info("Способ 1 не сработал, ищу последним способом...")
            
            html_content = response.html.html
            soup = BeautifulSoup(html_content, 'html.parser')
            
            for elem in soup.find_all(['div', 'span', 'p']):
                text = elem.get_text(strip=True)
                if text and any(curr in text for curr in ['грн', 'UAH', 'uah']):
                    if any(char.isdigit() for char in text):
                        price = ''.join(filter(lambda x: x.isdigit() or x in ',.', text.replace(' ', '')))
                        if price and len(price) > 2 and price != '0':
                            price = price.replace(',', '.')
                            logger.info(f"✅ Цена найдена (способ 2): {price}")
                            session.close()
                            return price
            
            logger.warning("❌ Не удалось найти цену")
            session.close()
            return None
            
        except Exception as e:
            logger.error(f"❌ Ошибка при загрузке/рендеринге: {e}")
            import traceback
            logger.error(traceback.format_exc())
            session.close()
            return None
                
    except Exception as e:
        logger.error(f"❌ Ошибка при получении цены: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /start"""
    user_id = update.effective_user.id
    welcome_text = """
👋 Добро пожаловать в Hotel Price Tracker!

Этот бот отслеживает цены на отели с сайта poehalisnami.ua и уведомляет вас об изменениях.

📍 Команды:
/add_hotel - добавить отель для отслеживания
/list_hotels - показать список отслеживаемых отелей
/remove_hotel - удалить отель из списка
/help - справка

⏰ Бот проверяет цены каждый час!
    """
    await update.message.reply_text(welcome_text)

async def add_hotel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /add_hotel"""
    user_id = update.effective_user.id
    
    if len(context.args) < 2:
        await update.message.reply_text(
            "❌ Использование: /add_hotel <URL> <Название отеля>\n\n"
            "Пример: /add_hotel https://www.poehalisnami.ua/hotel/123 \"Отель Океан\""
        )
        return
    
    url = context.args[0]
    hotel_name = ' '.join(context.args[1:])
    
    # Валидация URL
    if not url.startswith('http'):
        await update.message.reply_text("❌ Неверный URL. Должен начинаться с http или https")
        return
    
    # Проверка, что отель с таким URL еще не добавлен
    user_hotels = tracker.get_user_hotels(user_id)
    for hotel in user_hotels.values():
        if hotel['url'] == url:
            await update.message.reply_text("⚠️ Этот отель уже в списке отслеживания!")
            return
    
    # Попытка получить цену для проверки URL
    price = await fetch_hotel_price(url)
    
    if price is None:
        await update.message.reply_text(
            "⚠️ Не удалось получить цену с этого URL.\n"
            "Пожалуйста, проверь ссылку и попробуй еще раз."
        )
        return
    
    hotel_id = tracker.add_hotel(user_id, url, hotel_name)
    tracker.update_price(user_id, hotel_id, price)
    
    await update.message.reply_text(
        f"✅ Отель добавлен!\n\n"
        f"📍 Название: {hotel_name}\n"
        f"💰 Текущая цена: {price}\n"
        f"⏰ Бот будет проверять цену каждый час"
    )

async def list_hotels(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /list_hotels"""
    user_id = update.effective_user.id
    hotels = tracker.get_user_hotels(user_id)
    
    if not hotels:
        await update.message.reply_text("📭 У тебя еще нет отслеживаемых отелей")
        return
    
    message = "📊 Твои отели:\n\n"
    for hotel_id, hotel_data in hotels.items():
        message += (
            f"🔹 {hotel_data['name']}\n"
            f"   💰 Цена: {hotel_data['last_price'] or 'не определена'}\n"
            f"   🔗 {hotel_data['url']}\n"
            f"   ID: {hotel_id}\n\n"
        )
    
    await update.message.reply_text(message)

async def remove_hotel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /remove_hotel"""
    user_id = update.effective_user.id
    
    if len(context.args) != 1:
        await update.message.reply_text(
            "❌ Использование: /remove_hotel <ID отеля>\n\n"
            "Сначала используй /list_hotels чтобы увидеть ID"
        )
        return
    
    try:
        hotel_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("❌ ID должен быть числом")
        return
    
    if tracker.remove_hotel(user_id, hotel_id):
        await update.message.reply_text("✅ Отель удален из списка отслеживания")
    else:
        await update.message.reply_text("❌ Отель не найден")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /help"""
    help_text = """
📖 Справка:

/start - главное меню
/add_hotel <URL> <Название> - добавить отель
/list_hotels - список отслеживаемых отелей
/remove_hotel <ID> - удалить отель

💡 Пример добавления отеля:
/add_hotel https://www.poehalisnami.ua/hotel/123 Отель Море

🔔 Бот автоматически проверяет цены каждый час!
Если цена изменилась, ты получишь уведомление.

📌 Важно: используй полные ссылки на страницы отелей с сайта poehalisnami.ua
    """
    await update.message.reply_text(help_text)

async def check_prices(context: ContextTypes.DEFAULT_TYPE):
    """Проверить цены на все отели всех пользователей"""
    logger.info("=" * 60)
    logger.info("🔍 НАЧАЛО ПРОВЕРКИ ЦЕН")
    logger.info("=" * 60)
    
    for user_id, user_data in tracker.data.items():
        hotels = user_data.get('hotels', {})
        logger.info(f"\n👤 Пользователь {user_id}: {len(hotels)} отелей")
        
        for hotel_id, hotel_info in hotels.items():
            url = hotel_info['url']
            hotel_name = hotel_info['name']
            
            logger.info(f"\n  🏨 Проверяю: {hotel_name}")
            logger.info(f"     URL: {url}")
            logger.info(f"     Была цена: {hotel_info.get('last_price', 'не определена')}")
            
            try:
                # Используй Playwright напрямую
                new_price = await fetch_hotel_price(url)
                
                if new_price:
                    logger.info(f"     ✅ Новая цена: {new_price}")
                    old_price = tracker.update_price(user_id, hotel_id, new_price)
                    
                    # Если цена изменилась, отправить уведомление
                    if old_price and old_price != new_price:
                        logger.info(f"     📊 ЦЕНА ИЗМЕНИЛАСЬ! {old_price} → {new_price}")
                        
                        try:
                            message = (
                                f"🔔 <b>Цена изменилась!</b>\n\n"
                                f"📍 <b>{hotel_name}</b>\n"
                                f"❌ Была: <b>{old_price}</b>\n"
                                f"✅ Стала: <b>{new_price}</b>\n"
                                f"🔗 <a href='{url}'>Смотреть отель</a>"
                            )
                            
                            await context.bot.send_message(
                                chat_id=int(user_id),
                                text=message,
                                parse_mode='HTML'
                            )
                            logger.info(f"     📨 ✅ Уведомление отправлено пользователю {user_id}")
                        except Exception as e:
                            logger.error(f"     📨 ❌ Ошибка отправки сообщения: {e}")
                    else:
                        if old_price:
                            logger.info(f"     ℹ️ Цена не изменилась ({old_price} == {new_price})")
                        else:
                            logger.info(f"     ℹ️ Первая проверка цены")
                else:
                    logger.warning(f"     ⚠️ Не удалось получить цену!")
                    
            except Exception as e:
                logger.error(f"     ❌ Ошибка при проверке цены: {e}")
                import traceback
                logger.error(traceback.format_exc())
    
    logger.info("\n" + "=" * 60)
    logger.info("✅ ПРОВЕРКА ЦЕН ЗАВЕРШЕНА")
    logger.info("=" * 60)

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик ошибок"""
    logger.error(msg="Exception while handling an update:", exc_info=context.error)

def main():
    """Главная функция"""
    # Получить токен из переменной окружения
    TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
    if not TOKEN:
        print("❌ Ошибка: установи переменную окружения TELEGRAM_BOT_TOKEN")
        print("Используй: export TELEGRAM_BOT_TOKEN='ваш_токен'")
        return
    
    # Создать приложение
    application = Application.builder().token(TOKEN).build()
    
    # Добавить обработчики команд
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("add_hotel", add_hotel))
    application.add_handler(CommandHandler("list_hotels", list_hotels))
    application.add_handler(CommandHandler("remove_hotel", remove_hotel))
    application.add_handler(CommandHandler("help", help_command))
    
    # Обработчик ошибок
    application.add_error_handler(error_handler)
    
    # Планировщик для проверки цен каждый час
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        check_prices,
        trigger=IntervalTrigger(hours=1),
        args=(application.job_queue,),
        id='check_prices_job',
        name='Проверка цен каждый час',
        replace_existing=True
    )
    
    # Добавить scheduler в приложение
    application.job_queue.scheduler = scheduler
    scheduler._application = application
    
    # Запустить бот
    print("✅ Бот запущен! Нажми Ctrl+C для остановки.")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
