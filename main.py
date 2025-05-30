import asyncio
import os

from dotenv import load_dotenv
from nsdev import Argument, ChatbotGemini, DataBase, ImageGenerator, LoggerHandler
from pyrogram import Client, filters
from pyrogram.types import InputMediaPhoto

load_dotenv()

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
COOKIES_SRCHHPGUSR = os.getenv("COOKIES_SRCHHPGUSR")
COOKIES_U = os.getenv("COOKIES_U")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

app = Client(name="genai", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

argument = Argument()
chatbot = ChatbotGemini(GEMINI_API_KEY)
db = DataBase(storage_type="sqlite", binary_keys=5788533467743994, method_encrypt="binary")
image = ImageGenerator(COOKIES_U, COOKIES_SRCHHPGUSR)
logger = LoggerHandler()


@app.on_message(filters.command(["ai", "image", "khodam", "setcountphoto"]))
async def main_command(client, message):
    command = message.command[0]
    getarg = argument.getMessage(message, is_arg=True)

    msg = await message.reply("**Sedang memproses...**")

    if not getarg:
        return await msg.edit("**Silahkan gunakan perintah sambil masukkan yang kamu inginkan**")

    if command == "ai":
        result = chatbot.send_chat_message(getarg, message.from_user.id, client.me.first_name)
        await asyncio.gather(msg.delete(), message.reply(result))

    if command == "image":
        try:
            result = await image.generate(getarg, int(db.getVars(client.me.id, "COUNT_PHOTO")) or 1)
            media = [InputMediaPhoto(photo) for photo in result]
            await asyncio.gather(msg.delete(), client.send_media_group(message.chat.id, media, reply_to_message_id=message.id))
        except Exception as error:
            await asyncio.gather(msg.delete(), message.reply(error))

    if command == "khodam":
        result = chatbot.send_khodam_message(getarg)
        await asyncio.gather(msg.delete(), message.reply(result))

    if command == "setcountphoto":
        try:
            db.setVars(client.me.id, "COUNT_PHOTO", int(getarg))
            await asyncio.gather(
                msg.delete(), message.reply(f"**Jumlah gambar yang akan di generate berhasil diubah ke {getarg}**")
            )
        except Exception:
            await asyncio.gather(msg.delete(), message.reply("**Jumlah harus berupa angka**"))


logger.print(f"{logger.WHITE}{argument.getNamebot(BOT_TOKEN)} {logger.PURPLE}| {logger.GREEN}berhasil dijalankan")
app.run()
