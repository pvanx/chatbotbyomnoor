import asyncio
import os
from collections import defaultdict
from dataclasses import dataclass
from typing import List, Optional, Union
from time import time

from dotenv import load_dotenv
from nsdev import (
    Argument,
    ChatbotGemini,
    DataBase,
    ImageGenerator,
    LoggerHandler
)
from pyrogram import Client, filters
from pyrogram.types import Message, InputMediaPhoto

@dataclass
class Config:
    API_ID: int
    API_HASH: str
    BOT_TOKEN: str
    COOKIES_SRCHHPGUSR: str
    COOKIES_U: str
    GEMINI_API_KEY: str

    @classmethod
    def from_env(cls) -> 'Config':
        load_dotenv()
        return cls(
            API_ID=int(os.getenv("API_ID", "0")),
            API_HASH=os.getenv("API_HASH", ""),
            BOT_TOKEN=os.getenv("BOT_TOKEN", ""),
            COOKIES_SRCHHPGUSR=os.getenv("COOKIES_SRCHHPGUSR", ""),
            COOKIES_U=os.getenv("COOKIES_U", ""),
            GEMINI_API_KEY=os.getenv("GEMINI_API_KEY", "")
        )

class RateLimiter:
    
    def __init__(self, requests_limit: int = 5, time_window: int = 60):
        self._requests_limit = requests_limit
        self._time_window = time_window
        self._user_requests: defaultdict = defaultdict(list)

    def is_rate_limited(self, user_id: int) -> bool:
     
        current_time = time()
        user_requests = self._user_requests[user_id]
        
        user_requests = [
            timestamp for timestamp in user_requests
            if current_time - timestamp < self._time_window
        ]
        self._user_requests[user_id] = user_requests
        
        if len(user_requests) >= self._requests_limit:
            return True
            
        user_requests.append(current_time)
        return False

class TelegramBot:
    
    def __init__(self, config: Config):
        self.config = config
        self.client = Client(
            name="genai",
            api_id=config.API_ID,
            api_hash=config.API_HASH,
            bot_token=config.BOT_TOKEN
        )
        
        self.argument = Argument()
        self.chatbot = ChatbotGemini(config.GEMINI_API_KEY)
        self.db = DataBase(
            storage_type="sqlite",
            binary_keys=5788533467743994,
            method_encrypt="binary"
        )
        self.image_gen = ImageGenerator(
            config.COOKIES_U,
            config.COOKIES_SRCHHPGUSR
        )
        self.logger = LoggerHandler()
        self.rate_limiter = RateLimiter(requests_limit=5, time_window=60)
        
        self.register_handlers()

    def register_handlers(self) -> None:
        @self.client.on_message(filters.command(["ai", "image", "khodam", "setcountphoto"]))
        async def handle_commands(client: Client, message: Message) -> None:
            await self._process_command(message)

    async def _process_command(self, message: Message) -> None:
        if self.rate_limiter.is_rate_limited(message.from_user.id):
            await message.reply("**tunggu beberapa saat sebelum mengirim perintah lagi.**")
            return

        command = message.command[0]
        args = self.argument.getMessage(message, is_arg=True)

        if not args:
            await message.reply("**silahkan gunakan perintah sambil masukkan yang kamu inginkan**")
            return

        status_message = await message.reply("**sedang memproses...**")
        
        try:
            await self._execute_command(command, args, message, status_message)
        except Exception as e:
            await asyncio.gather(
                status_message.delete(),
                message.reply(f"**terjadi kesalahan: {str(e)}**")
            )

    async def _execute_command(
        self,
        command: str,
        args: str,
        message: Message,
        status_message: Message
    ) -> None:
        if command == "ai":
            result = self.chatbot.send_chat_message(
                args,
                message.from_user.id,
                self.client.me.first_name
            )
            await self._send_response(status_message, message, result)

        elif command == "image":
            count = int(self.db.getVars(self.client.me.id, "COUNT_PHOTO") or 1)
            images = await self.image_gen.generate(args, count)
            media = [InputMediaPhoto(photo) for photo in images]
            await asyncio.gather(
                status_message.delete(),
                message.reply_media_group(media)
            )

        elif command == "khodam":
            result = self.chatbot.send_khodam_message(args)
            await self._send_response(status_message, message, result)

        elif command == "setcountphoto":
            if not args.isdigit():
                raise ValueError("jumlah harus berupa angka**")
                
            self.db.setVars(self.client.me.id, "COUNT_PHOTO", args)
            await self._send_response(
                status_message,
                message,
                f"**jumlah gambar yang akan di generate berhasil diubah ke {args}**"
            )

    async def _send_response(
        self,
        status_msg: Message,
        original_msg: Message,
        response: str
    ) -> None:
        await asyncio.gather(
            status_msg.delete(),
            original_msg.reply(response)
        )

    def run(self) -> None:
        self.logger.print(
            f"{self.logger.CYAN}"
            f"{self.argument.getNamebot(self.config.BOT_TOKEN)} "
            f"{self.logger.PURPLE}| "
            f"{self.logger.GREEN}berhasil dijalankan"
        )
        self.client.run()

def main() -> None:
    config = Config.from_env()
    bot = TelegramBot(config)
    bot.run()

if __name__ == "__main__":
    main()