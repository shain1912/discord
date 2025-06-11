import discord
from discord.ext import commands
from discord import app_commands

async def setup_utility_commands(bot):
    """유틸리티 관련 명령어 설정"""
    
    @bot.tree.command(name="핑", description="봇의 응답 시간을 확인합니다.")
    async def ping(interaction: discord.Interaction):
        """봇의 레이턴시를 확인하는 명령어 (ephemeral)"""
        latency_ms = round(bot.latency * 1000)
        
        embed = discord.Embed(
            title="🏓 Pong!",
            description=f"응답 시간: {latency_ms}ms",
            color=0x00ff00
        )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
