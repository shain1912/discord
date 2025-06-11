import os
import asyncio
import discord
from dotenv import load_dotenv
from openai import AsyncOpenAI
import logging
from message_manager import message_manager

logger = logging.getLogger(__name__)

# 환경 변수 로드
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    print("⚠️ OPENAI_API_KEY가 환경변수에 설정되지 않았습니다.")

# 비동기 OpenAI 클라이언트 초기화
openai_client = AsyncOpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

async def get_gpt_response_streaming(bot, prompt: str, interaction) -> None:
    """향상된 스트리밍 GPT 응답 (큐 시스템 적용)"""
    if not openai_client:
        await message_manager.safe_followup_send(
            interaction, 
            "OpenAI API 키가 설정되지 않았습니다.", 
            ephemeral=True
        )
        return
    
    try:
        # 프롬프트 최적화
        optimized_prompt = f\"\"\"
다음 질문에 도움이 되고 상세한 답변을 해주세요. 필요하다면 예시나 설명도 포함해주세요.

질문: {prompt}
        \"\"\"
        
        # OpenAI 스트림 생성
        stream = await openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "당신은 도움이 되고 친근한 AI 어시스턴트입니다. 사용자의 질문에 상세하고 유용한 답변을 제공합니다."},
                {"role": "user", "content": optimized_prompt}
            ],
            max_tokens=1500,
            temperature=0.7,
            stream=True,
            timeout=30  # 타임아웃 연장
        )
        
        # 스트리밍 처리를 메시지 매니저에 위임
        async def content_generator():
            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        
        await message_manager.streaming_response_handler(
            interaction, 
            content_generator(),
            "🤖 **ChatGPT 응답:**\\n\\n"
        )
                
    except asyncio.TimeoutError:
        await message_manager.safe_followup_send(
            interaction,
            "⏰ 응답 생성 시간이 초과되었습니다. 다시 시도해주세요.", 
            ephemeral=True
        )
    except Exception as e:
        logger.error(f"Streaming GPT error: {e}")
        await message_manager.safe_followup_send(
            interaction,
            "응답 생성 중 오류가 발생했습니다.", 
            ephemeral=True
        )

# 큐 시스템 통합을 위한 래퍼 함수
async def queue_gpt_request(bot, prompt: str, interaction):
    """GPT 요청을 큐에 추가"""
    from request_manager_enhanced import RequestType
    
    success = await bot.request_manager.queue_request(
        user_id=interaction.user.id,
        request_type=RequestType.CHAT,
        handler=get_gpt_response_streaming,
        bot=bot,
        prompt=prompt,
        interaction=interaction
    )
    
    if not success:
        await message_manager.safe_followup_send(
            interaction,
            "⚠️ 서버가 바쁩니다. 잠시 후 다시 시도해주세요.",
            ephemeral=True
        )
