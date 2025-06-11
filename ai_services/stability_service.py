import os
import asyncio
import aiohttp
from dotenv import load_dotenv
import logging

logger = logging.getLogger(__name__)

# 환경 변수 로드
load_dotenv()
STABILITY_API_KEY = os.getenv("STABILITY_API_KEY")

if not STABILITY_API_KEY:
    print("⚠️ STABILITY_API_KEY가 환경변수에 설정되지 않았습니다.")

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
