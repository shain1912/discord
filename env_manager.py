"""
로드 밸런싱 기반 다중 인스턴스 환경 변수 관리

모든 인스턴스가 모든 기능을 처리하되, 사용자 기반으로 분산 처리
진짜 4배 성능 향상을 위한 API 키 분산 활용
"""

import os
from typing import Optional, Dict, List
from dotenv import load_dotenv
import logging

# 환경 변수 로드 여부 추적
_ENV_LOADED = False

# 환경 변수 캐시
_ENV_CACHE = {}

def init_environment(force_reload: bool = False) -> None:
    """환경 변수 초기화 - 로드 밸런싱 방식"""
    global _ENV_LOADED, _ENV_CACHE
    
    if _ENV_LOADED and not force_reload:
        return
    
    # .env 파일 로드
    if os.path.exists('.env'):
        load_dotenv()
        logging.info("Loaded environment variables from .env file (local development)")
    elif os.path.exists('.env.multi'):
        load_dotenv('.env.multi')
        logging.info("Loaded environment variables from .env.multi file (load balancing)")
    else:
        logging.info("Using system environment variables (production/docker)")
    
    # 인스턴스 설정
    instance_id = os.getenv('INSTANCE_ID', '1')
    
    # 주요 환경 변수들을 캐시에 저장
    _ENV_CACHE = {
        # 공통 설정
        'DISCORD_TOKEN': os.getenv('DISCORD_TOKEN'),
        'INSTANCE_ID': instance_id,
        'INSTANCE_TYPE': 'loadbalancer',  # 모든 인스턴스가 로드밸런서
        'ENABLED_COMMANDS': 'all',  # 모든 인스턴스가 모든 기능
        'TOTAL_INSTANCES': int(os.getenv('TOTAL_INSTANCES', '4')),
        
        # 인스턴스별 API 키들
        'OPENAI_API_KEY': os.getenv(f'OPENAI_API_KEY_{instance_id}'),
        'MINIMAX_API_KEY': os.getenv(f'MINIMAX_API_KEY_{instance_id}'), 
        'STABILITY_API_KEY': os.getenv(f'STABILITY_API_KEY_{instance_id}'),
        
        # 로드 밸런싱 설정
        'LOAD_BALANCING_STRATEGY': os.getenv('LOAD_BALANCING_STRATEGY', 'user_based'),  # user_based, random, channel_based
        'FAILOVER_ENABLED': os.getenv('FAILOVER_ENABLED', 'true'),
        'HEALTH_CHECK_INTERVAL': int(os.getenv('HEALTH_CHECK_INTERVAL', '30')),
        
        # 성능 최적화 설정 (로드 밸런싱으로 낮은 쿨다운)
        'CHAT_DAILY_LIMIT': int(os.getenv('CHAT_DAILY_LIMIT', '10000')),  # 인스턴스당 높은 한계
        'IMAGE_DAILY_LIMIT': int(os.getenv('IMAGE_DAILY_LIMIT', '800')),   # 인스턴스당 높은 한계
        'VIDEO_DAILY_LIMIT': int(os.getenv('VIDEO_DAILY_LIMIT', '160')),   # 인스턴스당 높은 한계
        'CHAT_COOLDOWN': int(os.getenv('CHAT_COOLDOWN', '0')),           # 쿨다운 없음 (분산 처리)
        'IMAGE_COOLDOWN': int(os.getenv('IMAGE_COOLDOWN', '0')),          # 쿨다운 없음
        'VIDEO_COOLDOWN': int(os.getenv('VIDEO_COOLDOWN', '2')),          # 최소 쿨다운
        
        # 로그 설정
        'LOG_LEVEL': os.getenv('LOG_LEVEL', 'INFO'),
        'LOG_FILE': f"logs/instance_{instance_id}.log"
    }
    
    _ENV_LOADED = True
    logging.info(f"Load balancing environment initialized for Instance {instance_id}")

def get_env(key: str, default: Optional[str] = None) -> Optional[str]:
    """환경 변수 값 조회 (캐시된 값 사용)"""
    if not _ENV_LOADED:
        init_environment()
    
    return _ENV_CACHE.get(key, default)

def get_env_int(key: str, default: int = 0) -> int:
    """정수형 환경 변수 값 조회"""
    value = get_env(key)
    if value is None:
        return default
    
    try:
        return int(value)
    except (ValueError, TypeError):
        logging.warning(f"Invalid integer value for {key}: {value}, using default: {default}")
        return default

def get_env_bool(key: str, default: bool = False) -> bool:
    """불린형 환경 변수 값 조회"""
    value = get_env(key)
    if value is None:
        return default
    
    return value.lower() in ('true', '1', 'yes', 'on')

def get_instance_config() -> Dict[str, any]:
    """인스턴스별 설정 반환 (로드 밸런싱)"""
    if not _ENV_LOADED:
        init_environment()
        
    return {
        'instance_id': get_env('INSTANCE_ID', '1'),
        'instance_type': 'loadbalancer',
        'enabled_commands': ['all'],  # 모든 기능 활성화
        'total_instances': get_env_int('TOTAL_INSTANCES', 4),
        'load_balancing_strategy': get_env('LOAD_BALANCING_STRATEGY', 'user_based'),
        'failover_enabled': get_env_bool('FAILOVER_ENABLED', True),
        'log_file': get_env('LOG_FILE')
    }

