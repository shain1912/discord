import os
import discord
from discord.ext import commands
from dotenv import load_dotenv

from request_manager import RequestManager
from channel_manager import setup_bot_events
from ai_handlers import get_gpt_response, generate_image

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

# 인텐트 설정 업데이트
intents = discord.Intents.default()
intents.message_content = True
intents.members = True  # 멤버 관련 이벤트 활성화

class MyBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents)
        self.request_manager = RequestManager()
        
    async def setup_hook(self):  # 봇 초기 설정을 위한 새로운 방식
        print("Bot is setting up...")
        await self.tree.sync()  # 슬래시 명령어 동기화

bot = MyBot()
setup_bot_events(bot)

# 명령어 정의는 여기서부터 시작

@bot.command()
async def chat(ctx, *, question):
    # 요청 가능 여부 확인
    can_request, message = await bot.request_manager.can_make_request(ctx.author.id, 'chat')
    if not can_request:
        await ctx.send(f"⚠️ {message}")
        return

    # 초기 메시지 전송
    init_message = await ctx.send("생각하는 중...")
    
    # 스트리밍 응답 생성 및 실시간 업데이트
    response = await get_gpt_response(bot, question, init_message)
    
    # 최종 응답이 2000자를 넘으면 나눠서 다시 보내기
    if len(response) > 2000:
        await init_message.delete()
        for i in range(0, len(response), 2000):
            await ctx.send(response[i:i+2000])
    elif not response.startswith("오류가 발생했습니다"):
        # 성공적인 응답인 경우 그대로 둠
        pass
    else:
        # 오류 발생 시 메시지 교체
        await init_message.edit(content=response)

# 기존 명령어 방식
@bot.command()
async def ping(ctx):
    await ctx.send(f"🏓 Pong! {round(bot.latency * 1000)}ms")

# 최신 슬래시 명령어 방식
@bot.tree.command(name="hello", description="인사를 합니다")
async def hello(interaction: discord.Interaction):
    await interaction.response.send_message(f"안녕하세요, {interaction.user.name}님!")

# 버튼 기능이 있는 명령어
class SimpleView(discord.ui.View):
    @discord.ui.button(label="Click me!", style=discord.ButtonStyle.primary)
    async def button_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("버튼이 클릭되었습니다!", ephemeral=True)

@bot.command()
async def button(ctx):
    view = SimpleView()
    await ctx.send("아래 버튼을 눌러보세요:", view=view)

# 버튼 UI 클래스 정의

@bot.command()
async def img(ctx, *, description=None):
    # 요청 가능 여부 확인
    can_request, message = await bot.request_manager.can_make_request(ctx.author.id, 'image')
    if not can_request:
        await ctx.send(f"⚠️ {message}")
        return

    # 설명이 없는 경우
    if not description and not ctx.message.attachments:
        await ctx.send("❌ 이미지 설명을 입력하거나 변환할 이미지를 첨부해주세요!")
        return

    async with ctx.typing():
        try:
            # 첨부된 이미지가 있는 경우
            source_image_url = None
            if ctx.message.attachments:
                attachment = ctx.message.attachments[0]
                if attachment.content_type.startswith('image/'):
                    source_image_url = attachment.url
                else:
                    await ctx.send("❌ 유효한 이미지 파일을 첨부해주세요!")
                    return

            # 이미지 URL 생성
            image_url = await generate_image(bot, description or "변형해주세요", source_image_url)
            
            if image_url.startswith("http"):
                # 임베드 생성
                embed = discord.Embed(
                    title="🎨 생성된 이미지", 
                    description=description or "이미지 변형 결과"
                )
                if source_image_url:
                    embed.add_field(name="원본 이미지", value="첨부된 이미지 기반으로 생성되었습니다.")
                embed.set_image(url=image_url)
                await ctx.send(embed=embed)
            else:
                # 에러 메시지 전송
                await ctx.send(image_url)
        except Exception as e:
            await ctx.send(f"오류가 발생했습니다: {str(e)}")

bot.run(TOKEN)
