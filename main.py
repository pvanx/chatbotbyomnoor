import asyncio
import os
from collections import defaultdict
from dataclasses import dataclass
from typing import List, Optional, Union
from time import time
from functools import wraps
from concurrent.futures import ThreadPoolExecutor

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

class ServiceRateLimiter:
    def __init__(self, limits: dict):
        self._limits = limits
        self._requests = defaultdict(lambda: defaultdict(list))

    async def check_limit(self, service: str, user_id: int) -> tuple[bool, float]:
        current_time = time()
        requests = self._requests[service][user_id]
        
        requests = [t for t in requests if current_time - t < self._limits[service]["window"]]
        self._requests[service][user_id] = requests
        
        if len(requests) >= self._limits[service]["max_requests"]:
            wait_time = self._limits[service]["window"] - (current_time - requests[0])
            return True, wait_time
        
        requests.append(current_time)
        return False, 0.0

def to_async(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, lambda: func(*args, **kwargs))
    return wrapper

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
        self._executor = ThreadPoolExecutor(max_workers=10)
        
        service_limits = {
            "telegram": {"max_requests": 20, "window": 60},
            "gemini": {"max_requests": 60, "window": 60},
            "image": {"max_requests": 10, "window": 60}
        }
        self.service_limiter = ServiceRateLimiter(service_limits)
        self.rate_limiter = RateLimiter(requests_limit=5, time_window=60)

        self.register_handlers()

    def register_handlers(self) -> None:
        @self.client.on_message(filters.command(["ai", "image", "khodam", "setcountphoto", "ping"]))
        async def handle_commands(client: Client, message: Message) -> None:
            await self._process_command(message)

    async def _async_chat_message(self, *args, **kwargs):
        return await to_async(self.chatbot.send_chat_message)(*args, **kwargs)
    
    async def _async_khodam_message(self, *args, **kwargs):
        return await to_async(self.chatbot.send_khodam_message)(*args, **kwargs)
    
    async def _async_db_get(self, *args, **kwargs):
        return await to_async(self.db.getVars)(*args, **kwargs)
    
    async def _async_db_set(self, *args, **kwargs):
        return await to_async(self.db.setVars)(*args, **kwargs)

    async def _process_command(self, message: Message) -> None:
        command = message.command[0]
        user_id = message.from_user.id

        if command == "ping":
            start_time = time()
            msg = await message.reply("**cek latensi botanj...**")
            end_time = time()
            await msg.edit(f"**latency: {round((end_time - start_time) * 1000)}ms**")
            return

        is_limited, wait_time = await self.service_limiter.check_limit("telegram", user_id)
        if is_limited:
            await message.reply(f"**mohon tunggu {round(wait_time)} detik sebelum mengirim pesan lagi.**")
            return

        args = self.argument.getMessage(message, is_arg=True)
        if not args:
            await message.reply("**silahkan gunakan perintah sambil masukkan prompt yang kamu inginkan**")
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
        user_id = message.from_user.id

        if command == "ai":
            is_limited, wait_time = await self.service_limiter.check_limit("gemini", user_id)
            if is_limited:
                await status_message.edit(f"**Mohon tunggu {round(wait_time)} detik sebelum menggunakan lagi.**")
                return

            result = await self._async_chat_message(args, user_id, self.client.me.first_name)
            await self._send_response(status_message, message, result)

        elif command == "image":
            is_limited, wait_time = await self.service_limiter.check_limit("image", user_id)
            if is_limited:
                await status_message.edit(f"**mohon tunggu {round(wait_time)} detik sebelum generate gambar lagi.**")
                return

            count = int(await self._async_db_get(self.client.me.id, "COUNT_PHOTO") or 1)
            images = await self.image_gen.generate(args, count)
            media = [InputMediaPhoto(photo) for photo in images]
            await asyncio.gather(
                status_message.delete(),
                message.reply_media_group(media)
            )

        elif command == "khodam":
            is_limited, wait_time = await self.service_limiter.check_limit("gemini", user_id)
            if is_limited:
                await status_message.edit(f"**mohon tunggu {round(wait_time)} detik sebelum menggunakan Khodam lagi.**")
                return

            result = await self._async_khodam_message(args)
            await self._send_response(status_message, message, result)

        elif command == "setcountphoto":
            if not args.isdigit():
                raise ValueError("**jumlah harus berupa angka**")
            
            await self._async_db_set(self.client.me.id, "COUNT_PHOTO", args)
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