import speech_recognition as sr
import pyttsx3
from googlesearch import search
import os
import pygame
import requests
from bs4 import BeautifulSoup
import random
from goose3 import Goose

API_KEY = '5fdbe308ebce23df8d6e9f78436d40df'

def get_weather(city):
    try:    
        url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&units=metric&appid={API_KEY}"
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            main = data['main']
            weather = data['weather'][0]['description']
            temperature = main['temp']
            speak(f"Погода в городе {city}: {weather}. Температура {temperature} градусов по Цельсию.")
        else:
            speak("Произошла ошибка при получении данных о погоде.")
    except Exception as e:
        print(f"Ошибка при запросе погоды: {str(e)}")
        speak("Произошла ошибка при получении данных о погоде.")
recognizer = sr.Recognizer()
engine = pyttsx3.init()

current_track_index = 0 
is_playing = False 

pygame.init()

def speak(text):
    engine.say(text)
    engine.runAndWait()

def listen():
    with sr.Microphone() as source:
        print("Скажите что-нибудь...")
        audio = recognizer.listen(source)
        try:
            text = recognizer.recognize_google(audio, language="ru-RU")
            print(f"Вы сказали: {text}")
            return text
        except sr.UnknownValueError:
            print("Извините, не могу распознать вашу речь.")
            return ""
        except sr.RequestError:
            print("Произошла ошибка при запросе к сервису распознавания речи.")
            return ""

def search_and_read_answer(query):
    try:
        search_results = list(search(query, lang="ru", num_results=1))
        if search_results:
            result_url = search_results[0]
            g = Goose()
            article = g.extract(result_url) # type: ignore
            answer = article.cleaned_text
            if answer:
                speak("Вот ответ на ваш запрос:")
                speak(answer)
            else:
                speak("На странице не найдено информации.")
        else:
            speak("По вашему запросу ничего не найдено.")
    except Exception as e:
        print(f"Ошибка при выполнении поиска: {str(e)}")
        speak("Произошла ошибка при выполнении поиска.")

def play_random_music():
    global is_playing

    music_folder = "music"
    if not os.path.exists(music_folder):
        speak("Папка с музыкой не найдена.")
        return

    music_files = [file for file in os.listdir(music_folder) if file.endswith((".mp3", ".wav"))]
    if not music_files:
        speak("В папке с музыкой нет поддерживаемых файлов.")
        return

    pygame.mixer.init()
    while True:
        if not is_playing:
            random_track_index = random.randint(0, len(music_files) - 1)
            music_path = os.path.join(music_folder, music_files[random_track_index])
            pygame.mixer.music.load(music_path)
            pygame.mixer.music.play()
            speak(f"Воспроизводится трек: {music_files[random_track_index]}")
            is_playing = True

        command = listen()
        if isinstance(command, str):
            command = command.lower()
        else:
            command = ""
        if "пауза" in command:
            pygame.mixer.music.pause()
            is_playing = False
            speak("Музыка поставлена на паузу.")
        elif "воспроизведи" in command:
            pygame.mixer.music.unpause()
            is_playing = True
            speak("Продолжаю воспроизведение.")
        elif "следующий трек" in command:
            pygame.mixer.music.stop()
            is_playing = False
            speak("Переключаюсь на следующий случайный трек.")
        elif "предыдущий трек" in command:
            pygame.mixer.music.stop()
            is_playing = False
            speak("Переключаюсь на предыдущий случайный трек.")
        elif "стоп" in command:
            pygame.mixer.music.stop()
            is_playing = False
            speak("Музыка остановлена.")
        elif "выход" in command:
            pygame.mixer.quit()
            speak("Выход из режима музыки.")
            break

def add_note():
    try:
        with open('todo-list.txt', 'a', encoding='utf-8') as file:
            speak("Что вы хотели бы добавить в список дел?")
            new_note = listen()
            if new_note:
                file.write(f"- {new_note}\n")
                speak("Заметка добавлена в список дел.")
            else:
                speak("Извините, не могу записать вашу заметку. Пожалуйста, повторите.")
    except Exception as e:
        print(f"Ошибка при добавлении заметки: {str(e)}")
        speak("Произошла ошибка при добавлении заметки.")

if __name__ == "__main__":
    speak("Здравствуйте! Я ваш голосовой помощник.")
    
    while True:
        command = listen()
        if isinstance(command, str):
            command = command.lower()
        else:
            command = ""
        
        if "привет" in command:
            speak("Привет! Чем могу помочь?")
        elif "поиск" in command:
            speak("Что вы хотели бы найти?")
            search_query = listen()
            if search_query:
                search_and_read_answer(search_query)
            else:
                speak("Пожалуйста, повторите ваш запрос.")
        elif "включи музыку" in command:
            play_random_music()
        elif "добавь заметку" in command:
            add_note()
        elif "погода" in command:
            speak("Для какого города вы хотите узнать погоду?")
        city = listen()
        if city:
            get_weather(city)
        elif "пока" in command:
            speak("До свидания!")
            break
        else:
            speak("Извините, я не понял вашу команду. Пожалуйста, повторите.")
