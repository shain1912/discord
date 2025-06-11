import os
import asyncio
import discord
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv
from typing import Optional
import logging

# 로컬 모듈 import
from request_manager import RequestManager
from channel_manager import setup_bot_events
from ai_handlers import generate_image, get_gpt_response_streaming, generate_stability_image
from utils import setup_logging, split_message

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
        
        # Queue processor 시작
        self.request_manager.start_queue_processor(self)
        
        # 슬래시 명령어 동기화
        await self.tree.sync()
        print("Bot setup completed")

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
        await self.request_manager.stop_queue_processor()
        await super().close()

def create_bot() -> MyBot:
    """봇 인스턴스 생성"""
    # 환경 변수 로드
    load_dotenv()
    
    # 로깅 설정
    setup_logging("INFO")
    
    # 봇 생성
    bot = MyBot()
    
    # 이벤트 설정
    setup_bot_events(bot)
    
    return bot

# 봇 인스턴스 생성
bot = create_bot()

@bot.tree.command(name="채팅", description="ChatGPT와 대화를 시작합니다.")
async def chat(interaction: discord.Interaction, 질문: str):
    """ChatGPT와 대화하는 명령어 (스트리밍 방식)"""
    try:
        # 요청 가능 여부 확인
        can_request, message = await bot.request_manager.can_make_request(
            interaction.user.id, 'chat'
        )
        if not can_request:
            await interaction.response.send_message(f"⚠️ {message}", ephemeral=True)
            return

        # 초기 응답 전송
        await interaction.response.defer(thinking=True)
        await interaction.followup.send("🤔 ChatGPT가 답변을 생성하고 있습니다...")
        
        # 스트리밍 GPT 응답 생성
        await get_gpt_response_streaming(bot, 질문, interaction)
        
    except Exception as e:
        print(f"Chat command error: {e}")
        await interaction.followup.send("채팅 응답 생성 중 오류가 발생했습니다.", ephemeral=True)

@bot.tree.command(name="이미지", description="AI로 이미지를 생성하거나 변환합니다.")
async def image(interaction: discord.Interaction, 파라미터1: str, 파라미터2: Optional[str] = None):
    """
    이미지 생성/변환 명령어
    
    사용 방법:
    1. 텍스트를 이미지로 변환: /이미지 "설명"
    2. 이미지를 변환: /이미지 "설명" "이미지_url"
    3. 이미지를 변환: /이미지 "이미지_url" "설명"
    4. 이미지를 기반으로 새로운 이미지 생성: /이미지 "이미지_url"
    """
    try:
        # 요청 가능 여부 확인
        can_request, message = await bot.request_manager.can_make_request(
            interaction.user.id, 'image'
        )
        if not can_request:
            await interaction.response.send_message(f"⚠️ {message}", ephemeral=True)
            return

        # 파라미터 해석
        설명, 이미지_url = _parse_image_parameters(파라미터1, 파라미터2)

        # 이미지 생성 시작
        await interaction.response.defer(thinking=True)
        
        processing_msg = (
            "🎨 이미지 변환 중입니다... (최대 60초 소요)" if 이미지_url 
            else "🎨 이미지 생성 중입니다... (최대 60초 소요)"
        )
        processing_msg += "\n💡 팁: 간단한 설명일수록 빠르게 생성됩니다!"
        await interaction.followup.send(processing_msg)

        # 이미지 생성
        image_url = await generate_image(bot, 설명, 이미지_url)
        
        if image_url.startswith("http"):
            # 성공적으로 생성된 경우
            embed = discord.Embed(
                title="🎨 생성된 이미지",
                description=설명 if 설명 else "이미지 변환",
                color=0x00ff00
            )
            embed.set_image(url=image_url)
            await interaction.followup.send(embed=embed)
        else:
            # 에러 메시지인 경우
            await interaction.followup.send(f"❌ {image_url}")
            
    except Exception as e:
        print(f"Image command error: {e}")
        await interaction.followup.send("이미지 생성 중 오류가 발생했습니다.", ephemeral=True)

def _parse_image_parameters(param1: str, param2: Optional[str]) -> tuple[Optional[str], Optional[str]]:
    """이미지 명령어 파라미터를 파싱하여 설명과 이미지 URL을 반환"""
    설명 = None
    이미지_url = None
    
    # 파라미터1이 URL인지 확인
    if param1.startswith("http"):
        이미지_url = param1
        설명 = param2
    else:
        설명 = param1
        이미지_url = param2 if param2 and param2.startswith("http") else None
    
    return 설명, 이미지_url

