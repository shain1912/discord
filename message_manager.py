import asyncio
import discord
from typing import AsyncGenerator
import logging

logger = logging.getLogger(__name__)

class MessageManager:
    """메시지 처리 관련 유틸리티"""
    
    @staticmethod
    async def safe_followup_send(interaction, content: str, ephemeral: bool = False, **kwargs):
        """안전한 followup 메시지 전송"""
        try:
            return await interaction.followup.send(content, ephemeral=ephemeral, **kwargs)
        except discord.errors.HTTPException as e:
            logger.error(f"Failed to send followup message: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error in followup send: {e}")
            return None
    
    @staticmethod 
    async def streaming_response_handler(interaction, content_generator: AsyncGenerator[str, None], 
                                       prefix: str = "") -> None:
        """스트리밍 응답 처리 (줄바꿈 수정됨)"""
        content = ""
        message = None
        last_update = 0
        
        async for chunk in content_generator:
            content += chunk
            
            # 처음 메시지 또는 300자마다 업데이트
            if message is None:
                # 처음 메시지 전송 - 실제 줄바꿈 사용
                display_content = content if len(content) <= 2000 else content[:1950] + "\n\n**[계속 입력 중...]**"
                message = await MessageManager.safe_followup_send(
                    interaction, 
                    f"{prefix}{display_content}"
                )
                last_update = len(content)
                
            elif len(content) - last_update >= 300:  # 300자마다 업데이트
                last_update = len(content)
                try:
                    # 기존 메시지 수정 - 실제 줄바꿈 사용
                    display_content = content if len(content) <= 2000 else content[:1950] + "\n\n**[계속 입력 중...]**"
                    await message.edit(content=f"{prefix}{display_content}")
                except discord.errors.HTTPException:
                    # 수정 실패시 무시하고 계속
                    pass
        
        # 최종 메시지 수정
        if message is not None:
            try:
                if len(content) <= 2000:
                    # 전체 내용이 2000자 이하인 경우 - 실제 줄바꿈 사용
                    await message.edit(content=f"{prefix}{content}")
                else:
                    # 2000자 초과인 경우 - 실제 줄바꿈 사용
                    await message.edit(content=f"{prefix}{content[:1950]}\n\n**[계속 ⬇️]**")
                    
                    # 나머지 내용을 새 메시지들로 전송
                    remaining = content[1950:]
                    chunk_num = 2
                    while remaining:
                        chunk = remaining[:1950]
                        remaining = remaining[1950:]
                        if remaining:  # 아직 더 있다면 - 실제 줄바꿈 사용
                            await MessageManager.safe_followup_send(
                                interaction,
                                f"**[계속 {chunk_num}]**\n\n{chunk}\n\n**[계속 ⬇️]**"
                            )
                        else:  # 마지막 청크 - 실제 줄바꿈 사용
                            await MessageManager.safe_followup_send(
                                interaction,
                                f"**[계속 {chunk_num}]**\n\n{chunk}"
                            )
                        chunk_num += 1
                        
            except discord.errors.HTTPException:
                # 수정 실패시 새 메시지로 전송
                await MessageManager.safe_followup_send(
                    interaction,
                    f"**[최종 응답]**\n\n{content[:2000]}"
                )
        else:
            # message가 None인 경우 (매우 짧은 응답) - 실제 줄바꿈 사용
            await MessageManager.safe_followup_send(
                interaction,
                f"{prefix}{content}"
            )

# 글로벌 인스턴스 생성
message_manager = MessageManager()
