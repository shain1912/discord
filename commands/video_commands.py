import discord
import asyncio
from discord.ext import commands
from discord import app_commands
from ai_handlers import generate_video
from env_manager import get_instance_config, should_handle_command
async def setup_video_commands(bot):
    """비디오 관련 명령어 설정"""
    
    @bot.tree.command(name="비디오", description="MiniMax AI로 비디오 생성 (최대 5분 소요)")
    async def video(interaction: discord.Interaction, 설명: str):
        """
        MiniMax AI 비디오 생성
        
        사용법:
        /비디오 "고양이가 공원에서 뛰어노는 모습"
        """
        instance_config = get_instance_config()
        if not should_handle_command(interaction, instance_config):
            return  # ❌ 내가 처리할 인스턴스가 아님 → 조용히 무시
        try:
            # 요청 가능 여부 확인
            can_request, message = await bot.request_manager.can_make_request(
                interaction.user.id, 'video'
            )
            if not can_request:
                await interaction.response.send_message(f"⚠️ {message}", ephemeral=True)
                return

            # 초기 응답 전송 (ephemeral) - 실제 줄바꿈 사용
            processing_msg = "🎬 MiniMax AI로 비디오 생성 중... (최대 5분 소요)\n⏰ 비디오 생성은 시간이 오래 걸립니다. 잠시만 기다려주세요!\n📹 고품질 비디오를 제작하고 있습니다..."
            await interaction.response.send_message(processing_msg, ephemeral=True)

            # 주기적 업데이트 메시지 전송을 위한 태스크 생성
            update_task = asyncio.create_task(_send_video_progress_updates(interaction))
            
            try:
                # MiniMax 비디오 생성
                result = await generate_video(설명)
                
                # 업데이트 태스크 취소
                update_task.cancel()
                try:
                    await update_task
                except asyncio.CancelledError:
                    pass
                
                if result.startswith("http"):
                    # 성공적으로 생성된 경우 (ephemeral)
                    embed = discord.Embed(
                        title="🎬 MiniMax AI 생성 비디오",
                        description=설명,
                        color=0x00c851
                    )
                    embed.add_field(
                        name="📥 다운로드 링크", 
                        value=f"[비디오 다운로드]({result})", 
                        inline=False
                    )
                    embed.add_field(
                        name="💡 안내", 
                        value="링크를 클릭하여 비디오를 다운로드하세요.", 
                        inline=False
                    )
                    embed.set_footer(text="Powered by MiniMax T2V-01 | 비디오 링크는 일정 시간 후 만료됩니다")
                    
                    await interaction.followup.send("✅ 비디오 생성이 완료되었습니다!", embed=embed, ephemeral=True)
                else:
                    # 에러 메시지인 경우 (ephemeral)
                    await interaction.followup.send(f"❌ {result}", ephemeral=True)
                    
            except Exception as e:
                # 업데이트 태스크 취소
                update_task.cancel()
                try:
                    await update_task
                except asyncio.CancelledError:
                    pass
                raise e
                
        except Exception as e:
            print(f"Video command error: {e}")
            await interaction.followup.send("비디오 생성 중 오류가 발생했습니다.", ephemeral=True)

async def _send_video_progress_updates(interaction: discord.Interaction):
    """비디오 생성 중 주기적 업데이트 메시지 전송 (ephemeral)"""
    try:
        progress_messages = [
            "🎬 비디오 생성 시작... (1/5분)",
            "🎥 장면 구성 중... (2/5분)",
            "🎨 비주얼 렌더링 중... (3/5분)",
            "🎵 최종 처리 중... (4/5분)",
            "⏰ 거의 완료... (5/5분)"
        ]
        
        for i, message in enumerate(progress_messages):
            await asyncio.sleep(60)  # 1분마다
            try:
                await interaction.followup.send(message, ephemeral=True)
            except:
                # 이미 완료되었을 수 있음
                break
                
    except asyncio.CancelledError:
        # 정상적으로 취소됨
        pass
