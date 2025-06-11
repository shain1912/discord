import discord
from discord.ext import commands
from discord import app_commands
from typing import Optional
from ai_handlers import generate_image, generate_stability_image

async def setup_image_commands(bot):
    """이미지 관련 명령어 설정"""
    
    @bot.tree.command(name="이미지", description="AI로 이미지를 생성하거나 변환합니다.")
    async def image(interaction: discord.Interaction, 설명: str, 이미지: Optional[discord.Attachment] = None):
        """
        이미지 생성/변환 명령어
        
        사용 방법:
        1. 텍스트를 이미지로 변환: /이미지 "설명"
        2. 이미지를 변환: /이미지 "설명" + 이미지 첨부
        """
        try:
            # 요청 가능 여부 확인
            can_request, message = await bot.request_manager.can_make_request(
                interaction.user.id, 'image'
            )
            if not can_request:
                await interaction.response.send_message(f"⚠️ {message}", ephemeral=True)
                return

            # 이미지 첨부 파일 검증
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

            # 이미지 생성 시작 (ephemeral)
            if 이미지:
                processing_msg = f"🎨 이미지 변환 중입니다... (최대 60초 소요)\\n🔄 업로드된 이미지를 설명에 따라 변환합니다!\\n💡 팁: 간단한 설명일수록 빠르게 생성됩니다!"
            else:
                processing_msg = f"🎨 이미지 생성 중입니다... (최대 60초 소요)\\n✨ 설명에 따라 새로운 이미지를 생성합니다!\\n💡 팁: 간단한 설명일수록 빠르게 생성됩니다!"
            
            await interaction.response.send_message(processing_msg, ephemeral=True)

            # 이미지 생성 (Discord Attachment 객체 직접 전달)
            image_url = await generate_image(bot, 설명, 이미지)
            
            if image_url.startswith("http"):
                # 성공적으로 생성된 경우 (ephemeral)
                if 이미지:
                    embed_title = "🔄 이미지 변환 완료"
                    embed_color = 0xff6b6b  # 빨간색 (이미지 변환)
                else:
                    embed_title = "🎨 이미지 생성 완료"
                    embed_color = 0x00ff00  # 초록색 (이미지 생성)
                
                embed = discord.Embed(
                    title=embed_title,
                    description=설명,
                    color=embed_color
                )
                embed.set_image(url=image_url)
                await interaction.followup.send(embed=embed, ephemeral=True)
            else:
                # 에러 메시지인 경우 (ephemeral)
                await interaction.followup.send(f"❌ {image_url}", ephemeral=True)
                
        except Exception as e:
            print(f"Image command error: {e}")
            await interaction.followup.send("이미지 생성 중 오류가 발생했습니다.", ephemeral=True)

    @bot.tree.command(name="img", description="Stability AI로 빠른 이미지 생성 (이미지 첨부 가능)")
    async def img(interaction: discord.Interaction, 설명: str, 이미지: Optional[discord.Attachment] = None, 강도: Optional[float] = 0.7):
        """
        Stability AI 이미지 생성
        
        사용법:
        1. 텍스트만: /img "고양이" 
        2. 이미지 변환: /img "만화스타일" + 이미지 첨부
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
            
            # 이미지 첨부 파일 검증
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

            # 초기 응답 전송 (ephemeral)
            if 이미지:
                # Image-to-Image 모드
                processing_msg = f"✨ Stability AI 이미지 변환 중... (강도: {강도})\\n🔄 업로드된 이미지를 설명에 따라 변환합니다!\\n📊 강도 {int(강도*100)}% - 높을수록 원본 이미지 무시"
            else:
                # Text-to-Image 모드
                processing_msg = "⚡ Stability AI로 이미지 생성 중... (최대 45초)\\n✨ 고품질 이미지를 빠르게 생성합니다!"
            
            await interaction.response.send_message(processing_msg, ephemeral=True)

            # Stability AI 이미지 생성
            result = await generate_stability_image(설명, 이미지, 강도)
            
            if isinstance(result, bytes):
                # 성공적으로 생성된 경우 (ephemeral)
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
                
                await interaction.followup.send(embed=embed, file=file, ephemeral=True)
            else:
                # 에러 메시지인 경우 (ephemeral)
                await interaction.followup.send(f"❌ {result}", ephemeral=True)
                
        except Exception as e:
            print(f"Stability AI command error: {e}")
            await interaction.followup.send("이미지 생성 중 오류가 발생했습니다.", ephemeral=True)
