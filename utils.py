import asyncio
import functools
from typing import Callable, Any, List
import logging

logger = logging.getLogger(__name__)

def async_retry(max_retries: int = 3, delay: float = 1.0, backoff: float = 2.0):
    """비동기 함수 재시도 데코레이터"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        wait_time = delay * (backoff ** attempt)
                        logger.warning(f"Attempt {attempt + 1} failed: {e}. Retrying in {wait_time}s...")
                        await asyncio.sleep(wait_time)
                    else:
                        logger.error(f"All {max_retries} attempts failed: {e}")
            
            raise last_exception
        
        return wrapper
    return decorator

def split_message(content: str, max_length: int = 2000) -> List[str]:
    """긴 메시지를 여러 청크로 분할"""
    if len(content) <= max_length:
        return [content]
    
    chunks = []
    current_chunk = ""
    
    # 줄바꿈을 기준으로 분할 시도
    lines = content.split('\n')
    
    for line in lines:
        if len(current_chunk) + len(line) + 1 <= max_length:
            current_chunk += line + '\n'
        else:
            if current_chunk:
                chunks.append(current_chunk.rstrip())
                current_chunk = line + '\n'
            else:
                # 한 줄이 너무 긴 경우 강제 분할
                while len(line) > max_length:
                    chunks.append(line[:max_length])
                    line = line[max_length:]
                current_chunk = line + '\n'
    
    if current_chunk:
        chunks.append(current_chunk.rstrip())
    
    return chunks

def sanitize_filename(filename: str) -> str:
    """파일명 정리"""
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    return filename[:255]  # 파일명 길이 제한

class RateLimiter:
    """간단한 레이트 리미터"""
    def __init__(self, max_calls: int, time_window: float):
        self.max_calls = max_calls
        self.time_window = time_window
        self.calls = []
    
    async def acquire(self) -> bool:
        """레이트 리미트 확인 및 획득"""
        now = asyncio.get_event_loop().time()
        
        # 시간 윈도우 밖의 호출 제거
        self.calls = [call_time for call_time in self.calls 
                     if now - call_time < self.time_window]
        
        if len(self.calls) < self.max_calls:
            self.calls.append(now)
            return True
        
        return False

def setup_logging(level: str = "INFO"):
    """로깅 설정"""
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # 기본 로깅 설정
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format=log_format,
        handlers=[
            logging.FileHandler('bot.log', encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    
    # Discord.py 로그 레벨 조정
    logging.getLogger('discord').setLevel(logging.WARNING)
    logging.getLogger('discord.http').setLevel(logging.WARNING)
