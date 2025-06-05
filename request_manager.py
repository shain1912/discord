from asyncio import Queue, Lock
from datetime import datetime, timedelta

class RequestManager:
    def __init__(self):
        self.request_queue = Queue()
        self.user_cooldowns = {}
        self.lock = Lock()
        self.rate_limits = {
            'chat': {'cooldown': 1, 'daily_limit': 1000},
            'image': {'cooldown': 1, 'daily_limit': 50000}
        }
        
    async def can_make_request(self, user_id: int, request_type: str) -> tuple[bool, str]:
        async with self.lock:
            current_time = datetime.now()
            
            if user_id not in self.user_cooldowns:
                self.user_cooldowns[user_id] = {
                    'chat': {'last_request': None, 'daily_count': 0, 'daily_reset': current_time},
                    'image': {'last_request': None, 'daily_count': 0, 'daily_reset': current_time}
                }
            
            user_data = self.user_cooldowns[user_id][request_type]
            
            # 일일 제한 초기화
            if current_time - user_data['daily_reset'] > timedelta(days=1):
                user_data['daily_count'] = 0
                user_data['daily_reset'] = current_time
            
            # 일일 제한 확인
            if user_data['daily_count'] >= self.rate_limits[request_type]['daily_limit']:
                return False, f"일일 사용 한도({self.rate_limits[request_type]['daily_limit']}회)를 초과했습니다. 내일 다시 시도해주세요."
            
            # 쿨다운 확인
            if user_data['last_request'] and \
               current_time - user_data['last_request'] < timedelta(seconds=self.rate_limits[request_type]['cooldown']):
                remaining = self.rate_limits[request_type]['cooldown'] - \
                           (current_time - user_data['last_request']).seconds
                return False, f"재사용까지 {remaining}초 남았습니다."
            
            # 요청 허용 및 정보 업데이트
            user_data['last_request'] = current_time
            user_data['daily_count'] += 1
            return True, ""
