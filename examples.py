"""
Примеры расширенного использования Hotel Price Tracker Bot
Копируй нужные части в основной файл или создавай отдельные модули
"""

# ============================================================================
# ПРИМЕР 1: Добавить уведомления только при снижении цены
# ============================================================================

async def check_prices_smart(context):
    """Проверить цены и отправить уведомления только при снижении"""
    
    for user_id, user_data in tracker.data.items():
        for hotel_id, hotel_info in user_data.get('hotels', {}).items():
            url = hotel_info['url']
            
            try:
                async with aiohttp.ClientSession() as session:
                    new_price = await fetch_hotel_price(session, url)
                
                if new_price:
                    old_price = tracker.update_price(user_id, hotel_id, new_price)
                    
                    # Только если цена СНИЗИЛАСЬ
                    if old_price and float(new_price) < float(old_price):
                        await context.bot.send_message(
                            chat_id=int(user_id),
                            text=f"📉 Цена снизилась!\n\n{hotel_info['name']}\n"
                                 f"Было: {old_price} → Стало: {new_price}"
                        )
            except Exception as e:
                logger.error(f"Ошибка: {e}")

# ============================================================================
# ПРИМЕР 2: Добавить команду /stats для статистики
# ============================================================================

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /stats - показать статистику"""
    user_id = str(update.effective_user.id)
    hotels = tracker.get_user_hotels(user_id)
    
    if not hotels:
        await update.message.reply_text("📭 У тебя нет отелей")
        return
    
    prices = []
    for hotel in hotels.values():
        if hotel['last_price']:
            try:
                prices.append(float(hotel['last_price']))
            except ValueError:
                pass
    
    if not prices:
        await update.message.reply_text("⚠️ Нет данных о ценах")
        return
    
    avg_price = sum(prices) / len(prices)
    min_price = min(prices)
    max_price = max(prices)
    
    stats_text = f"""📊 Твоя статистика:

🏨 Отелей отслеживается: {len(hotels)}
💰 Средняя цена: {avg_price:.2f}
📈 Максимум: {max_price:.2f}
📉 Минимум: {min_price:.2f}
💵 Сумма всех цен: {sum(prices):.2f}
"""
    
    await update.message.reply_text(stats_text)

# ============================================================================
# ПРИМЕР 3: Добавить команду /export для скачивания данных
# ============================================================================

from utils import DataExporter

async def export_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /export - экспортировать данные"""
    user_id = update.effective_user.id
    hotels = tracker.get_user_hotels(user_id)
    
    if not hotels:
        await update.message.reply_text("📭 Нет отелей для экспорта")
        return
    
    # Создать данные для экспорта только этого пользователя
    export_data = {str(user_id): {'hotels': hotels}}
    
    # Экспортировать в CSV
    filename = f"hotels_{user_id}.csv"
    if DataExporter.export_to_csv(export_data, filename):
        with open(filename, 'rb') as f:
            await update.message.reply_document(document=f)
        await update.message.reply_text("✅ Данные экспортированы в CSV")
    else:
        await update.message.reply_text("❌ Ошибка при экспорте")

# ============================================================================
# ПРИМЕР 4: Добавить команду /alarm для целевой цены
# ============================================================================

# Добавить в начало файла:
PRICE_ALARMS = {}  # {user_id: {hotel_id: target_price}}

async def alarm_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /alarm <hotel_id> <price> - установить целевую цену"""
    
    if len(context.args) != 2:
        await update.message.reply_text(
            "❌ Использование: /alarm <ID отеля> <целевая цена>\n"
            "Пример: /alarm 0 1200"
        )
        return
    
    try:
        hotel_id = int(context.args[0])
        target_price = float(context.args[1])
    except ValueError:
        await update.message.reply_text("❌ Неверные параметры")
        return
    
    user_id = update.effective_user.id
    if user_id not in PRICE_ALARMS:
        PRICE_ALARMS[user_id] = {}
    
    PRICE_ALARMS[user_id][hotel_id] = target_price
    await update.message.reply_text(
        f"✅ Установлена целевая цена {target_price} для отеля {hotel_id}\n"
        "Ты получишь уведомление, когда цена упадет ниже"
    )

async def check_alarms(context):
    """Проверить целевые цены"""
    
    for user_id, alarms in PRICE_ALARMS.items():
        user_hotels = tracker.get_user_hotels(user_id)
        
        for hotel_id, target_price in alarms.items():
            hotel_id_str = str(hotel_id)
            if hotel_id_str in user_hotels:
                current_price = user_hotels[hotel_id_str]['last_price']
                
                try:
                    if float(current_price) <= target_price:
                        await context.bot.send_message(
                            chat_id=user_id,
                            text=f"🎯 Цель достигнута!\n\n"
                                 f"{user_hotels[hotel_id_str]['name']}\n"
                                 f"Целевая цена: {target_price}\n"
                                 f"Текущая цена: {current_price}\n\n"
                                 f"Спешите бронировать! 🏃"
                        )
                        # Удалить уведомление после срабатывания
                        del alarms[hotel_id]
                except ValueError:
                    pass

# ============================================================================
# ПРИМЕР 5: Уведомления в определенное время
# ============================================================================

from apscheduler.triggers.cron import CronTrigger

async def morning_report(context: ContextTypes.DEFAULT_TYPE):
    """Отправить утренний отчет в 9:00"""
    
    for user_id, user_data in tracker.data.items():
        hotels = user_data.get('hotels', {})
        
        if not hotels:
            continue
        
        report = "📊 Утренний отчет\n\n"
        for hotel_id, hotel_info in hotels.items():
            report += f"🏨 {hotel_info['name']}: {hotel_info.get('last_price', 'N/A')}\n"
        
        try:
            await context.bot.send_message(chat_id=int(user_id), text=report)
        except Exception as e:
            logger.error(f"Ошибка при отправке отчета: {e}")

# В функции main(), добавить:
# scheduler.add_job(
#     morning_report,
#     trigger=CronTrigger(hour=9, minute=0),
#     args=(application.job_queue,),
#     id='morning_report',
#     replace_existing=True
# )

# ============================================================================
# ПРИМЕР 6: Интеграция с Google Sheets
# ============================================================================

"""
Для сохранения данных в Google Sheets нужна библиотека gspread:
pip install gspread google-auth-oauthlib

