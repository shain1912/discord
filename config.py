from env_manager import init_environment, get_env, validate_required_env
from utils import setup_logging

def load_config():
    """환경 변수 및 설정 로드 - Docker 최적화"""
    # 환경 변수 초기화 (한 번만 실행)
    init_environment()
    
    # 로깅 설정
    log_level = get_env("LOG_LEVEL", "INFO")
    setup_logging(log_level)
    
    # 필수 환경 변수 검증
    missing_vars = validate_required_env()
    if missing_vars:
        missing_str = ", ".join(missing_vars)
        raise ValueError(f"❌ 다음 환경변수들이 설정되지 않았습니다: {missing_str}")
    
    # Discord 토큰 반환
    token = get_env("DISCORD_TOKEN")
    if not token:
        raise ValueError("❌ DISCORD_TOKEN이 환경변수에 설정되지 않았습니다.")
    
    return token
