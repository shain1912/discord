import asyncio
from datetime import datetime, timedelta
from typing import Dict, Tuple, Optional
import logging
from dotenv import load_dotenv
import os
load_dotenv()

logger = logging.getLogger(__name__)
CHAT_DAILY_LIMIT = int(os.getenv("CHAT_DAILY_LIMIT"))
IMAGE_DAILY_LIMIT = int(os.getenv("IMAGE_DAILY_LIMIT"))
VIDEO_DAILY_LIMIT = int(os.getenv("VIDEO_DAILY_LIMIT"))
CHAT_COOLDOWN= os.getenv("CHAT_COOLDOWN")
IMAGE_COOLDOWN= os.getenv("IMAGE_COOLDOWN")
VIDEO_COOLDOWN= os.getenv("VIDEO_COOLDOWN")
class RequestManager:
    """간단한 요청 관리자 클래스"""
    
    def __init__(self):
        self.user_cooldowns: Dict[int, Dict[str, datetime]] = {}
        self.user_daily_counts: Dict[int, Dict[str, int]] = {}
        self.user_daily_reset: Dict[int, datetime] = {}
        self.lock = asyncio.Lock()
        
        # 레이트 리미트 설정
        self.rate_limits = {
            'chat': {'cooldown': CHAT_COOLDOWN, 'daily_limit': CHAT_DAILY_LIMIT},
            'image': {'cooldown': IMAGE_COOLDOWN, 'daily_limit': IMAGE_DAILY_LIMIT},
            'video': {'cooldown': VIDEO_COOLDOWN, 'daily_limit': VIDEO_DAILY_LIMIT}
        }
        self.queue_processor_task: Optional[asyncio.Task] = None
        
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

    def start_queue_processor(self, bot) -> asyncio.Task:
        """큐 프로세서 시작 (현재는 사용하지 않음)"""
        print("Queue processor started (simplified version)")
        return asyncio.create_task(self._dummy_processor())
    
    async def _dummy_processor(self):
        """더미 프로세서"""
        while True:
            await asyncio.sleep(60)  # 1분마다 체크

    async def stop_queue_processor(self) -> None:
        """큐 프로세서 중지"""
        if self.queue_processor_task:
            self.queue_processor_task.cancel()
            try:
                await self.queue_processor_task
            except asyncio.CancelledError:
                pass
        print("Queue processor stopped")

    async def get_user_stats(self, user_id: int) -> Dict[str, any]:
        """사용자 통계 정보 반환 (간단 버전)"""
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
