"""
Утилиты для Hotel Price Tracker Bot
Функции для парсинга, экспорта и работы с данными
"""

import json
import csv
from datetime import datetime
from typing import Optional, Dict, List
import re

class PriceParser:
    """Утилита для парсинга цен с разных форматов"""
    
    @staticmethod
    def extract_price(text: str) -> Optional[str]:
        """
        Извлечь цену из текста
        
        Примеры:
        "$1,234.50" -> "1234.50"
        "1234 UAH" -> "1234"
        "1 234,50 грн" -> "1234,50"
        """
        if not text:
            return None
        
        # Удалить все пробелы
        text = text.replace(' ', '')
        
        # Удалить валюты и буквы
        price = re.sub(r'[a-zA-Z₽€$]', '', text)
        
        # Удалить специальные символы кроме точки и запятой
        price = re.sub(r'[^\d.,]', '', price)
        
        # Нормализовать разделители
        if price.count(',') > 1 or price.count('.') > 1:
            # Случай типа "1.234,50" или "1,234.50"
            if price.rfind(',') > price.rfind('.'):
                price = price.replace('.', '').replace(',', '.')
            else:
                price = price.replace(',', '')
        else:
            # Заменить запятую на точку если это десятичный разделитель
            if ',' in price and price.count(',') == 1:
                if price.index(',') > len(price) - 4:
                    price = price.replace(',', '.')
        
        return price.strip() if price else None
    
    @staticmethod
    def compare_prices(old_price: str, new_price: str) -> Dict[str, any]:
        """
        Сравнить две цены и вернуть информацию об изменении
        
        Returns:
            {
                'changed': bool,
                'old': float,
                'new': float,
                'difference': float,
                'percent': float,
                'direction': 'up' | 'down' | 'same'
            }
        """
        try:
            old = float(old_price)
            new = float(new_price)
        except (ValueError, TypeError):
            return {'changed': False, 'error': 'Invalid price format'}
        
        if old == new:
            return {
                'changed': False,
                'old': old,
                'new': new,
                'difference': 0,
                'percent': 0,
                'direction': 'same'
            }
        
        difference = new - old
        percent = (difference / old * 100) if old != 0 else 0
        direction = 'down' if difference < 0 else 'up'
        
        return {
            'changed': True,
            'old': old,
            'new': new,
            'difference': abs(difference),
            'percent': round(percent, 2),
            'direction': direction
        }
    
    @staticmethod
    def format_price(price: str, currency: str = "грн") -> str:
        """Форматировать цену для вывода"""
        try:
            price_float = float(price)
            return f"{price_float:,.2f} {currency}".replace(',', ' ')
        except (ValueError, TypeError):
            return price

class DataExporter:
    """Утилита для экспорта данных"""
    
    @staticmethod
    def export_to_csv(data: Dict, filename: str = "hotel_prices.csv") -> bool:
        """Экспортировать данные в CSV"""
        try:
            with open(filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['User ID', 'Hotel Name', 'URL', 'Last Price', 'Added Date', 'Last Check'])
                
                for user_id, user_data in data.items():
                    for hotel_id, hotel_info in user_data.get('hotels', {}).items():
                        writer.writerow([
                            user_id,
                            hotel_info.get('name', ''),
                            hotel_info.get('url', ''),
                            hotel_info.get('last_price', ''),
                            hotel_info.get('added_date', ''),
                            hotel_info.get('last_check', '')
                        ])
            return True
        except Exception as e:
            print(f"Ошибка при экспорте: {e}")
            return False
    
    @staticmethod
    def export_to_json(data: Dict, filename: str = "hotel_prices_backup.json") -> bool:
        """Создать резервную копию в JSON"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"Ошибка при резервной копии: {e}")
            return False
    
    @staticmethod
    def get_statistics(data: Dict) -> Dict:
        """Получить статистику по отелям"""
        total_users = len(data)
        total_hotels = sum(len(user_data.get('hotels', {})) for user_data in data.values())
        
        all_prices = []
        for user_data in data.values():
            for hotel_info in user_data.get('hotels', {}).values():
                if hotel_info.get('last_price'):
                    try:
                        all_prices.append(float(hotel_info['last_price']))
                    except ValueError:
                        pass
        
        return {
            'total_users': total_users,
            'total_hotels': total_hotels,
            'average_price': round(sum(all_prices) / len(all_prices), 2) if all_prices else 0,
            'min_price': round(min(all_prices), 2) if all_prices else 0,
            'max_price': round(max(all_prices), 2) if all_prices else 0,
            'prices_tracked': len(all_prices)
        }

class MessageFormatter:
    """Утилита для форматирования сообщений"""
    
    @staticmethod
    def format_price_change_message(
        hotel_name: str,
        old_price: str,
        new_price: str,
        url: str,
        comparison: Dict
    ) -> str:
        """Форматировать сообщение об изменении цены"""
        
        direction = "📉" if comparison['direction'] == 'down' else "📈"
        
        message = f"""{direction} *Цена изменилась!*

