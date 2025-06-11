async def setup_error_events(bot):
    """봇 에러 이벤트 설정"""
    
    @bot.event
    async def on_command_error(ctx, error):
        """명령어 에러 처리"""
        print(f"Command error: {error}")
        await ctx.send("명령어 실행 중 오류가 발생했습니다.")
