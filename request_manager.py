import asyncio
from datetime import datetime, timedelta
from typing import Dict, Tuple, Optional, Callable, Any
import logging
from env_manager import get_env_int

logger = logging.getLogger(__name__)

# 환경 변수에서 설정값 로드 (캐시된 값 사용)
CHAT_DAILY_LIMIT = get_env_int("CHAT_DAILY_LIMIT", 1000)
IMAGE_DAILY_LIMIT = get_env_int("IMAGE_DAILY_LIMIT", 50)
VIDEO_DAILY_LIMIT = get_env_int("VIDEO_DAILY_LIMIT", 10)
CHAT_COOLDOWN = get_env_int("CHAT_COOLDOWN", 3)
IMAGE_COOLDOWN = get_env_int("IMAGE_COOLDOWN", 3)
VIDEO_COOLDOWN = get_env_int("VIDEO_COOLDOWN", 10)

class RequestManager:
    """향상된 요청 관리자 - Docker 최적화"""
    
    def __init__(self):
        # 기존 기능
        self.user_cooldowns: Dict[int, Dict[str, datetime]] = {}
        self.user_daily_counts: Dict[int, Dict[str, int]] = {}
        self.user_daily_reset: Dict[int, datetime] = {}
        self.lock = asyncio.Lock()
        
        # 레이트 리미트 설정 (환경 변수에서 로드)
        self.rate_limits = {
            'chat': {'cooldown': CHAT_COOLDOWN, 'daily_limit': CHAT_DAILY_LIMIT},
            'image': {'cooldown': IMAGE_COOLDOWN, 'daily_limit': IMAGE_DAILY_LIMIT},
            'video': {'cooldown': VIDEO_COOLDOWN, 'daily_limit': VIDEO_DAILY_LIMIT}
        }
        
        logger.info(f"RequestManager initialized with limits: {self.rate_limits}")

    async def can_make_request(self, user_id: int, request_type: str) -> Tuple[bool, str]:
        """사용자가 요청을 할 수 있는지 확인"""
        async with self.lock:
            current_time = datetime.now()
            
            # 사용자 데이터 초기화
            if user_id not in self.user_cooldowns:
                self.user_cooldowns[user_id] = {}
                self.user_daily_counts[user_id] = {}
                self.user_daily_reset[user_id] = current_time
            
            # 일일 제한 초기화 확인 (24시간마다)
            if current_time - self.user_daily_reset[user_id] > timedelta(days=1):
                self.user_daily_counts[user_id] = {}
                self.user_daily_reset[user_id] = current_time
            
            # 일일 제한 확인
            daily_count = self.user_daily_counts[user_id].get(request_type, 0)
            if daily_count >= self.rate_limits[request_type]['daily_limit']:
                return False, "일일 사용 제한에 도달했습니다. 내일 다시 시도해주세요."
            
            # 쿨다운 확인
            last_request = self.user_cooldowns[user_id].get(request_type)
            if last_request:
                time_diff = (current_time - last_request).total_seconds()
                cooldown = self.rate_limits[request_type]['cooldown']
                if time_diff < cooldown:
                    remaining = cooldown - int(time_diff)
                    return False, f"재사용까지 {remaining}초 남았습니다."
            
            # 요청 허용 및 정보 업데이트
            self.user_cooldowns[user_id][request_type] = current_time
            self.user_daily_counts[user_id][request_type] = daily_count + 1
            return True, ""

    async def get_user_stats(self, user_id: int) -> Dict[str, any]:
        """사용자 통계 정보 반환"""
        if user_id not in self.user_daily_counts:
            return {"message": "사용자 데이터가 없습니다."}
        
        stats = {}
        for request_type, limit_info in self.rate_limits.items():
            used = self.user_daily_counts[user_id].get(request_type, 0)
            remaining = limit_info['daily_limit'] - used
            stats[request_type] = {
                "daily_used": used,
                "daily_remaining": remaining,
                "daily_limit": limit_info['daily_limit']
            }
        
        return stats
