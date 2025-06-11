import os
import json
import asyncio
import aiohttp
from typing import Optional
from dotenv import load_dotenv
from openai import AsyncOpenAI
import logging
import discord

logger = logging.getLogger(__name__)

# 환경 변수 로드
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MINIMAX_API_KEY = os.getenv("MINIMAX_API_KEY")
STABILITY_API_KEY = os.getenv("STABILITY_API_KEY")

if not OPENAI_API_KEY:
    print("⚠️ OPENAI_API_KEY가 환경변수에 설정되지 않았습니다.")
if not MINIMAX_API_KEY:
    print("⚠️ MINIMAX_API_KEY가 환경변수에 설정되지 않았습니다.")
if not STABILITY_API_KEY:
    print("⚠️ STABILITY_API_KEY가 환경변수에 설정되지 않았습니다.")

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
                    display_content = content if len(content) <= 2000 else content[:1950] + "\n\n**[계속 입력 중...]**"
                    message = await interaction.followup.send(f"🤖 **ChatGPT 응답:**\n\n{display_content}")
                    last_update = len(content)
                    
                elif len(content) - last_update >= 300:  # 300자마다 업데이트
                    last_update = len(content)
                    try:
                        # 기존 메시지 수정
                        display_content = content if len(content) <= 2000 else content[:1950] + "\n\n**[계속 입력 중...]**"
                        await message.edit(content=f"🤖 **ChatGPT 응답:**\n\n{display_content}")
                    except discord.errors.HTTPException:
                        # 수정 실패시 무시하고 계속
                        pass
        
        # 최종 메시지 수정
        if message is not None:
            try:
                if len(content) <= 2000:
                    # 전체 내용이 2000자 이하인 경우
                    await message.edit(content=f"🤖 **ChatGPT 응답:**\n\n{content}")
                else:
                    # 2000자 초과인 경우 첫 번째 부분만 수정하고 나머지는 새 메시지로
                    await message.edit(content=f"🤖 **ChatGPT 응답:**\n\n{content[:1950]}\n\n**[계속 ⬇️]**")
                    
                    # 나머지 내용을 새 메시지들로 전송
                    remaining = content[1950:]
                    chunk_num = 2
                    while remaining:
                        chunk = remaining[:1950]
                        remaining = remaining[1950:]
                        if remaining:  # 아직 더 있다면
                            await interaction.followup.send(f"**[계속 {chunk_num}]**\n\n{chunk}\n\n**[계속 ⬇️]**")
                        else:  # 마지막 청크
                            await interaction.followup.send(f"**[계속 {chunk_num}]**\n\n{chunk}")
                        chunk_num += 1
                        
            except discord.errors.HTTPException:
                # 수정 실패시 새 메시지로 전송
                await interaction.followup.send(f"**[최종 응답]**\n\n{content[:2000]}")
        else:
            # message가 None인 경우 (매우 짧은 응답)
            await interaction.followup.send(f"🤖 **ChatGPT 응답:**\n\n{content}")
                
    except asyncio.TimeoutError:
        await interaction.followup.send("⏰ 응답 생성 시간이 초과되었습니다. 다시 시도해주세요.", ephemeral=True)
    except Exception as e:
        print(f"Streaming GPT error: {e}")
        await interaction.followup.send("응답 생성 중 오류가 발생했습니다.", ephemeral=True)

