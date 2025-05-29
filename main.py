from config import (
    API_HASH,
    API_ID,
    BOT_TOKEN,
    COOKIES_SRCHHPGUSR,
    COOKIES_U,
    GEMINI_API_KEY,
)
from nsdev import ChatbotGemini, ImageGenerator, LoggerHandler, Argument 
from pyrogram import Client, filters 

app = Client(name="genai", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

chatbot = ChatbotGemini(GEMINI_API_KEY)
image = ImageGenerator(COOKIES_U, COOKIES_SRCHHPGUSR)
logger = LoggerHandler()


@app.on_message(filters.command(["ai", "image", "khodam")]))
async def main_command(client, message):
    command = message.command[0]
    getarg = Argument().getMessage(message, is_arg=True)

    if not getarg:
        return await message.reply("**Silahkan gunakan perintah sambil masukkan yang kamu inginkan**")

    if command == "ai":
        pass
    if command == "image":
        pass 
    if command == "khodam":
        pass
