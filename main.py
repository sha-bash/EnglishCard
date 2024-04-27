import threading
import schedule
import time
import requests
import random
import telebot
from telebot import types
import psycopg2
from translatepy import Translator

from db_config import DB_NAME, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT
from get_tokens import GetTokens
from data_user import process_user_data, add_word_to_student

class WordnikAPI:
    def __init__(self):
        self.api_url = 'http://api.wordnik.com/v4'
        self.api_key = GetTokens.get_wordnik_token()
        self.headers = {'Accept': 'application/json'}
        self.params = {
            'api_key': self.api_key,
            'hasDictionaryDef': 'true',
            'minDictionaryCount': '1',
            'minLength': '5'
        }

    def get_random_words(self, limit=10):
        params = self.params.copy()
        params.update({'limit': limit})
        response = requests.get(f'{self.api_url}/words.json/randomWords', params=params, headers=self.headers)
        response.raise_for_status()
        return [item['word'] for item in response.json()]

class DatabaseManager:
    @staticmethod
    def get_connection():
        return psycopg2.connect(dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD, host=DB_HOST, port=DB_PORT)

    @staticmethod
    def insert_words(words):
        with DatabaseManager.get_connection() as conn, conn.cursor() as cursor:
            cursor.executemany("INSERT INTO words (english_word, russian_translation) VALUES (%s, %s);", words)
            conn.commit()

def update_words():
    wordnik_api = WordnikAPI()
    translator = Translator()
    random_words = wordnik_api.get_random_words()
    translated_words = [(word, translator.translate(word, 'ru').result) for word in random_words]
    DatabaseManager.insert_words(translated_words)

def schedule_updates():
    schedule.every(12).hours.do(update_words)
    while True:
        schedule.run_pending()
        time.sleep(1)

bot = telebot.TeleBot(GetTokens.get_tokentg())

@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True).add(types.KeyboardButton("Начать"))
    user_id = message.from_user.id
    process_user_data(user_id, message.from_user.username, message.from_user.first_name, message.from_user.last_name)
    greeting = f"Привет, {message.from_user.first_name}! Я твой бот помощник в изучении английского языка!"
    bot.send_message(message.chat.id, greeting, reply_markup=markup)

def get_words():
    with DatabaseManager.get_connection() as conn:
        with conn.cursor() as cursor:
            query = "SELECT english_word, russian_translation FROM words;"
            try:
                cursor.execute(query)
                words = cursor.fetchall()
                en_to_ru_dict = {word[0]: word[1] for word in words}
                en_words = list(en_to_ru_dict.keys())
                return en_words, en_to_ru_dict
            except Exception as e:
                print(f"An error occurred: {e}")
                return [], {}

@bot.message_handler(content_types=['text'])
def create_card(message):
    if message.text == 'Начать':
        en_words, en_to_ru_dict = get_words()
        random_en_word = random.choice(en_words)
        correct_ru_translation = en_to_ru_dict[random_en_word]

        all_ru_translations = list(en_to_ru_dict.values())
        random.shuffle(all_ru_translations)

        wrong_translations = [translation for translation in all_ru_translations if translation != correct_ru_translation]
        random_wrong_translations = random.sample(wrong_translations, 3)

        translations = [correct_ru_translation] + random_wrong_translations
        random.shuffle(translations)

        markup = types.InlineKeyboardMarkup()
        for translation in translations:
            button = types.InlineKeyboardButton(text=translation, callback_data=translation)
            markup.add(button)
        bot.send_message(message.chat.id, f'Как переводится слово: {random_en_word}', reply_markup=markup)

# Обработчик нажатий на кнопки
@bot.callback_query_handler(func=lambda call: True)
def query_handler(call):
    en_words, en_to_ru_dict = get_words()
    english_word = call.message.text.split()[-1]
    correct_ru_translation = en_to_ru_dict.get(english_word, None)

    if call.data == correct_ru_translation:
        bot.answer_callback_query(callback_query_id=call.id, show_alert=True, text=f"Верно! Слово {english_word} переводится как {correct_ru_translation}")
        try:
            bot.delete_message(call.message.chat.id, call.message.message_id)
        except Exception as e:
            print(f"Не удалось удалить сообщение с карточкой вопроса: {e}")
        add_word_to_student(call.from_user.id, english_word)
        create_card(call.message)
    else:
        bot.answer_callback_query(callback_query_id=call.id, show_alert=True, text="Неверно, попробуйте еще раз.")

if __name__ == "__main__":
    thread = threading.Thread(target=schedule_updates, daemon=True)
    thread.start()
    bot.polling(none_stop=True, interval=0)

