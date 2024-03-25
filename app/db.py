
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.server_api import ServerApi
import pymongo


async def init_db(db_name):
    try:
        uri = "mongodb://localhost:27017"

        client = AsyncIOMotorClient(uri, server_api=ServerApi('1'))
    except Exception as e:
        print(f"Ошибка при инициализации БД: {e}")
    return client




