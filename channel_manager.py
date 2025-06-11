import discord
import logging
from dotenv import load_dotenv
import os
logger = logging.getLogger(__name__)
CHAT_DAILY_LIMIT = os.getenv("CHAT_DAILY_LIMIT")
IMAGE_DAILY_LIMIT = os.getenv("IMAGE_DAILY_LIMIT")
VIDEO_DAILY_LIMIT = os.getenv("VIDEO_DAILY_LIMIT")

CHANNEL_NUMS = int(os.getenv("CHANNEL_NUMS"))

async def create_service_channels(guild, num):
    """서비스 채널들을 생성"""
    try:
        # 카테고리 생성
        category = await guild.create_category("AI 서비스")
        
        # 안내 채널 생성
        announcement = await category.create_text_channel("📢안내-공지")
        await announcement.set_permissions(guild.default_role, send_messages=False)
        
        # 일반 채팅방 생성
        for i in range(1, num+1):
            await category.create_text_channel(f"💭명령어-{i}")
        
        # 이미지 생성방 생성
        for i in range(1, num+1):
            await category.create_text_channel(f"🎨갤러리-{i}")
        
        # 환영 메시지 전송
        embed = discord.Embed(
            title="🤖 GPT 서비스에 오신 것을 환영합니다!",
            description="AI와 함께하는 새로운 경험을 시작해보세요.",
            color=0x00ff00
        )
        
        embed.add_field(
            name="📋 사용 가능한 명령어",
            value=(
                "`/채팅 [질문]` - ChatGPT와 대화 (스트리밍)\n"
                "`/이미지 [프롬프트1] [프롬프트2]` - MiniMax 이미지 생성\n"
                "`/img [설명] [이미지] [강도]` - Stability AI 빠른 이미지\n"
                "`/비디오 [설명] [이미지]` - MiniMax 비디오 생성\n"
                "`/핑` - 봇 상태 확인하기"
            ),
            inline=False
        )
        
        embed.add_field(
            name="📝 이용 안내",
            value=(
                f"• 각 명령어는 쿨다운이 있습니다\n"
                f"• 채팅: 일일 {CHAT_DAILY_LIMIT}회 제한 (스트리밍 방식)\n"
                f"• 이미지 or img: 일일 {IMAGE_DAILY_LIMIT}회 제한\n"
                f"• 비디오: 일일 {VIDEO_DAILY_LIMIT}회 제한 (최대 5분)\n"
            ),
            inline=False
        )
        
        await announcement.send(embed=embed)
        
        print(f"✅ 채널 설정 완료: {guild.name}")
        
    except Exception as e:
        print(f"채널 생성 중 오류 발생: {str(e)}")

def setup_bot_events(bot):
    """봇 이벤트 설정"""
    
    @bot.event
    async def on_ready():
        print(f"✅ 봇 로그인 완료: {bot.user.name}")
        
        # 모든 서버에 채널 생성
        for guild in bot.guilds:
            # 이미 "GPT 서비스" 카테고리가 있는지 확인
            if not discord.utils.get(guild.categories, name="AI 서비스"):
                await create_service_channels(guild, CHANNEL_NUMS)
        
        await bot.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.playing,
                name="/명령어로 봇에 명령하기"
            )
        )

    @bot.event
    async def on_guild_join(guild):
        """새로운 서버에 참가했을 때 채널 생성"""
        await create_service_channels(guild, CHANNEL_NUMS)
