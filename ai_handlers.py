from openai import OpenAI
import os
import discord
import asyncio
from dotenv import load_dotenv

# OpenAI 설정
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=OPENAI_API_KEY)

async def get_gpt_response(bot, prompt, message=None):
    try:    
        response = await bot.loop.run_in_executor(None, lambda: client.chat.completions.create(
            model="gpt-4.1-nano",  # GPT-4.1 nano 모델
            messages=[
                {"role": "user", "content": prompt}
            ],
            max_tokens=1000
        ))
        return response.choices[0].message.content
    except Exception as e:
        return f"오류가 발생했습니다: {str(e)}"

async def generate_image(bot, prompt, image_url=None, message=None):
    try:
        if image_url:
            # Image to Image 생성
            response = await bot.loop.run_in_executor(None, lambda: client.images.create_variation(
                image=download_image(image_url),
                model="dall-e-3",
                prompt=prompt,
                size="1024x1024",
                quality="standard",
                n=1
            ))
        else:
            # 일반 이미지 생성
            response = await bot.loop.run_in_executor(None, lambda: client.images.generate(
                model="dall-e-3",
                prompt=prompt,
                size="1024x1024",
                quality="standard",
                n=1
            ))
                
        return response.data[0].url
    except Exception as e:
        return f"이미지 생성 중 오류가 발생했습니다: {str(e)}"

async def download_image(url):
    """URL에서 이미지를 다운로드하고 바이트로 반환"""
    import aiohttp
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                return await response.read()
    except Exception as e:
        raise Exception(f"이미지 다운로드 중 오류 발생: {str(e)}")
