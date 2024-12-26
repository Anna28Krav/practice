import sqlite3
import telebot
import logging
from telebot import types
import requests

# Параметри бота
DB_NAME = 'bot_database.db'  # Назва файлу бази даних
TOKEN = '7841518347:AAENiHfUyxNWFKS_qJLH8p0eOaq6kPJ5WQU'  # Заміни на свій токен
bot = telebot.TeleBot(TOKEN)

logging.basicConfig(
    filename='bot.log',
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Підключення до бази даних
def connect_to_db():
    return sqlite3.connect(DB_NAME)

# Ініціалізація бази даних
def initialize_database():
    connection = sqlite3.connect(DB_NAME)
    cursor = connection.cursor()

    # Створення таблиці користувачів
    cursor.execute(''' 
        CREATE TABLE IF NOT EXISTS Users (
            Id INTEGER PRIMARY KEY,
            Counter INTEGER DEFAULT 0
        )
    ''')

    # Створення таблиці для результатів пошуку
    cursor.execute(''' 
        CREATE TABLE IF NOT EXISTS SearchResult (
            Id INTEGER PRIMARY KEY AUTOINCREMENT,
            UserId INTEGER,
            Link TEXT,
            FOREIGN KEY(UserId) REFERENCES Users(Id)
        )
    ''')

    # Створення таблиці для вибраних відео
    cursor.execute(''' 
        CREATE TABLE IF NOT EXISTS Favorites (
            Id INTEGER PRIMARY KEY AUTOINCREMENT,
            UserId INTEGER,
            Link TEXT,
            FOREIGN KEY(UserId) REFERENCES Users(Id)
        )
    ''')
    connection.commit()
    connection.close()

# Додавання користувача до бази даних
def add_user(chat_id):
    connection = connect_to_db()
    cursor = connection.cursor()
    cursor.execute('INSERT OR IGNORE INTO Users (Id) VALUES (?)', (chat_id,))
    connection.commit()
    connection.close()

# Збереження результатів пошуку
def save_search_results(chat_id, links):
    connection = connect_to_db()
    cursor = connection.cursor()
    cursor.execute('DELETE FROM SearchResult WHERE UserId = ?', (chat_id,))
    connection.commit()

    for link in links:
        cursor.execute('INSERT INTO SearchResult (UserId, Link) VALUES (?, ?)', (chat_id, link))
    connection.commit()
    connection.close()

# Додавання відео в обране
def add_to_favorites(chat_id, link):
    connection = connect_to_db()
    cursor = connection.cursor()
    cursor.execute('INSERT INTO Favorites (UserId, Link) VALUES (?, ?)', (chat_id, link))
    connection.commit()
    connection.close()

# Видалення відео з обраного
def remove_from_favorites(chat_id, link):
    connection = connect_to_db()
    cursor = connection.cursor()
    cursor.execute('DELETE FROM Favorites WHERE UserId = ? AND Link = ?', (chat_id, link))
    connection.commit()
    connection.close()

# Отримання списку обраних відео
def get_favorites(chat_id):
    connection = connect_to_db()
    cursor = connection.cursor()
    cursor.execute('SELECT Link FROM Favorites WHERE UserId = ?', (chat_id,))
    favorites = cursor.fetchall()
    connection.close()
    return [item[0] for item in favorites]

# Пошук відео на YouTube
def youtube_search(query, sort_by="relevance"):
    API_KEY = 'AIzaSyBKuvZ7SGUXkvw8vzaRCkHjxVWVnhx32YE'  # Заміни на свій API ключ
    url = 'https://www.googleapis.com/youtube/v3/search'
    params = {
        'part': 'snippet',
        'q': query,
        'type': 'video',
        'maxResults': 5,
        'order': sort_by,
        'key': API_KEY
    }
    response = requests.get(url, params=params)
    data = response.json()
    links = []
    for item in data.get('items', []):
        video_id = item['id']['videoId']
        links.append(f'https://www.youtube.com/watch?v={video_id}')
    return links

# Основне меню для користувача
def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton('/search'), types.KeyboardButton('/favorite'))
    markup.add(types.KeyboardButton('/recommend'), types.KeyboardButton('/help'))
    return markup

