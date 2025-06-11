"""
환경 변수 통합 관리 모듈 - Docker 환경 최적화

Docker 컨테이너에서는 환경 변수가 이미 로드되어 있으므로 
load_dotenv()를 한 번만 호출하고 전역적으로 관리합니다.
"""

import os
from typing import Optional
from dotenv import load_dotenv
import logging

# 환경 변수 로드 여부 추적
_ENV_LOADED = False

# 환경 변수 캐시
_ENV_CACHE = {}

def init_environment(force_reload: bool = False) -> None:
    """
    환경 변수 초기화 - 애플리케이션 시작 시 한 번만 호출
    
    Args:
        force_reload: 강제로 다시 로드할지 여부
    """
    global _ENV_LOADED, _ENV_CACHE
    
    if _ENV_LOADED and not force_reload:
        return
    
    # .env 파일이 있는 경우에만 load_dotenv() 호출 (로컬 개발환경)
    if os.path.exists('.env'):
        load_dotenv()
        logging.info("Loaded environment variables from .env file (local development)")
    else:
        logging.info("Using system environment variables (production/docker)")
    
    # 주요 환경 변수들을 캐시에 저장
    _ENV_CACHE = {
        'DISCORD_TOKEN': os.getenv('DISCORD_TOKEN'),
        'OPENAI_API_KEY': os.getenv('OPENAI_API_KEY'),
        'MINIMAX_API_KEY': os.getenv('MINIMAX_API_KEY'),
        'STABILITY_API_KEY': os.getenv('STABILITY_API_KEY'),
        'CHAT_DAILY_LIMIT': int(os.getenv('CHAT_DAILY_LIMIT', '1000')),
        'IMAGE_DAILY_LIMIT': int(os.getenv('IMAGE_DAILY_LIMIT', '50')),
        'VIDEO_DAILY_LIMIT': int(os.getenv('VIDEO_DAILY_LIMIT', '10')),
        'CHAT_COOLDOWN': int(os.getenv('CHAT_COOLDOWN', '3')),
        'IMAGE_COOLDOWN': int(os.getenv('IMAGE_COOLDOWN', '3')),
        'VIDEO_COOLDOWN': int(os.getenv('VIDEO_COOLDOWN', '10')),
        'LOG_LEVEL': os.getenv('LOG_LEVEL', 'INFO')
    }
    
    _ENV_LOADED = True
    logging.info("Environment variables initialized successfully")

def get_env(key: str, default: Optional[str] = None) -> Optional[str]:
    """
    환경 변수 값 조회 (캐시된 값 사용)
    
    Args:
        key: 환경 변수 키
        default: 기본값
        
    Returns:
        환경 변수 값
    """
    if not _ENV_LOADED:
        init_environment()
    
    return _ENV_CACHE.get(key, default)

def get_env_int(key: str, default: int = 0) -> int:
    """
    정수형 환경 변수 값 조회
    
    Args:
        key: 환경 변수 키
        default: 기본값
        
    Returns:
        정수형 환경 변수 값
    """
    value = get_env(key)
    if value is None:
        return default
    
    try:
        return int(value)
    except (ValueError, TypeError):
        logging.warning(f"Invalid integer value for {key}: {value}, using default: {default}")
        return default

def get_env_bool(key: str, default: bool = False) -> bool:
    """
    불린형 환경 변수 값 조회
    
    Args:
        key: 환경 변수 키
        default: 기본값
        
    Returns:
        불린형 환경 변수 값
    """
    value = get_env(key)
    if value is None:
        return default
    
    return value.lower() in ('true', '1', 'yes', 'on')

def validate_required_env() -> list[str]:
    """
    필수 환경 변수 검증
    
    Returns:
        누락된 환경 변수 목록
    """
    required_vars = [
        'DISCORD_TOKEN',
        'OPENAI_API_KEY',
        'MINIMAX_API_KEY', 
        'STABILITY_API_KEY'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not get_env(var):
            missing_vars.append(var)
    
    return missing_vars

def get_environment_info() -> dict:
    """
    환경 정보 조회 (디버깅용)
    
    Returns:
        환경 정보 딕셔너리
    """
    missing_vars = validate_required_env()
    
    return {
        'env_loaded': _ENV_LOADED,
        'docker_env': not os.path.exists('.env'),
        'has_env_file': os.path.exists('.env'),
        'missing_required_vars': missing_vars,
        'config_vars_count': len(_ENV_CACHE),
        'log_level': get_env('LOG_LEVEL')
    }

# 하위 호환성을 위한 개별 변수들 (기존 코드가 계속 작동하도록)
def get_discord_token() -> Optional[str]:
    return get_env('DISCORD_TOKEN')

def get_openai_key() -> Optional[str]:
    return get_env('OPENAI_API_KEY')

def get_minimax_key() -> Optional[str]:
    return get_env('MINIMAX_API_KEY')

def get_stability_key() -> Optional[str]:
    return get_env('STABILITY_API_KEY')