async def generate_image(bot, prompt: str, image_attachment=None) -> str:
    """최적화된 이미지 생성 - MiniMax subject_reference 지원"""
    if not MINIMAX_API_KEY:
        return "MiniMax API 키가 설정되지 않았습니다."
    
    if not prompt:
        return "이미지 설명을 입력해주세요."
    
    # 프롬프트 최적화 (너무 길면 자르기)
    if len(prompt) > 500:
        prompt = prompt[:500] + "..."
        print(f"Prompt truncated to 500 characters for faster processing")
    
    try:
        url = "https://api.minimaxi.chat/v1/image_generation"
        
        # 페이로드 기본 구성
        payload = {
            "model": "image-01",
            "aspect_ratio": "1:1",
            "response_format": "url",
            "n": 1,
            "prompt_optimizer": False,  # 빠른 처리를 위해 비활성화
            "prompt": prompt
        }
        
        # 이미지 첫부가 있는 경우 subject_reference 사용
        if image_attachment:
            import base64
            
            # 이미지 데이터를 base64로 인코딩
            image_data = await image_attachment.read()
            
            # MIME 타입 확인
            content_type = image_attachment.content_type
            if content_type not in ['image/jpeg', 'image/jpg', 'image/png']:
                return "❌ 지원되지 않는 이미지 형식입니다. (JPG, JPEG, PNG만 지원)"
            
            # base64 인코딩
            base64_image = base64.b64encode(image_data).decode('utf-8')
            
            # MIME 타입에 따라 데이터 URI 생성
            if content_type == 'image/png':
                image_uri = f"data:image/png;base64,{base64_image}"
            else:  # JPEG/JPG
                image_uri = f"data:image/jpeg;base64,{base64_image}"
            
            # subject_reference 추가
            payload["subject_reference"] = [{
                "type": "character",
                "image_file": image_uri
            }]
            
            print(f"Using subject_reference with character reference")
        
        headers = {
            'Authorization': f'Bearer {MINIMAX_API_KEY}',
            'Content-Type': 'application/json'
        }
        
        print(f"Starting MiniMax image generation... (timeout: 60s)")
        
        # 타임아웃 증가 및 재시도 메커니즘
        for attempt in range(3):  # 3번 재시도
            try:
                async with aiohttp.ClientSession(
                    timeout=aiohttp.ClientTimeout(
                        total=60,  # 전체 타임아웃 60초로 증가
                        connect=10,  # 연결 타임아웃 10초
                        sock_read=30  # 속켓 읽기 타임아웃 30초
                    )
                ) as session:
                    async with session.post(url, headers=headers, data=json.dumps(payload)) as response:
                        
                        if response.status == 200:
                            result = await response.json()
                            if 'data' in result and 'image_urls' in result['data']:
                                image_urls = result['data']['image_urls']
                                if image_urls and len(image_urls) > 0:
                                    print(f"MiniMax image generated successfully on attempt {attempt + 1}")
                                    return image_urls[0]
                            return "이미지 URL을 찾을 수 없습니다."
                        
                        elif response.status == 429:  # Rate limit
                            print(f"Rate limit hit, waiting {(attempt + 1) * 2} seconds...")
                            await asyncio.sleep((attempt + 1) * 2)
                            continue
                        
                        else:
                            error_text = await response.text()
                            print(f"MiniMax API error {response.status}: {error_text}")
                            if attempt == 2:  # 마지막 시도
                                return f"이미지 생성 API 오류 (상태 코드: {response.status})"
                            
            except asyncio.TimeoutError:
                print(f"Timeout on attempt {attempt + 1}/3")
                if attempt == 2:  # 마지막 시도
                    return "⏰ 이미지 생성 시간이 초과되었습니다. \n\n해결법:\n- 더 간단한 설명으로 다시 시도해주세요\n- 잠시 후 다시 시도해주세요"
                await asyncio.sleep(2)  # 2초 대기 후 재시도
                continue
            
            except Exception as e:
                print(f"Attempt {attempt + 1} failed: {e}")
                if attempt == 2:
                    return f"이미지 생성 중 오류가 발생했습니다: {str(e)}"
                await asyncio.sleep(1)
                continue
                
    except Exception as e:
        print(f"Image generation error: {e}")
        return f"이미지 생성 중 오류가 발생했습니다: {str(e)}"