# Обробка команди /start
@bot.message_handler(commands=['start'])
def handle_start(message):
    chat_id = message.chat.id
    add_user(chat_id)
    bot.send_message(chat_id, 'Привіт! Обери одну з команд нижче:', reply_markup=main_menu())  # Привітання 😊

# Обробка команди /help
@bot.message_handler(commands=['help'])
def handle_help(message):
    chat_id = message.chat.id
    help_text = (
        "Доступні команди:\n"
        "/search - Пошук відео на YouTube 🔍\n"
        "/favorite - Перегляд обраних відео ❤️\n"
        "/recommend - Отримати рекомендації (поки в розробці) 🔜\n"
        "/help - Отримати допомогу 💡\n"
        "📋 Про програму:\n"
        "Цей бот допомагає шукати відео на YouTube, зберігати їх у список обраного та переглядати відео на основі ваших запитів. \n"
        "Ви можете легко додавати відео до обраного та видаляти їх за допомогою зручних кнопок.\n"
        "👨‍💻 Автор: Кравченко Анна\n"
        "📅 Дата створення: 25 грудня 2024 року\n\n"
        "Залишайтеся на зв'язку та користуйтеся всіма можливостями бота! 😊"
    )
    bot.send_message(chat_id, help_text, reply_markup=main_menu())  # Допомога

# Обробка команди /search
@bot.message_handler(commands=['search'])
def handle_search(message):
    chat_id = message.chat.id
    bot.send_message(chat_id, 'Введіть запит для пошуку: 📝', reply_markup=types.ReplyKeyboardRemove())  # Запит на пошук

    @bot.message_handler(func=lambda msg: True)
    def handle_query(msg):
        query = msg.text
        links = youtube_search(query)
        save_search_results(chat_id, links)

        for link in links:
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("Додати в обране ❤️", callback_data=f'add_favorite_{link}'))
            bot.send_message(chat_id, link, reply_markup=markup)

        bot.send_message(chat_id, 'Ви можете додати відео в обране, натиснувши кнопку.', reply_markup=main_menu())  # Пояснення

# Обробка команди /favorite
@bot.message_handler(commands=['favorite'])
def handle_favorite(message):
    chat_id = message.chat.id
    favorites = get_favorites(chat_id)

    if favorites:
        bot.send_message(chat_id, 'Ваші обрані відео: ❤️')
        for link in favorites:
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("Видалити з обраного ❌", callback_data=f'remove_favorite_{link}'))
            bot.send_message(chat_id, link, reply_markup=markup)
    else:
        bot.send_message(chat_id, 'Ваш список обраних порожній. 🥲')
    bot.send_message(chat_id, 'Виберіть одну з команд нижче:', reply_markup=main_menu())  # Запит на вибір

# Обробка додавання в обране через inline кнопку
@bot.callback_query_handler(func=lambda call: call.data.startswith('add_favorite_'))
def handle_add_favorite(callback_query):
    chat_id = callback_query.message.chat.id
    link = callback_query.data.replace('add_favorite_', '')
    add_to_favorites(chat_id, link)
    bot.answer_callback_query(callback_query.id, text=f'Відео додано в обране: {link} 😊')
    bot.send_message(chat_id, f'Відео додано в обране: {link}')
    bot.send_message(chat_id, 'Виберіть одну з команд нижче:', reply_markup=main_menu())

# Обробка видалення з обраного через inline кнопку
@bot.callback_query_handler(func=lambda call: call.data.startswith('remove_favorite_'))
def handle_remove_favorite(callback_query):
    chat_id = callback_query.message.chat.id
    link = callback_query.data.replace('remove_favorite_', '')
    remove_from_favorites(chat_id, link)
    bot.answer_callback_query(callback_query.id, text=f'Відео видалено з обраного: {link} 😢')
    bot.send_message(chat_id, f'Відео видалено з обраного: {link}')
    bot.send_message(chat_id, 'Виберіть одну з команд нижче:', reply_markup=main_menu())

# Обробка команди /recommend
@bot.message_handler(commands=['recommend'])
def handle_recommend(message):
    chat_id = message.chat.id
    bot.send_message(chat_id, 'Рекомендації на основі ваших запитів поки в розробці! 🔜')
    bot.send_message(chat_id, 'Виберіть одну з команд нижче:', reply_markup=main_menu())  # Розробка

# Запуск бота
if __name__ == '__main__':
    initialize_database()
    bot.polling(none_stop=True)
