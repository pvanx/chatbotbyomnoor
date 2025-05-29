from pyrogram import Client 
from nsdev import LoggerHandler, ImageGenerator, ChatbotGemini

from config import BOT_TOKEN, API_ID, API_HASH, COOKIES_U COOKIES_SRCHHPGUSR GEMINI_API_KEY

app = Client(name="genai", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

chatbot = ChatbotGemini(GEMINI_API_KEY)
image = ImageGenerator(COOKIES_U, COOKIES_SRCHHPGUSR)
logger = LoggerHandler()