async def generate_video(prompt: str) -> str:
    """MiniMax API를 사용하여 비디오 생성"""
    if not MINIMAX_API_KEY:
        return "MiniMax API 키가 설정되지 않았습니다."
    
    if not prompt:
        return "비디오 설명을 입력해주세요."
    
    # 프롬프트 최적화
    if len(prompt) > 1000:
        prompt = prompt[:1000] + "..."
        print(f"Video prompt truncated to 1000 characters")
    
    try:
        print(f"Starting video generation... (timeout: 300s)")
        
        # 1단계: 비디오 생성 작업 제출
        task_id = await _submit_video_task(prompt)
        
        print(f"Video generation task submitted: {task_id}")
        
        # 2단계: 작업 완료까지 대기 (최대 5분)
        max_wait_time = 300  # 5분
        wait_interval = 15   # 15초마다 확인
        max_attempts = max_wait_time // wait_interval
        
        for attempt in range(max_attempts):
            await asyncio.sleep(wait_interval)
            
            file_id, status = await _query_video_status(task_id)
            
            if status == "Success" and file_id:
                # 3단계: 완성된 비디오 다운로드 URL 획득
                download_url = await _get_video_download_url(file_id)
                if download_url.startswith("http"):
                    return download_url
                else:
                    return download_url  # 에러 메시지
            
            elif status == "Fail":
                return "❌ 비디오 생성에 실패했습니다. 다른 설명으로 다시 시도해주세요."
            
            elif status == "Unknown":
                return "❌ 알 수 없는 오류가 발생했습니다."
            
            # 진행 상황 로그
            if attempt % 4 == 0:  # 1분마다 로그
                print(f"Video generation status: {status} (attempt {attempt + 1}/{max_attempts})")
        
        return "⏰ 비디오 생성 시간이 초과되었습니다. 비디오 생성에는 최대 5분이 소요될 수 있습니다."
        
    except Exception as e:
        print(f"Video generation error: {e}")
        return f"비디오 생성 중 오류가 발생했습니다: {str(e)}"

async def _submit_video_task(prompt: str) -> str:
    """비디오 생성 작업 제출"""
    url = "https://api.minimax.io/v1/video_generation"
    
    payload = {
        "prompt": prompt,
        "model": "T2V-01"
    }
    
    headers = {
        'Authorization': f'Bearer {MINIMAX_API_KEY}',
        'Content-Type': 'application/json'
    }
    
    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30)) as session:
        async with session.post(url, headers=headers, data=json.dumps(payload)) as response:
            print("responseStatus:", response.status)
            if response.status == 200:
                result = await response.json()
                if 'task_id' in result:
                    return result['task_id']
                else:
                    return "task_id를 찾을 수 없습니다."
            else:
                error_text = await response.text()
                print(f"Video task submission error {response.status}: {error_text}")
                
                if response.status == 400:
                    return "❌ 잘못된 요청입니다. 비디오 설명을 확인해주세요."
                elif response.status == 401:
                    return "❌ API 키가 잘못되었습니다."
                elif response.status == 402:
                    return "❌ 크레딧이 부족합니다."
                elif response.status == 429:
                    return "❌ 너무 많은 요청입니다. 잠시 후 다시 시도해주세요."
                else:
                    return f"❌ 비디오 생성 요청 실패 (코드: {response.status})"

async def _query_video_status(task_id: str) -> tuple[str, str]:
    """비디오 생성 상태 확인"""
    url = f"https://api.minimax.io/v1/query/video_generation?task_id={task_id}"
    
    headers = {
        'Authorization': f'Bearer {MINIMAX_API_KEY}'
    }
    
    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=15)) as session:
            async with session.get(url, headers=headers) as response:
                
                if response.status == 200:
                    result = await response.json()
                    status = result.get('status', 'Unknown')
                    file_id = result.get('file_id', '')
                    
                    return file_id, status
                else:
                    return "", "Unknown"
                    
    except Exception as e:
        print(f"Video status query error: {e}")
        return "", "Unknown"

