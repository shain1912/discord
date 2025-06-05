import discord

async def create_service_channels(guild):
    try:
        # 카테고리 생성
        category = await guild.create_category("GPT 서비스")
        
        # 안내 채널 생성
        announcement = await category.create_text_channel("📢안내-공지")
        await announcement.set_permissions(guild.default_role, send_messages=False)
        
        # 일반 채팅방 생성
        for i in range(1, 4):
            await category.create_text_channel(f"💭채팅방-{i}")
        
        # 이미지 생성방 생성
        for i in range(1, 4):
            await category.create_text_channel(f"🎨이미지생성-{i}")
        
        print(f"✅ 채널 설정 완료: {guild.name}")
    except Exception as e:
        print(f"채널 생성 중 오류 발생: {str(e)}")
        
def setup_bot_events(bot):
    @bot.event
    async def on_ready():
        print(f"✅ 봇 로그인 완료: {bot.user.name}")
        
        # 모든 서버에 채널 생성
        for guild in bot.guilds:
            # 이미 "GPT 서비스" 카테고리가 있는지 확인
            if not discord.utils.get(guild.categories, name="GPT 서비스"):
                await create_service_channels(guild)
        
        await bot.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.playing,
                name="!chat로 GPT와 대화하기"
            )
        )

    @bot.event
    async def on_guild_join(guild):
        # 새로운 서버에 참가했을 때 채널 생성
        await create_service_channels(guild)
