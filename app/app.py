# import os
# from keen_bot.main import dp, bot
# from aiogram import types
# import logging
# from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
# import google.generativeai as genai
#
#
#
# @dp.message_handler(commands=['start'])
# async def start_command(message: types.Message):
#     keyboard = InlineKeyboardMarkup()
#     button = InlineKeyboardButton("Ввести лицевой счет", callback_data="button_pressed")
#     keyboard.add(button)
#     await message.answer("Введите лицевой счет, указанный на квитанциях",reply_markup=keyboard)
#
#
# @dp.message_handler(content_types=types.ContentType.ANY)
# async def handle_message(message: types.Message):
#     if message.content_type == types.ContentType.TEXT:
#         await message.answer(message)
#
# @dp.message_handler(content_types=types.ContentType.PHOTO)
# async def handle_photo(message: types.Message):
#     if message.content_type == types.ContentType.PHOTO:
#         model = genai.GenerativeModel(model_name="gemini-pro-vision")
#
#         response = model.generate_content(["Каково количество израсходованной воды в кубических метрах?", message])
#
#
#         await message.answer(response)
#
# if __name__ == "__main__":
#     from aiogram import executor
#     executor.start_polling(dp, skip_updates=True)

import asyncio
from keen_bot.main import dp, bot
from aiogram import types, executor
import logging
from aiogram.utils.exceptions import Throttled

import google.generativeai as genai
import PIL.Image
from keen_bot.app.db import init_db
import requests
import os
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "data/credentials.json"


logging.basicConfig(level=logging.INFO)

"""надеюсь сработает"""
# db  = asyncio.run(init_db("keeenvision"))

from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017")
db = client["keenvision"]
collection = db["users"]

temp = {}


@dp.message_handler(commands=['start'])
async def start_command(message: types.Message):
    try:
        await message.answer("Введите лицевой счет, указанный на квитанциях")
        logging.info(f"User {message.from_user.id} requested /start command")
    except Throttled as e:
        logging.error(f"Bot was throttled: {e}")
        await message.answer("Пожалуйста, повторите запрос позже.")


@dp.message_handler(content_types=types.ContentType.ANY)
async def handle_message(message: types.Message):
    try:
        logging.info(f"Received message from {message.from_user.id}: {message.text}")
        if message.content_type == types.ContentType.TEXT:
            temp["id"] = message.text
            await message.answer("Теперь можете сфотографировать показания")
        else:
            await handle_photo(message)
    except Exception as e:
        logging.exception(f"Error handling message: {e}")
        await message.answer("Произошла ошибка. Попробуйте позже.")

async def process_photo(file_id):
    file_path = await bot.download_file_by_id(file_id)
    img = PIL.Image.open(file_path)

    return img


@dp.message_handler(content_types=types.ContentType.PHOTO)
async def handle_photo(message: types.Message):
  try:
    logging.info(f"Получено фото от @{message.from_user.username}")
    process = await message.answer("Обрабатываем ваш запрос...")
    photo = message.photo[-1]
    file_url = photo.file_id

    img = await process_photo(file_url)

    model = genai.GenerativeModel(model_name="gemini-pro-vision")
    response = model.generate_content(
        ["Каково количество израсходованной воды в кубических метрах(ответь только цифрой)? если на фото нет счетчика воды, ответь 'no'", img])

    if response.text == " no":
        await message.answer("Счётчик не обнаружен, попробуйте снова, или обратитесь в тех поддержку")
        await bot.delete_message(message.chat.id, process.message_id)

    await bot.delete_message(message.chat.id, process.message_id)
    await message.answer(f"Показания счётчика{response.text} отправлены. ")
    temp["meter_reading"] = response.text
    requests.post("http://localhost:8080", data=temp)
    collection.insert_one(temp)
    temp.clear()
  except Exception as e:
    logging.error(f"Ошибка {e}")


if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)