@bot.tree.command(name="img", description="Stability AI로 빠른 이미지 생성 (이미지 첫부 가능)")
async def img(interaction: discord.Interaction, 설명: str, 이미지: Optional[discord.Attachment] = None, 강도: Optional[float] = 0.7):
    """
    Stability AI 이미지 생성
    
    사용법:
    1. 텍스트만: /img "고양이" 
    2. 이미지 변환: /img "만화스타일" + 이미지 청부
    3. 강도 조절: /img "만화스타일" + 이미지 + 강도:0.5
    """
    try:
        # 요청 가능 여부 확인
        can_request, message = await bot.request_manager.can_make_request(
            interaction.user.id, 'image'
        )
        if not can_request:
            await interaction.response.send_message(f"⚠️ {message}", ephemeral=True)
            return

        # 강도 범위 검증 (0.1-1.0)
        if 강도 < 0.1 or 강도 > 1.0:
            await interaction.response.send_message("⚠️ 강도는 0.1~1.0 사이의 값이어야 합니다.", ephemeral=True)
            return
        
        # 이미지 첫부 파일 검증
        if 이미지:
            # 파일 크기 및 형식 검증
            if 이미지.size > 4 * 1024 * 1024:  # 4MB 제한
                await interaction.response.send_message("⚠️ 이미지 파일이 너무 큽니다. (4MB 이하만 가능)", ephemeral=True)
                return
            
            # 이미지 형식 검증
            allowed_types = ['image/png', 'image/jpeg', 'image/jpg', 'image/webp']
            if 이미지.content_type not in allowed_types:
                await interaction.response.send_message(
                    "⚠️ 지원되지 않는 이미지 형식입니다. (PNG, JPEG, WebP만 지원)", 
                    ephemeral=True
                )
                return

        # 초기 응답 전송
        await interaction.response.defer(thinking=True)
        
        if 이미지:
            # Image-to-Image 모드
            processing_msg = f"✨ Stability AI 이미지 변환 중... (강도: {강도})"
            processing_msg += "\n🔄 업로드된 이미지를 설명에 따라 변환합니다!"
            processing_msg += f"\n📊 강도 {int(강도*100)}% - 높을수록 원본 이미지 무시"
        else:
            # Text-to-Image 모드
            processing_msg = "⚡ Stability AI로 이미지 생성 중... (최대 45초)"
            processing_msg += "\n✨ 고품질 이미지를 빠르게 생성합니다!"
        
        await interaction.followup.send(processing_msg)

        # Stability AI 이미지 생성
        result = await generate_stability_image(설명, 이미지, 강도)
        
        if isinstance(result, bytes):
            # 성공적으로 생성된 경우
            import io
            file = discord.File(io.BytesIO(result), filename="stability_image.png")
            
            # 모드에 따라 다른 임베드 색상
            if 이미지:
                embed_color = 0xff6b6b  # 빨간색 (이미지 변환)
                embed_title = "🔄 Stability AI 이미지 변환"
                embed_desc = f"{설명} (강도: {int(강도*100)}%)"
            else:
                embed_color = 0x7c3aed  # 보라색 (이미지 생성)
                embed_title = "⚡ Stability AI 생성 이미지"
                embed_desc = 설명
            
            embed = discord.Embed(
                title=embed_title,
                description=embed_desc,
                color=embed_color
            )
            embed.set_image(url="attachment://stability_image.png")
            embed.set_footer(text="Powered by Stability AI SD3.5 Turbo")
            
            await interaction.followup.send(embed=embed, file=file)
        else:
            # 에러 메시지인 경우
            await interaction.followup.send(f"❌ {result}")
            
    except Exception as e:
        print(f"Stability AI command error: {e}")
        await interaction.followup.send("이미지 생성 중 오류가 발생했습니다.", ephemeral=True)

@bot.tree.command(name="핑", description="봇의 응답 시간을 확인합니다.")
async def ping(interaction: discord.Interaction):
    """봇의 레이턴시를 확인하는 명령어"""
    latency_ms = round(bot.latency * 1000)
    
    embed = discord.Embed(
        title="🏓 Pong!",
        description=f"응답 시간: {latency_ms}ms",
        color=0x00ff00
    )
    
    await interaction.response.send_message(embed=embed)

@bot.event
async def on_command_error(ctx, error):
    """명령어 에러 처리"""
    print(f"Command error: {error}")
    await ctx.send("명령어 실행 중 오류가 발생했습니다.")

def main():
    """메인 함수"""
    # 환경 변수에서 토큰 가져오기
    TOKEN = os.getenv("DISCORD_TOKEN")
    
    if not TOKEN:
        print("❌ DISCORD_TOKEN이 환경변수에 설정되지 않았습니다.")
        return
    
    try:
        # 봇 실행
        bot.run(TOKEN)
    except Exception as e:
        print(f"Bot failed to start: {e}")

if __name__ == "__main__":
    main()
