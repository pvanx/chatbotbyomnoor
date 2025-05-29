from config import (
    API_HASH,
    API_ID,
    BOT_TOKEN,
    COOKIES_SRCHHPGUSR,
    COOKIES_U,
    GEMINI_API_KEY,
)
from nsdev import ChatbotGemini, ImageGenerator, LoggerHandler
from pyrogram import Client

app = Client(name="genai", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

chatbot = ChatbotGemini(GEMINI_API_KEY)
image = ImageGenerator(COOKIES_U, COOKIES_SRCHHPGUSR)
logger = LoggerHandler()
