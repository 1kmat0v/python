import os
import telebot
from telebot import types
from googlesearch import search
import requests
from bs4 import BeautifulSoup
import random
import pygame
from goose3 import Goose
import itertools
import wikipedia
from newsapi import NewsApiClient 
import g4f


API_KEY = '5fdbe308ebce23df8d6e9f78436d40df'
NEWS_API_KEY = '97971fdb130f45b0b6ef723a362fa633'

bot = telebot.TeleBot("6694379437:AAFtmeLLh3_n1cj-NKYGRWvqXmP3dYDE0nk")
music_folder = "music"
current_track_index = None

newsapi = NewsApiClient(api_key=NEWS_API_KEY)

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "Здравствуйте! Я ваш телеграм-бот помощник. Введите команду.")

@bot.message_handler(regexp=r'\b(?:как тебя зовут)\b')
def handle_name_request(message):
    bot.reply_to(message, f"Меня зовут Артур.")

@bot.message_handler(func=lambda message: 'артур' in message.text.lower())
def handle_artur(message):
    bot.reply_to(message, "Слушаю вас!")

def handle_user_input(message):
    user_message = message.text
    response = g4f.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": user_message}],
        stream=True,
    )
    full_response = ''.join(list(response))
    bot.send_message(message.chat.id, full_response)

@bot.message_handler(regexp=r'\b(?:новости)\b')
def get_news(message):
    try:
        # Получение топ-5 новостей
        news_headlines = newsapi.get_top_headlines(language='ru', country='ru', page_size=5)

        if news_headlines['status'] == 'ok':
            articles = news_headlines['articles']
            news_list = []

            for article in articles:
                news_list.append(f"{article['title']}\n{article['url']}\n")

            news_text = '\n'.join(news_list)
            bot.reply_to(message, news_text)
        else:
            bot.reply_to(message, "Не удалось получить новости. Попробуйте позже.")
    except Exception as e:
        print(f"Ошибка при получении новостей: {str(e)}")
        bot.reply_to(message, "Произошла ошибка при получении новостей.")


@bot.message_handler(commands=['music'])
def send_music(message):
    chat_id = message.chat.id

    music_files = [file for file in os.listdir(music_folder) if file.endswith((".mp3", ".wav"))]

    if not music_files:
        bot.send_message(chat_id, "В папке с музыкой нет поддерживаемых файлов.")
        return

    random_track_index = random.randint(0, len(music_files) - 1)
    music_path = os.path.join(music_folder, music_files[random_track_index])

    audio = open(music_path, 'rb')
    bot.send_audio(chat_id, audio)
    audio.close()

@bot.message_handler(regexp=r'\b(?:включи музыку)\b')
def handle_play_music(message):
    bot.reply_to(message, play_random_music())

@bot.message_handler(regexp=r'\b(?:стоп)\b')
def handle_stop_music(message):
    bot.reply_to(message, stop_music())

@bot.message_handler(regexp=r'\b(?:следующий трек)\b')
def handle_next_track(message):
    bot.reply_to(message, next_track())


@bot.message_handler(regexp=r'^\d+[+\-*/]\d+$')
def handle_math_expression(message):
    expression = message.text
    try:
        result = eval(expression)
        bot.reply_to(message, f"Результат выражения {expression} равен {result}")
    except Exception as e:
        bot.reply_to(message, "Произошла ошибка при вычислении выражения.")

@bot.message_handler(regexp=r'\b(?:заметки)\b')
def show_notes(message):
    try:
        with open('todo-list.txt', 'r', encoding='utf-8') as file:
            notes = file.read()
            if notes:
                bot.reply_to(message, f"Ваши заметки:\n{notes}")
            else:
                bot.reply_to(message, "Список дел пуст.")
    except Exception as e:
        print(f"Ошибка при чтении списка дел: {str(e)}")
        bot.reply_to(message, "Произошла ошибка при чтении списка дел.")

@bot.message_handler(regexp=r'\b(?:очистить список дел)\b')
def clear_notes(message):
    try:
        with open('todo-list.txt', 'w', encoding='utf-8') as file:
            file.write("")
        bot.reply_to(message, "Список дел очищен.")
    except Exception as e:
        print(f"Ошибка при очистке списка дел: {str(e)}")
        bot.reply_to(message, "Произошла ошибка при очистке списка дел.")

@bot.message_handler(regexp=r'\b(?:привет|здравствуйте)\b')
def handle_greetings(message):
    bot.reply_to(message, "Привет! Как я могу вам помочь?")

