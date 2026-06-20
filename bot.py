import os
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message
import asyncio

from assistant import YandexAssistantClient
from bitrix24_rag import Bitrix24RAG

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

if not TELEGRAM_TOKEN:
    raise RuntimeError("TELEGRAM_TOKEN is not set in environment. Copy config.example.env -> .env and set values.")

bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher()

rag = Bitrix24RAG(base_url=os.getenv("BITRIX24_DOCS_BASE_URL", "https://apidocs.bitrix24.ru/"))
assistant = YandexAssistantClient()


@dp.message(Command(commands=["start", "help"]))
async def start(msg: Message):
    await msg.reply("Привет! Я бот-ассистент по документации Bitrix24. Задайте вопрос.")


@dp.message()
async def handle_message(msg: Message):
    text = (msg.text or "").strip()
    if not text:
        await msg.reply("Пожалуйста, отправьте вопрос текстом.")
        return

    await msg.reply("Ищу релевантную документацию и формирую ответ...")

    contexts = rag.retrieve(text, top_k=3)
    answer = assistant.generate(text, contexts)

    # send answer in chunks if large
    for chunk in (answer[i:i+4000] for i in range(0, len(answer), 4000)):
        await msg.reply(chunk)


def run():
    import logging
    logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
    from aiogram import executor
    executor.start_polling(dp, skip_updates=True)


if __name__ == "__main__":
    run()
