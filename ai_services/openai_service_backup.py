import os
import asyncio
import discord
from dotenv import load_dotenv
from openai import AsyncOpenAI
import logging

logger = logging.getLogger(__name__)

# 환경 변수 로드
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    print("⚠️ OPENAI_API_KEY가 환경변수에 설정되지 않았습니다.")

# 비동기 OpenAI 클라이언트 초기화
openai_client = AsyncOpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

async def get_gpt_response_streaming(bot, prompt: str, interaction) -> None:
    """스트리밍 방식으로 GPT 응답 생성 (하나의 메시지를 계속 수정)"""
    if not openai_client:
        await interaction.followup.send("OpenAI API 키가 설정되지 않았습니다.", ephemeral=True)
        return
    
    try:
        # 프롬프트 최적화: 도움이 되고 상세한 응답 요청
        optimized_prompt = f"""
다음 질문에 도움이 되고 상세한 답변을 해주세요. 필요하다면 예시나 설명도 포함해주세요.

질문: {prompt}
        """
        
        stream = await openai_client.chat.completions.create(
            model="gpt-4o-mini",  # 빠른 모델 사용
            messages=[
                {"role": "system", "content": "당신은 도움이 되고 친근한 AI 어시스턴트입니다. 사용자의 질문에 상세하고 유용한 답변을 제공합니다."},
                {"role": "user", "content": optimized_prompt}
            ],
            max_tokens=1500,  # 토큰 수 증가
            temperature=0.7,
            stream=True,
            timeout=25  # 타임아웃 증가
        )
        
        content = ""
        message = None
        last_update = 0
        
        async for chunk in stream:
            if chunk.choices[0].delta.content:
                content += chunk.choices[0].delta.content
                
                # 300자마다 또는 처음 텍스트가 들어왔을 때 메시지 업데이트
                if message is None:
                    # 처음 메시지 전송 (일반 메시지로 변경)
                    display_content = content if len(content) <= 2000 else content[:1950] + "\\n\\n**[계속 입력 중...]**"
                    message = await interaction.followup.send(f"🤖 **ChatGPT 응답:**\\n\\n{display_content}")
                    last_update = len(content)
                    
                elif len(content) - last_update >= 300:  # 300자마다 업데이트
                    last_update = len(content)
                    try:
                        # 기존 메시지 수정
                        display_content = content if len(content) <= 2000 else content[:1950] + "\\n\\n**[계속 입력 중...]**"
                        await message.edit(content=f"🤖 **ChatGPT 응답:**\\n\\n{display_content}")
                    except discord.errors.HTTPException:
                        # 수정 실패시 무시하고 계속
                        pass
        
        # 최종 메시지 수정
        if message is not None:
            try:
                if len(content) <= 2000:
                    # 전체 내용이 2000자 이하인 경우
                    await message.edit(content=f"🤖 **ChatGPT 응답:**\\n\\n{content}")
                else:
                    # 2000자 초과인 경우 첫 번째 부분만 수정하고 나머지는 새 메시지로
                    await message.edit(content=f"🤖 **ChatGPT 응답:**\\n\\n{content[:1950]}\\n\\n**[계속 ⬇️]**")
                    
                    # 나머지 내용을 새 메시지들로 전송
                    remaining = content[1950:]
                    chunk_num = 2
                    while remaining:
                        chunk = remaining[:1950]
                        remaining = remaining[1950:]
                        if remaining:  # 아직 더 있다면
                            await interaction.followup.send(f"**[계속 {chunk_num}]**\\n\\n{chunk}\\n\\n**[계속 ⬇️]**")
                        else:  # 마지막 청크
                            await interaction.followup.send(f"**[계속 {chunk_num}]**\\n\\n{chunk}")
                        chunk_num += 1
                        
            except discord.errors.HTTPException:
                # 수정 실패시 새 메시지로 전송
                await interaction.followup.send(f"**[최종 응답]**\\n\\n{content[:2000]}")
        else:
            # message가 None인 경우 (매우 짧은 응답)
            await interaction.followup.send(f"🤖 **ChatGPT 응답:**\\n\\n{content}")
                
    except asyncio.TimeoutError:
        await interaction.followup.send("⏰ 응답 생성 시간이 초과되었습니다. 다시 시도해주세요.", ephemeral=True)
    except Exception as e:
        print(f"Streaming GPT error: {e}")
        await interaction.followup.send("응답 생성 중 오류가 발생했습니다.", ephemeral=True)
