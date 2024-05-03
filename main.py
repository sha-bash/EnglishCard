import threading
import schedule
import time
import random
import telebot
from telebot import types
from translatepy import Translator

from get_tokens import GetTokens
from database import DatabaseManager
from WordnikAPI import WordnikAPI


bot = telebot.TeleBot(GetTokens.get_tokentg())
db_manager = DatabaseManager()


def update_words():
    wordnik_api = WordnikAPI()
    translator = Translator()
    random_words = wordnik_api.get_random_words()
    translated_words = [(word, translator.translate(word, 'ru').result) for word in random_words]
    db_manager.insert_words(translated_words)

def schedule_updates():
    schedule.every(12).hours.do(update_words)
    while True:
        schedule.run_pending()
        time.sleep(1)

main_markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
btn1 = types.KeyboardButton("Учиться")
btn2 = types.KeyboardButton("Мои слова")
main_markup.add(btn1, btn2)

study_markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
btn3 = types.KeyboardButton("Новое слово")
btn4 = types.KeyboardButton("Главное меню")
study_markup.add(btn3, btn4)

@bot.message_handler(commands=['start']) 
def start(message): 
    user_id = message.from_user.id
    db_manager.process_user_data(user_id, message.from_user.username, message.from_user.first_name, message.from_user.last_name)
    greeting = f"Привет, {message.from_user.first_name}! Я твой бот помощник в изучении английского языка!"
    bot.send_message(message.chat.id, greeting, reply_markup=main_markup)
    bot.send_message(message.chat.id, "Выберий пункт меню", reply_markup=main_markup)

@bot.message_handler(content_types=['text'])
def handle_text(message):
    if message.text == 'Учиться':
        bot.send_message(message.chat.id, "Для старта нажмите 'Новое слово'", reply_markup=study_markup)
    elif message.text == 'Новое слово':
        create_card(message)
    elif message.text == 'Мои слова':
        my_words(message)
    elif message.text == 'Главное меню':
        bot.send_message(message.chat.id, "Возвращаемся в главное меню", reply_markup=main_markup)

def create_card(message):
    en_words, en_to_ru_dict = db_manager.get_words()
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

def my_words(message):
    user_id = message.from_user.id
    en_user_words, en_to_ru_user_dict = db_manager.get_user_words(user_id)

    words_list = ' '.join([f"{word} - {en_to_ru_user_dict[word]}\n" for word in en_user_words])

    if words_list:
        bot.send_message(message.chat.id, "Ваши слова и переводы: " + words_list, reply_markup=main_markup)
    else:
        bot.send_message(message.chat.id, "У вас пока нет изучаемых слов.", reply_markup=main_markup)


@bot.callback_query_handler(func=lambda call: True)
def query_handler(call):
    en_words, en_to_ru_dict = db_manager.get_words()
    english_word = call.message.text.split()[-1]
    correct_ru_translation = en_to_ru_dict.get(english_word, None)

    if call.data == correct_ru_translation:
        bot.answer_callback_query(callback_query_id=call.id, show_alert=True, text=f"Верно! Слово {english_word} переводится как {correct_ru_translation}")
        bot.delete_message(call.message.chat.id, call.message.message_id)
        db_manager.add_word_to_student(call.from_user.id, english_word)
        create_card(call.message)
    else:
        bot.answer_callback_query(callback_query_id=call.id, show_alert=True, text="Неверно, попробуйте еще раз.")

if __name__ == "__main__":
    db_manager.create_schema() 
    update_words()
    thread = threading.Thread(target=schedule_updates, daemon=True)
    thread.start()
    bot.polling(none_stop=True, interval=0)