import os
import re
from bs4 import BeautifulSoup
import aiohttp
import asyncio
from fake_headers import Headers
from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher
from aiogram.utils import executor
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

bot = Bot(token="token")
dp = Dispatcher(bot)

async def get_weather() -> str:
    # Создаем заголовки для запроса (нужны для обхода защиты от парсинга)
    headers = Headers(os="mac", headers=True).generate()
    url = 'https://www.gismeteo.ru/weather-veliky-novgorod-4090/now/'

    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            html = await response.text()

    soup = BeautifulSoup(html, 'lxml')

    time = soup.find('div', class_='tab-content').find('div', class_='day').text
    celsia = soup.find('span', class_='unit unit_temperature_c').text
    feels = soup.find('div', class_='weather-feel').text
    sostoyanie = soup.find('div', class_='now-desc').text
    info = soup.find('div', class_='now-info').find('div', class_='info-wrap').find_all('div', class_='item-title')
    value = soup.find('div', class_='now-info').find('div', class_='info-wrap').find_all('div', class_='item-value')

    result = f"Сейчас в {time}, {celsia} градусов\n{feels[0:15]} градусов\nТекущая оценка погоды: {sostoyanie}\n"

    for i in range(len(info)):
        if info[i].text == 'Ветер':
            wind_data = re.findall(r'\d+м/c', value[i].text)
            if len(wind_data) > 0:
                wind_speed = wind_data[0]
            else:
                wind_speed = "Нет данных"
            if len(re.findall(r'[А-Я]+', value[i].text)) > 0:
                wind_direction = re.findall(r'[А-Я]+', value[i].text)[0]
            else:
                wind_direction = "Нет данных"
            result += f"{info[i].text}: {wind_speed} {wind_direction}\n"
        elif info[i].text.startswith('Вода'):
            water_temperature = list(filter(str.isdigit, value[i].text))[0]
            result += f"{info[i].text}: +{water_temperature}\n"
        else:
            result += f"{info[i].text}: {value[i].text}\n"

    return result

@dp.message_handler(commands=['start'])
async def process_start_command(message: types.Message):
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    weather_button = KeyboardButton(text="Погода")
    wind_button = KeyboardButton(text="Ветер")
    water_button = KeyboardButton(text="Температура воды")
    keyboard.add(weather_button).add(wind_button).add(water_button)

    await message.answer("Привет! Выбери что тебе нужно", reply_markup=keyboard)

@dp.message_handler(lambda message: message.text == "Погода")
async def send_weather(message: types.Message):
    weather_info = await get_weather()

    await message.answer(weather_info)

@dp.message_handler(lambda message: message.text == "Ветер")
async def send_wind(message: types.Message):
    weather_info = await get_weather()
    
    wind_data = re.findall(r'\d+м/c', weather_info)
    if len(wind_data) > 0:
        wind_speed = wind_data[0]
    else:
        wind_speed = "Нет данных"
    
    wind_direction_data = re.findall(r'[А-Я]+', weather_info)
    if wind_direction_data and len(wind_direction_data) > 0:
        wind_direction = wind_direction_data[0]
    else:
        wind_direction = "Нет данных"
    
    await message.answer(f"Скорость ветра: {wind_speed}\nНаправление ветра: {wind_direction}")

@dp.message_handler(lambda message: message.text == "Температура воды")
async def send_water_temperature(message: types.Message):
    weather_info = await get_weather()
    water_temperature_data = re.findall(r'\d+', weather_info)
    if len(water_temperature_data) > 0:
        water_temperature = water_temperature_data[3]
    else:
        water_temperature = "Нет данных"

    await message.answer(f"Температура воды: +{water_temperature}")

if __name__ == '__main__':
    # Запускаем бота
    executor.start_polling(dp, skip_updates=True)
