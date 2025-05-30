from nsdev import Argument, ChatbotGemini, ImageGenerator, LoggerHandler
from pyrogram import Client, filters
from dotenv import load_dotenv 
import os 

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
COOKIES_SRCHHPGUSR = os.getenv("COOKIES_SRCHHPGUSR")
COOKIES_U = os.getenv("COOKIES_U")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

app = Client(name="genai", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

argument = Argument()
chatbot = ChatbotGemini(GEMINI_API_KEY)
db = DataBase(
    "storage_type": "sqlite",
    "binary_keys": 5788533467743994, 
    "method_encrypt": "binary"
)
image = ImageGenerator(COOKIES_U, COOKIES_SRCHHPGUSR)
logger = LoggerHandler()


@app.on_message(filters.command(["ai", "image", "khodam", "setcountphoto"]))
async def main_command(client, message):
    command = message.command[0]
    getarg = argument.getMessage(message, is_arg=True)

    if not getarg:
        return await message.reply("**Silahkan gunakan perintah sambil masukkan yang kamu inginkan**")

    if command == "ai":
        pass
    if command == "image":
        pass
    if command == "khodam":
        pass
    if command == "setcountphoto":
        pass