@bot.message_handler(regexp=r'\b(?:как дела)\b')
def handle_how_are_you(message):
    bot.reply_to(message, "У меня все отлично, спасибо!")

@bot.message_handler(func=lambda message: True)
def handle_messages(message):
    command = message.text.lower()

    if "привет" in command:
        bot.reply_to(message, "Привет! Чем могу помочь?")
    elif "поиск" in command:
        bot.reply_to(message, "Что вы хотели бы найти?")
        bot.register_next_step_handler(message, search_query_handler)
    elif "включи музыку" in command:
        bot.reply_to(message, play_random_music())
    elif "добавь заметку" in command:
        bot.reply_to(message, "Введите текст заметки:")
        bot.register_next_step_handler(message, add_note)
    elif "погода" in command:
        bot.reply_to(message, "Для какого города вы хотите узнать погоду?")
        bot.register_next_step_handler(message, get_weather_handler)
    elif "пока" in command:
        bot.reply_to(message, "До свидания!")
    elif "ии" in command:  # Заменено на проверку "инпут"
        bot.reply_to(message, "Введите ваш запрос:")
        bot.register_next_step_handler(message, handle_user_input)
    else:
        result = search_and_read_answer(command)
        bot.reply_to(message, result)


def get_weather(city):
    try:
        url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&units=metric&appid={API_KEY}"
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            main = data['main']
            weather = data['weather'][0]['description']
            temperature = main['temp']
            return f"Погода в городе {city}: {weather}. Температура {temperature} градусов по Цельсию."
        else:
            return "Произошла ошибка при получении данных о погоде."
    except Exception as e:
        print(f"Ошибка при запросе погоды: {str(e)}")
        return "Произошла ошибка при получении данных о погоде."
    
# def add_note():
#     try:
#         with open('todo-list.txt', 'a', encoding='utf-8') as file:
#             new_note = input("Что вы хотели бы добавить в список дел? ")
#             if new_note:
#                 file.write(f"- {new_note}\n")
#                 return "Заметка добавлена в список дел."
#             else:
#                 return "Извините, не могу записать вашу заметку. Пожалуйста, повторите."
#     except Exception as e:
#         print(f"Ошибка при добавлении заметки: {str(e)}")
#         return "Произошла ошибка при добавлении заметки."

def add_note(message):
    try:
        with open('todo-list.txt', 'a', encoding='utf-8') as file:
            new_note = message.text
            if new_note:
                file.write(f"- {new_note}\n")
                bot.reply_to(message, "Заметка добавлена в список дел.")
            else:
                bot.reply_to(message, "Извините, не могу записать вашу заметку. Пожалуйста, повторите.")
    except Exception as e:
        print(f"Ошибка при добавлении заметки: {str(e)}")
        bot.reply_to(message, "Произошла ошибка при добавлении заметки.")


# def play_random_music():
#     music_folder = "music"
#     if not os.path.exists(music_folder):
#         return "Папка с музыкой не найдена."

#     music_files = [file for file in os.listdir(music_folder) if file.endswith((".mp3", ".wav"))]
#     if not music_files:
#         return "В папке с музыкой нет поддерживаемых файлов."

#     pygame.init()
#     while True:
#         random_track_index = random.randint(0, len(music_files) - 1)
#         music_path = os.path.join(music_folder, music_files[random_track_index])
#         pygame.mixer.init()
#         pygame.mixer.music.load(music_path)
#         pygame.mixer.music.play()
#         return f"Воспроизводится трек: {music_files[random_track_index]}"

def play_random_music():
    global current_track_index  # Объявляем, что будем использовать глобальную переменную
    music_folder = "music"
    
    if not os.path.exists(music_folder):
        return "Папка с музыкой не найдена."

    music_files = [file for file in os.listdir(music_folder) if file.endswith((".mp3", ".wav"))]
    
    if not music_files:
        return "В папке с музыкой нет поддерживаемых файлов."

    pygame.init()

    if current_track_index is not None:
        # Если уже воспроизводится трек, останавливаем его
        pygame.mixer.music.stop()

    # Выбираем новый случайный трек
    current_track_index = random.randint(0, len(music_files) - 1)
    music_path = os.path.join(music_folder, music_files[current_track_index])
    
    pygame.mixer.init()
    pygame.mixer.music.load(music_path)
    pygame.mixer.music.play()

    return f"Воспроизводится трек: {music_files[current_track_index]}"

