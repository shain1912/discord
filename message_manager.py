import asyncio
from datetime import datetime, timedelta
from typing import Dict, Tuple, Optional, Callable, Any
import logging
from dotenv import load_dotenv
import os
from dataclasses import dataclass
from enum import Enum

load_dotenv()

logger = logging.getLogger(__name__)
CHAT_DAILY_LIMIT = int(os.getenv("CHAT_DAILY_LIMIT"))
IMAGE_DAILY_LIMIT = int(os.getenv("IMAGE_DAILY_LIMIT"))
VIDEO_DAILY_LIMIT = int(os.getenv("VIDEO_DAILY_LIMIT"))
CHAT_COOLDOWN = int(os.getenv("CHAT_COOLDOWN"))
IMAGE_COOLDOWN = int(os.getenv("IMAGE_COOLDOWN"))
VIDEO_COOLDOWN = int(os.getenv("VIDEO_COOLDOWN"))

class RequestType(Enum):
    CHAT = "chat"
    IMAGE = "image"
    VIDEO = "video"

@dataclass
class QueuedRequest:
    user_id: int
    request_type: RequestType
    handler: Callable
    args: tuple
    kwargs: dict
    created_at: datetime
    priority: int = 1  # 1=highest, 5=lowest

class EnhancedRequestManager:
    """향상된 요청 관리자 - 큐 시스템과 동시성 제어"""
    
    def __init__(self):
        # 기존 기능
        self.user_cooldowns: Dict[int, Dict[str, datetime]] = {}
        self.user_daily_counts: Dict[int, Dict[str, int]] = {}
        self.user_daily_reset: Dict[int, datetime] = {}
        self.lock = asyncio.Lock()
        
        # 새로운 큐 시스템
        self.request_queues: Dict[RequestType, asyncio.Queue] = {
            RequestType.CHAT: asyncio.Queue(maxsize=100),
            RequestType.IMAGE: asyncio.Queue(maxsize=50),
            RequestType.VIDEO: asyncio.Queue(maxsize=20)
        }
        
        # 동시성 제어
        self.concurrency_limits = {
            RequestType.CHAT: asyncio.Semaphore(10),    # 동시 10개 채팅
            RequestType.IMAGE: asyncio.Semaphore(5),    # 동시 5개 이미지
            RequestType.VIDEO: asyncio.Semaphore(2)     # 동시 2개 비디오
        }
        
        # 작업자 태스크들
        self.worker_tasks: Dict[RequestType, list] = {
            RequestType.CHAT: [],
            RequestType.IMAGE: [],
            RequestType.VIDEO: []
        }
        
        # 레이트 리미트 설정
        self.rate_limits = {
            'chat': {'cooldown': CHAT_COOLDOWN, 'daily_limit': CHAT_DAILY_LIMIT},
            'image': {'cooldown': IMAGE_COOLDOWN, 'daily_limit': IMAGE_DAILY_LIMIT},
            'video': {'cooldown': VIDEO_COOLDOWN, 'daily_limit': VIDEO_DAILY_LIMIT}
        }
        
        # 통계
        self.stats = {
            'processed': 0,
            'failed': 0,
            'queue_sizes': {},
            'active_workers': 0
        }

    async def can_make_request(self, user_id: int, request_type: str) -> Tuple[bool, str]:
        """사용자가 요청을 할 수 있는지 확인 (기존 로직 유지)"""
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

    async def queue_request(self, user_id: int, request_type: RequestType, 
                          handler: Callable, *args, **kwargs) -> bool:
        """요청을 큐에 추가"""
        try:
            request = QueuedRequest(
                user_id=user_id,
                request_type=request_type,
                handler=handler,
                args=args,
                kwargs=kwargs,
                created_at=datetime.now()
            )
            
            # 큐에 추가 (논블로킹)
            queue = self.request_queues[request_type]
            if queue.full():
                logger.warning(f"Queue for {request_type.value} is full, dropping request")
                return False
            
            await queue.put(request)
            logger.info(f"Queued {request_type.value} request for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to queue request: {e}")
            return False

    async def _process_queue_worker(self, request_type: RequestType, worker_id: int):
        """큐 처리 작업자"""
        queue = self.request_queues[request_type]
        semaphore = self.concurrency_limits[request_type]
        
        logger.info(f"Started {request_type.value} worker {worker_id}")
        
        while True:
            try:
                # 큐에서 요청 가져오기
                request = await queue.get()
                
                # 동시성 제어
                async with semaphore:
                    self.stats['active_workers'] += 1
                    try:
                        # 요청 처리
                        await request.handler(*request.args, **request.kwargs)
                        self.stats['processed'] += 1
                        
                    except Exception as e:
                        logger.error(f"Request processing failed: {e}")
                        self.stats['failed'] += 1
                        
                    finally:
                        self.stats['active_workers'] -= 1
                        queue.task_done()
                        
            except asyncio.CancelledError:
                logger.info(f"{request_type.value} worker {worker_id} cancelled")
                break
            except Exception as e:
                logger.error(f"Worker error: {e}")
                await asyncio.sleep(1)

    def start_queue_processor(self, bot) -> None:
        """큐 프로세서 시작 - 각 타입별로 여러 작업자 생성"""
        worker_counts = {
            RequestType.CHAT: 3,    # 채팅 작업자 3개
            RequestType.IMAGE: 2,   # 이미지 작업자 2개  
            RequestType.VIDEO: 1    # 비디오 작업자 1개
        }
        
        for request_type, count in worker_counts.items():
            for i in range(count):
                task = asyncio.create_task(
                    self._process_queue_worker(request_type, i + 1)
                )
                self.worker_tasks[request_type].append(task)
        
        # 통계 수집 태스크
        asyncio.create_task(self._stats_collector())
        
        logger.info("Enhanced queue processor started with multiple workers")

    async def _stats_collector(self):
        """통계 수집"""
        while True:
            try:
                # 큐 크기 업데이트
                for req_type, queue in self.request_queues.items():
                    self.stats['queue_sizes'][req_type.value] = queue.qsize()
                
                # 1분마다 통계 로그
                if self.stats['processed'] % 10 == 0:
                    logger.info(f"Stats: {self.stats}")
                
                await asyncio.sleep(30)  # 30초마다 수집
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Stats collector error: {e}")

    async def stop_queue_processor(self) -> None:
        """큐 프로세서 중지"""
        logger.info("Stopping queue processor...")
        
        # 모든 작업자 태스크 취소
        for request_type, tasks in self.worker_tasks.items():
            for task in tasks:
                task.cancel()
            
            # 취소 완료 대기
            await asyncio.gather(*tasks, return_exceptions=True)
            
        logger.info("Queue processor stopped")

    async def get_queue_stats(self) -> Dict[str, Any]:
        """큐 통계 반환"""
        return {
            'queue_sizes': {req_type.value: queue.qsize() 
                          for req_type, queue in self.request_queues.items()},
            'processed_total': self.stats['processed'],
            'failed_total': self.stats['failed'],
            'active_workers': self.stats['active_workers'],
            'concurrency_limits': {req_type.value: sem._value 
                                 for req_type, sem in self.concurrency_limits.items()}
        }

    async def get_user_stats(self, user_id: int) -> Dict[str, any]:
        """사용자 통계 정보 반환 (기존 로직 유지)"""
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

# 하위 호환성을 위한 별칭
RequestManager = EnhancedRequestManager