📍 *{hotel_name}*
❌ Была: {old_price}
✅ Стала: {new_price}
💱 Разница: {comparison['difference']:.2f}
📊 Изменение: {comparison['percent']:.1f}%
🔗 [Открыть отель]({url})
⏰ {datetime.now().strftime('%d.%m.%Y %H:%M')}
"""
        return message
    
    @staticmethod
    def format_statistics_message(stats: Dict) -> str:
        """Форматировать сообщение со статистикой"""
        message = f"""📊 *Статистика отслеживания*

👥 Пользователей: {stats['total_users']}
🏨 Отелей: {stats['total_hotels']}
💰 Средняя цена: {stats['average_price']:.2f}
📈 Максимум: {stats['max_price']:.2f}
📉 Минимум: {stats['min_price']:.2f}
"""
        return message
    
    @staticmethod
    def format_hotel_list(hotels: Dict) -> str:
        """Форматировать список отелей"""
        if not hotels:
            return "📭 Нет отслеживаемых отелей"
        
        message = "📊 *Твои отели:*\n\n"
        for hotel_id, hotel_data in hotels.items():
            message += f"""🔹 *{hotel_data['name']}*
   💰 Цена: {hotel_data.get('last_price', 'не определена')}
   📅 Добавлен: {hotel_data.get('added_date', 'неизвестно')[:10]}
   ID: `{hotel_id}`
"""
        return message

class URLValidator:
    """Утилита для проверки и нормализации URL"""
    
    @staticmethod
    def is_valid_url(url: str) -> bool:
        """Проверить, является ли строка валидным URL"""
        return url.startswith('http://') or url.startswith('https://')
    
    @staticmethod
    def is_poehalisnami_url(url: str) -> bool:
        """Проверить, что URL с сайта poehalisnami.ua"""
        return 'poehalisnami.ua' in url.lower()
    
    @staticmethod
    def normalize_url(url: str) -> str:
        """Нормализовать URL (добавить протокол если нужно)"""
        if not url.startswith('http'):
            url = 'https://' + url
        return url

class DateFormatter:
    """Утилита для работы с датами"""
    
    @staticmethod
    def format_time_ago(iso_datetime: str) -> str:
        """Форматировать время в формате 'N часов назад'"""
        try:
            dt = datetime.fromisoformat(iso_datetime)
            now = datetime.now()
            diff = now - dt
            
            if diff.days > 0:
                return f"{diff.days} дней назад"
            elif diff.seconds > 3600:
                hours = diff.seconds // 3600
                return f"{hours} часов назад"
            else:
                minutes = diff.seconds // 60
                return f"{minutes} минут назад"
        except:
            return "давно"
    
    @staticmethod
    def get_readable_datetime(iso_datetime: str) -> str:
        """Преобразовать ISO datetime в читаемый формат"""
        try:
            dt = datetime.fromisoformat(iso_datetime)
            return dt.strftime('%d.%m.%Y %H:%M')
        except:
            return iso_datetime

# Примеры использования
if __name__ == '__main__':
    print("🧪 Тестирование утилит...\n")
    
    # Тест парсера цен
    print("1️⃣ Тест PriceParser:")
    prices = ["$1,234.50", "1234 UAH", "1 234,50 грн"]
    for price in prices:
        extracted = PriceParser.extract_price(price)
        print(f"  '{price}' -> '{extracted}'")
    
    # Тест сравнения цен
    print("\n2️⃣ Тест сравнения цен:")
    comparison = PriceParser.compare_prices("1000", "900")
    print(f"  1000 -> 900: {comparison['percent']:.1f}% {comparison['direction']}")
    
    # Тест валидации URL
    print("\n3️⃣ Тест URLValidator:")
    urls = [
        "https://www.poehalisnami.ua/hotel/123",
        "poehalisnami.ua/hotel/456",
        "example.com"
    ]
    for url in urls:
        valid = URLValidator.is_valid_url(url)
        poehali = URLValidator.is_poehalisnami_url(url)
        print(f"  {url}")
        print(f"    Valid: {valid}, Poehali: {poehali}")
    
    print("\n✅ Все утилиты готовы к использованию!")
