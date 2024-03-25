import logging
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from keen_bot.data import config


logging.basicConfig(level=logging.INFO)

bot = Bot(token=config.API_KEY, parse_mode=types.ParseMode.HTML)
storage = MemoryStorage()
dp = Dispatcher(bot,  storage=storage)


