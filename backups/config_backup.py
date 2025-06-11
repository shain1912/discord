import os
from dotenv import load_dotenv
from utils import setup_logging

def load_config():
    """환경 변수 및 설정 로드"""
    # 환경 변수 로드
    load_dotenv()
    
    # 로깅 설정
    setup_logging("INFO")
    
    # 필수 환경 변수 확인
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        raise ValueError("❌ DISCORD_TOKEN이 환경변수에 설정되지 않았습니다.")
    
    return token