def get_assigned_instance(user_id: int, total_instances: int = None) -> int:
    """사용자 ID 기반으로 담당 인스턴스 결정"""
    if total_instances is None:
        total_instances = get_env_int('TOTAL_INSTANCES', 4)
    
    strategy = get_env('LOAD_BALANCING_STRATEGY', 'user_based')
    
    if strategy == 'user_based':
        # 사용자 ID 기반 분산 (일관성 보장)
        return (user_id % total_instances) + 1
    elif strategy == 'random':
        # 랜덤 분산 (매번 다름)
        import random
        random.seed(user_id)  # 동일 사용자는 동일한 랜덤 시드
        return random.randint(1, total_instances)
    else:
        # 기본: 사용자 기반
        return (user_id % total_instances) + 1

def get_assigned_instance_by_channel(channel_id: int, total_instances: int = None) -> int:
    """채널 ID 기반으로 담당 인스턴스 결정"""
    if total_instances is None:
        total_instances = get_env_int('TOTAL_INSTANCES', 4)
    
    return (channel_id % total_instances) + 1

def should_handle_command(interaction, instance_config: Dict) -> bool:
    """이 인스턴스가 해당 요청을 처리해야 하는지 판단 (로드 밸런싱)"""
    current_instance = int(instance_config['instance_id'])
    total_instances = instance_config['total_instances']
    strategy = instance_config['load_balancing_strategy']
    
    if strategy == 'channel_based':
        # 채널 기반 분산
        assigned_instance = get_assigned_instance_by_channel(interaction.channel.id, total_instances)
    else:
        # 사용자 기반 분산 (기본)
        assigned_instance = get_assigned_instance(interaction.user.id, total_instances)
    
    # 기본: 할당된 인스턴스가 처리
    return assigned_instance == current_instance

def get_next_available_instance(current_instance: int, total_instances: int = None) -> int:
    """장애 복구를 위한 다음 인스턴스 반환"""
    if total_instances is None:
        total_instances = get_env_int('TOTAL_INSTANCES', 4)
    
    # 다음 인스턴스로 순환
    return (current_instance % total_instances) + 1

def get_api_keys_for_instance(instance_id: str = None) -> Dict[str, str]:
    """인스턴스별 API 키 반환"""
    if instance_id is None:
        instance_id = get_env('INSTANCE_ID', '1')
    
    return {
        'openai': os.getenv(f'OPENAI_API_KEY_{instance_id}'),
        'minimax': os.getenv(f'MINIMAX_API_KEY_{instance_id}'),
        'stability': os.getenv(f'STABILITY_API_KEY_{instance_id}')
    }

def validate_required_env() -> List[str]:
    """자신의 인스턴스에 해당하는 필수 환경 변수만 검사"""
    missing_vars = []

    # Discord 토큰은 필수
    if not get_env('DISCORD_TOKEN'):
        missing_vars.append('DISCORD_TOKEN')

    # 현재 인스턴스의 ID
    instance_id = get_env('INSTANCE_ID', '1')

    # 해당 인스턴스의 API 키만 검사
    api_keys = get_api_keys_for_instance(instance_id)

    if not api_keys['openai']:
        missing_vars.append(f'OPENAI_API_KEY_{instance_id}')
    if not api_keys['minimax']:
        missing_vars.append(f'MINIMAX_API_KEY_{instance_id}')
    if not api_keys['stability']:
        missing_vars.append(f'STABILITY_API_KEY_{instance_id}')

    return missing_vars


def get_environment_info() -> Dict[str, any]:
    """환경 정보 조회 (로드 밸런싱 정보 포함)"""
    missing_vars = validate_required_env()
    instance_config = get_instance_config()
    
    return {
        'env_loaded': _ENV_LOADED,
        'docker_env': not os.path.exists('.env') and not os.path.exists('.env.multi'),
        'has_env_file': os.path.exists('.env'),
        'has_multi_env_file': os.path.exists('.env.multi'),
        'missing_required_vars': missing_vars,
        'config_vars_count': len(_ENV_CACHE),
        'instance_config': instance_config,
        'load_balancing_strategy': get_env('LOAD_BALANCING_STRATEGY'),
        'total_instances': get_env_int('TOTAL_INSTANCES'),
        'log_level': get_env('LOG_LEVEL')
    }

def get_load_balancing_info() -> Dict[str, any]:
    """로드 밸런싱 정보 반환"""
    return {
        'strategy': get_env('LOAD_BALANCING_STRATEGY', 'user_based'),
        'total_instances': get_env_int('TOTAL_INSTANCES', 4),
        'current_instance': get_env('INSTANCE_ID', '1'),
        'failover_enabled': get_env_bool('FAILOVER_ENABLED', True),
        'performance_multiplier': get_env_int('TOTAL_INSTANCES', 4),  # 성능 배수
    }

# 하위 호환성을 위한 개별 함수들
def get_discord_token() -> Optional[str]:
    return get_env('DISCORD_TOKEN')

def get_openai_key() -> Optional[str]:
    return get_env('OPENAI_API_KEY')

def get_minimax_key() -> Optional[str]:
    return get_env('MINIMAX_API_KEY')

def get_stability_key() -> Optional[str]:
    return get_env('STABILITY_API_KEY')