async def _get_video_download_url(file_id: str) -> str:
    """비디오 다운로드 URL 획득"""
    url = f"https://api.minimax.io/v1/files/retrieve?file_id={file_id}"
    
    headers = {
        'Authorization': f'Bearer {MINIMAX_API_KEY}'
    }
    
    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=15)) as session:
            async with session.get(url, headers=headers) as response:
                
                if response.status == 200:
                    result = await response.json()
                    if 'file' in result and 'download_url' in result['file']:
                        return result['file']['download_url']
                    else:
                        return "다운로드 URL을 찾을 수 없습니다."
                else:
                    error_text = await response.text()
                    print(f"Video download URL error {response.status}: {error_text}")
                    return f"다운로드 URL 획득 실패 (코드: {response.status})"
                    
    except Exception as e:
        print(f"Video download URL error: {e}")
        return f"다운로드 URL 획득 중 오류: {str(e)}"

async def generate_stability_image(prompt: str, image_attachment=None, strength: float = 0.7) -> bytes:
    """Stability AI 이미지 생성 (text-to-image 또는 image-to-image)"""
    if not STABILITY_API_KEY:
        return "API 키가 없습니다."
    
    try:
        # image-to-image 모드인지 확인
        url = "https://api.stability.ai/v2beta/stable-image/generate/sd3"
        if image_attachment:
            mode = "image-to-image"
            print(f"Starting Stability AI image-to-image generation with strength {strength}...")
        else:
            mode = "text-to-image"
            print(f"Starting Stability AI text-to-image generation...")
        
        headers = {
            "authorization": f"Bearer {STABILITY_API_KEY}",
            "accept": "image/*"
        }

        form_data = aiohttp.FormData()
        form_data.add_field("prompt", prompt)
        form_data.add_field("model", "sd3.5-large-turbo")
        form_data.add_field("output_format", "png")
        
        # image-to-image 모드 설정
        if image_attachment:
            form_data.add_field("mode", "image-to-image")
            form_data.add_field("strength", str(strength))
            
            # 이미지 파일 추가
            image_data = await image_attachment.read()
            form_data.add_field(
                "image", 
                image_data, 
                filename=image_attachment.filename,
                content_type=image_attachment.content_type
            )
        else:
            # text-to-image 모드용 설정
            form_data.add_field("aspect_ratio", "1:1")
            form_data.add_field("none", "", filename="dummy.txt", content_type="text/plain")

        async with aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=45)  # image-to-image는 조금 더 시간이 걸릴 수 있음
        ) as session:
            async with session.post(
                url, headers=headers, data=form_data
            ) as response:
                if response.status == 200:
                    image_data = await response.read()
                    print(f"Stability AI {mode} generation successful ({len(image_data)} bytes)")
                    return image_data
                else:
                    error_text = await response.text()
                    print(f"Stability AI error {response.status}: {error_text}")
                    
                    # 상세한 에러 메시지
                    if response.status == 400:
                        return "❌ 잘못된 요청입니다. 프롬프트나 이미지를 확인해주세요."
                    elif response.status == 401:
                        return "❌ API 키가 잘못되었습니다."
                    elif response.status == 402:
                        return "❌ 크레딧이 부족합니다."
                    elif response.status == 403:
                        return "❌ 액세스가 거부되었습니다."
                    elif response.status == 413:
                        return "❌ 이미지 파일이 너무 큽니다. (최대 4MB)"
                    elif response.status == 415:
                        return "❌ 지원되지 않는 이미지 형식입니다. (PNG, JPEG, WebP만 지원)"
                    elif response.status == 429:
                        return "❌ 너무 많은 요청입니다. 잠시 후 다시 시도해주세요."
                    else:
                        return f"❌ Stability AI 오류 (코드: {response.status})"

    except asyncio.TimeoutError:
        print("Stability AI timeout")
        return "⏰ 이미지 생성 시간이 초과되었습니다. 다시 시도해주세요."
    except Exception as e:
        print(f"Stability AI error: {e}")
        return f"이미지 생성 중 오류가 발생했습니다: {str(e)}"