def stop_music():
    global current_track_index
    
    if current_track_index is not None:
        pygame.mixer.music.stop()
        return "Музыка остановлена."
    else:
        return "Нет воспроизводимого трека."

def next_track():
    global current_track_index
    
    if current_track_index is not None:
        pygame.mixer.music.stop()
        music_folder = "music"
        music_files = [file for file in os.listdir(music_folder) if file.endswith((".mp3", ".wav"))]
        
        current_track_index = (current_track_index + 1) % len(music_files)
        music_path = os.path.join(music_folder, music_files[current_track_index])
        
        pygame.mixer.init()
        pygame.mixer.music.load(music_path)
        pygame.mixer.music.play()
        
        return f"Переключено на следующий трек: {music_files[current_track_index]}"
    else:
        return "Нет воспроизводимого трека."

def search_and_read_answer(query):
    try:
        search_results = list(itertools.islice(search(query, lang="ru"), 1))
        if search_results:
            result_url = search_results[0]
            response = requests.get(str(result_url))

            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                paragraphs = soup.find_all('p')
                if paragraphs:
                    answer = '\n'.join([p.get_text() for p in paragraphs])
                    return  answer[:4000] + "...   "
                else:
                    return "На странице не найдено информации."
            else:
                return "Ошибка при получении данных с веб-страницы."
        else:
            return "По вашему запросу ничего не найдено."
    except Exception as e:
        print(f"Ошибка при выполнении поиска: {str(e)}")
        return "Произошла ошибка при выполнении поиска."

# def search_and_read_answer(query):
#     try:
#         search_results = list(itertools.islice(search(query, lang="ru"), 1))
#         if search_results:
#             result_url = search_results[0]
#             g = Goose()
#             article = g.extract(raw_html=requests.get(str(result_url)).text)

#             if article.cleaned_text:
#                 sentences = article.cleaned_text.split('. ')
#                 relevant_sentences = [sentence for sentence in sentences if query.lower() in sentence.lower()]

#                 if relevant_sentences:
#                     answer = '\n'.join(relevant_sentences)
#                     return answer[:4000] + "...   "
#                 else:
#                     # Проверка на запросы о людях с использованием Wikipedia API
#                     wikipedia.set_lang("ru")
#                     try:
#                         person_info = wikipedia.summary(query)
#                         return person_info[:4000] + "...   "
#                     except wikipedia.exceptions.DisambiguationError as e:
#                         return f"Уточните ваш запрос: {', '.join(e.options)}"
#                     except wikipedia.exceptions.PageError:
#                         return "На странице не найдено информации."
#             else:
#                 return "На странице нет текстовой информации."
#         else:
#             return "По вашему запросу ничего не найдено."
#     except Exception as e:
#         print(f"Ошибка при выполнении поиска: {str(e)}")
#         return "Произошла ошибка при выполнении поиска."

# def search_and_read_answer(query):
#     try:
#         search_results = list(itertools.islice(search(query, lang="ru"), 1))
#         if search_results:
#             result_url = search_results[0]
#             g = Goose()
#             article = g.extract(raw_html=requests.get(str(result_url)).text)

#             if article.cleaned_text:
#                 sentences = article.cleaned_text.split('. ')
#                 relevant_sentences = [sentence for sentence in sentences if query.lower() in sentence.lower()]

#                 if relevant_sentences:
#                     answer = '\n'.join(relevant_sentences)
#                     return answer[:4000] + "...   "
#                 else:
#                     # Проверка на запросы о людях с использованием Wikipedia API
#                     wikipedia.set_lang("ru")
#                     try:
#                         person_info = wikipedia.summary(query)
#                         return person_info[:4000] + "...   "
#                     except wikipedia.exceptions.DisambiguationError as e:
#                         return f"Уточните ваш запрос: {', '.join(e.options)}"
#                     except wikipedia.exceptions.PageError:
#                         return "На странице не найдено информации."
#             else:
#                 return "На странице нет текстовой информации."
#         else:
#             return "По вашему запросу ничего не найдено."
#     except requests.exceptions.RequestException as req_err:
#         return f"Ошибка при выполнении HTTP-запроса: {str(req_err)}"
#     except Exception as e:
#         return f"Произошла ошибка при выполнении поиска: {str(e)}"

def search_query_handler(message):
    search_query = message.text
    result = search_and_read_answer(search_query)
    bot.reply_to(message, result)

def get_weather_handler(message):
    city = message.text
    result = get_weather(city)
    bot.reply_to(message, result)

if __name__ == "__main__":
    bot.polling(none_stop=True)
