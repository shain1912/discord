import discord
from discord.ext import commands
from discord import app_commands
from typing import Optional
import logging

# 로컬 모듈 import
from request_manager import RequestManager
from utils import split_message

class MyBot(commands.Bot):
    def __init__(self):
        # 인텐트 설정
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        
        super().__init__(command_prefix="!", intents=intents)
        
        # 매니저 초기화
        self.request_manager = RequestManager()
        
    async def setup_hook(self):
        """봇 초기 설정"""
        print("Bot is setting up...")
        
        # 명령어 설정
        await self.setup_commands()
        
        # 에러 이벤트 설정
        from bot.events import setup_error_events
        await setup_error_events(self)
        
        # 기본 RequestManager는 queue processor가 없으므로 제거
        # self.request_manager.start_queue_processor(self)
        
        # 슬래시 명령어 동기화
        await self.tree.sync()
        print("Bot setup completed")

    async def setup_commands(self):
        """모든 명령어 설정"""
        from commands.chat_commands import setup_chat_commands
        from commands.image_commands import setup_image_commands
        from commands.video_commands import setup_video_commands
        from commands.utility_commands import setup_utility_commands
        
        await setup_chat_commands(self)
        await setup_image_commands(self)
        await setup_video_commands(self)
        await setup_utility_commands(self)

    async def send_long_message(self, interaction: discord.Interaction, content: str):
        """긴 메시지를 여러 청크로 분할하여 전송"""
        chunks = split_message(content, 2000)
        
        if chunks:
            await interaction.followup.send(chunks[0])
            for chunk in chunks[1:]:
                await interaction.channel.send(chunk)

    async def close(self):
        """봇 종료 시 정리 작업"""
        print("Bot is shutting down...")
        # 기본 RequestManager는 queue processor가 없으므로 제거
        # await self.request_manager.stop_queue_processor()
        await super().close()
