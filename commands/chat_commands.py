import discord
from discord.ext import commands
from discord import app_commands
from ai_handlers import get_gpt_response_streaming

async def setup_chat_commands(bot):
    """채팅 관련 명령어 설정"""
    
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

            # 초기 응답 전송 (ephemeral)
            await interaction.response.send_message("🤔 ChatGPT가 답변을 생성하고 있습니다...", ephemeral=True)
            
            # 스트리밍 GPT 응답 생성
            await get_gpt_response_streaming(bot, 질문, interaction)
            
        except Exception as e:
            print(f"Chat command error: {e}")
            await interaction.followup.send("채팅 응답 생성 중 오류가 발생했습니다.", ephemeral=True)