Пример кода:
"""

async def sync_to_google_sheets(context):
    """Синхронизировать данные с Google Sheets"""
    
    try:
        import gspread
        from google.auth.transport.requests import Request
        from google.oauth2.service_account import Credentials
        
        # Подключиться к Google Sheets (нужен файл credentials.json)
        creds = Credentials.from_service_account_file(
            'credentials.json',
            scopes=['https://www.googleapis.com/auth/spreadsheets']
        )
        
        gc = gspread.authorize(creds)
        sheet = gc.open("Hotel Prices").sheet1
        
        # Очистить лист
        sheet.clear()
        
        # Добавить заголовки
        sheet.append_row(['User ID', 'Hotel', 'Price', 'Date'])
        
        # Добавить данные
        for user_id, user_data in tracker.data.items():
            for hotel_id, hotel_info in user_data.get('hotels', {}).items():
                sheet.append_row([
                    user_id,
                    hotel_info['name'],
                    hotel_info.get('last_price', 'N/A'),
                    hotel_info.get('last_check', 'N/A')
                ])
        
        logger.info("✅ Данные синхронизированы с Google Sheets")
    
    except Exception as e:
        logger.error(f"Ошибка при синхронизации: {e}")

# ============================================================================
# ПРИМЕР 7: Фильтр по диапазону цен
# ============================================================================

async def filter_by_price_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /filter_price <min> <max> - фильтровать отели по цене"""
    
    if len(context.args) != 2:
        await update.message.reply_text(
            "❌ Использование: /filter_price <минимум> <максимум>\n"
            "Пример: /filter_price 500 2000"
        )
        return
    
    try:
        min_price = float(context.args[0])
        max_price = float(context.args[1])
    except ValueError:
        await update.message.reply_text("❌ Неверные параметры")
        return
    
    user_id = str(update.effective_user.id)
    hotels = tracker.get_user_hotels(user_id)
    
    filtered = []
    for hotel_id, hotel_info in hotels.items():
        price = hotel_info.get('last_price')
        if price:
            try:
                if min_price <= float(price) <= max_price:
                    filtered.append((hotel_id, hotel_info))
            except ValueError:
                pass
    
    if not filtered:
        await update.message.reply_text(
            f"🔍 Не найдено отелей в диапазоне {min_price} - {max_price}"
        )
        return
    
    message = f"🔍 Найдено {len(filtered)} отелей:\n\n"
    for hotel_id, hotel_info in filtered:
        message += f"🏨 {hotel_info['name']}: {hotel_info['last_price']}\n"
    
    await update.message.reply_text(message)

# ============================================================================
# ПРИМЕР 8: Поиск отелей по названию
# ============================================================================

async def search_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /search <название> - поиск отеля по названию"""
    
    if not context.args:
        await update.message.reply_text(
            "❌ Использование: /search <название отеля>"
        )
        return
    
    search_term = ' '.join(context.args).lower()
    user_id = str(update.effective_user.id)
    hotels = tracker.get_user_hotels(user_id)
    
    found = []
    for hotel_id, hotel_info in hotels.items():
        if search_term in hotel_info['name'].lower():
            found.append((hotel_id, hotel_info))
    
    if not found:
        await update.message.reply_text(f"🔍 Отелей '{search_term}' не найдено")
        return
    
    message = f"🔍 Найдено {len(found)} отелей:\n\n"
    for hotel_id, hotel_info in found:
        message += f"🏨 {hotel_info['name']}\n   ID: {hotel_id}\n"
    
    await update.message.reply_text(message)

# ============================================================================
# Как добавить эти примеры в основной файл:
# ============================================================================

"""
1. Копируй нужные функции в hotel_price_tracker.py
2. Добавь обработчики в main() функцию:

    application.add_handler(CommandHandler("stats", stats_command))
    application.add_handler(CommandHandler("export", export_command))
    application.add_handler(CommandHandler("alarm", alarm_command))
    application.add_handler(CommandHandler("filter_price", filter_by_price_command))
    application.add_handler(CommandHandler("search", search_command))

3. Добавь джобы в scheduler:

    scheduler.add_job(check_alarms, trigger=IntervalTrigger(minutes=5), ...)
    scheduler.add_job(morning_report, trigger=CronTrigger(hour=9), ...)
    scheduler.add_job(sync_to_google_sheets, trigger=IntervalTrigger(hours=1), ...)

4. Перезапусти бот
"""

if __name__ == '__main__':
    print("📚 Примеры расширенного использования Hotel Price Tracker Bot")
    print("=" * 60)
    print("\nЭтот файл содержит примеры кода для расширения функциональности.")
    print("Копируй нужные части в основной файл bot'а.")
    print("\n✨ Доступные примеры:")
    print("  1. Уведомления только при снижении цены")
    print("  2. Команда /stats для статистики")
    print("  3. Команда /export для скачивания данных")
    print("  4. Команда /alarm для целевой цены")
    print("  5. Утренний отчет в определенное время")
    print("  6. Синхронизация с Google Sheets")
    print("  7. Фильтр по диапазону цен")
    print("  8. Поиск отелей по названию")
