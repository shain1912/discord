# 🚀 Discord AI Bot 다중 인스턴스 분산처리 가이드

Discord AI Bot을 4개 인스턴스로 분산 처리하기 위한 완전한 가이드입니다.

## 📋 사전 준비사항

### 1. 🔑 API 키 준비 (각 서비스별 4개씩)

#### OpenAI API Keys
```
OPENAI_API_KEY_1=sk-...instance1
OPENAI_API_KEY_2=sk-...instance2  
OPENAI_API_KEY_3=sk-...instance3
OPENAI_API_KEY_4=sk-...instance4
```

#### MiniMax API Keys
```
MINIMAX_API_KEY_1=eyJ...instance1
MINIMAX_API_KEY_2=eyJ...instance2
MINIMAX_API_KEY_3=eyJ...instance3
MINIMAX_API_KEY_4=eyJ...instance4
```

#### Stability AI API Keys
```
STABILITY_API_KEY_1=sk-...instance1
STABILITY_API_KEY_2=sk-...instance2
STABILITY_API_KEY_3=sk-...instance3
STABILITY_API_KEY_4=sk-...instance4
```

#### Discord Bot Token (공통)
```
DISCORD_TOKEN=MTI...  # 모든 인스턴스가 같은 봇 토큰 사용
```

### 2. 🏗️ 인프라 준비

#### 서버 옵션
```
Option A: 단일 서버 (Docker Compose)
├── CPU: 8코어 이상
├── RAM: 16GB 이상  
├── Network: 안정적인 인터넷 연결

Option B: 클라우드 분산 (권장)
├── AWS/GCP/Azure 인스턴스 4개
├── 각각: 2코어, 4GB RAM
├── Load Balancer 설정 (선택사항)
```

## 🎯 인스턴스별 채널 분산 전략

### 전략 1: 기능별 분산 (권장)
```
Instance 1: 채팅 전용 (ChatGPT)
├── 📢 안내-공지 (모니터링)
├── 💭 채팅방-1,2,3,4,5
├── 🤖 ai-지원
└── ⚙️ 봇-상태

Instance 2: 이미지 생성 전용  
├── 🎨 이미지생성-1,2,3,4,5
├── 🖼️ 갤러리
├── 🔄 이미지변환
└── 📊 이미지-통계

Instance 3: 비디오 생성 전용
├── 🎬 비디오생성-1,2,3
├── 📹 비디오-갤러리  
├── ⏱️ 진행상황
└── 📈 비디오-통계

Instance 4: 관리 및 백업
├── 🔧 관리자-명령어
├── 📊 전체-통계
├── 🚨 알림-채널
└── 💾 백업-로그
```

### 전략 2: 서버별 분산
```
Instance 1: 서버 A, B 담당
Instance 2: 서버 C, D 담당  
Instance 3: 서버 E, F 담당
Instance 4: 오버플로우 + 관리
```

### 전략 3: 부하 기반 동적 분산
```
Instance 1-3: 자동 로드 밸런싱
Instance 4: 고가용성 백업
```

## 🐳 Docker Compose 다중 인스턴스 설정

### docker-compose.multi.yml
```yaml
version: '3.8'

services:
  # Instance 1: Chat Handler
  discord-bot-chat:
    build: .
    container_name: discord-bot-chat
    restart: unless-stopped
    environment:
      - DISCORD_TOKEN=${DISCORD_TOKEN}
      - OPENAI_API_KEY=${OPENAI_API_KEY_1}
      - MINIMAX_API_KEY=${MINIMAX_API_KEY_1}
      - STABILITY_API_KEY=${STABILITY_API_KEY_1}
      - INSTANCE_ID=1
      - INSTANCE_TYPE=chat
      - ENABLED_COMMANDS=chat,ping
      - LOG_LEVEL=INFO
    volumes:
      - ./logs/instance1:/app/logs
    
  # Instance 2: Image Handler  
  discord-bot-image:
    build: .
    container_name: discord-bot-image
    restart: unless-stopped
    environment:
      - DISCORD_TOKEN=${DISCORD_TOKEN}
      - OPENAI_API_KEY=${OPENAI_API_KEY_2}
      - MINIMAX_API_KEY=${MINIMAX_API_KEY_2}
      - STABILITY_API_KEY=${STABILITY_API_KEY_2}
      - INSTANCE_ID=2
      - INSTANCE_TYPE=image
      - ENABLED_COMMANDS=image,img
      - LOG_LEVEL=INFO
    volumes:
      - ./logs/instance2:/app/logs

  # Instance 3: Video Handler
  discord-bot-video:
    build: .
    container_name: discord-bot-video
    restart: unless-stopped
    environment:
      - DISCORD_TOKEN=${DISCORD_TOKEN}
      - OPENAI_API_KEY=${OPENAI_API_KEY_3}
      - MINIMAX_API_KEY=${MINIMAX_API_KEY_3}
      - STABILITY_API_KEY=${STABILITY_API_KEY_3}
      - INSTANCE_ID=3
      - INSTANCE_TYPE=video
      - ENABLED_COMMANDS=video
      - LOG_LEVEL=INFO
    volumes:
      - ./logs/instance3:/app/logs

  # Instance 4: Management & Backup
  discord-bot-admin:
    build: .
    container_name: discord-bot-admin
    restart: unless-stopped
    environment:
      - DISCORD_TOKEN=${DISCORD_TOKEN}
      - OPENAI_API_KEY=${OPENAI_API_KEY_4}
      - MINIMAX_API_KEY=${MINIMAX_API_KEY_4}
      - STABILITY_API_KEY=${STABILITY_API_KEY_4}
      - INSTANCE_ID=4
      - INSTANCE_TYPE=admin
      - ENABLED_COMMANDS=ping,stats,admin
      - LOG_LEVEL=DEBUG
    volumes:
      - ./logs/instance4:/app/logs
      - ./backups:/app/backups

# 공유 네트워크
networks:
  default:
    name: discord-bot-network

# 공유 볼륨
volumes:
  shared_logs:
  shared_data:
```

## ⚙️ 코드 수정사항

### 1. 환경 변수 확장 (env_manager.py)
```python
def get_instance_config():
    """인스턴스별 설정 반환"""
    return {
        'instance_id': get_env('INSTANCE_ID', '1'),
        'instance_type': get_env('INSTANCE_TYPE', 'all'),
        'enabled_commands': get_env('ENABLED_COMMANDS', 'all').split(','),
        'is_primary': get_env_bool('IS_PRIMARY', False)
    }

def get_api_keys_for_instance(instance_id: str):
    """인스턴스별 API 키 반환"""
    return {
        'openai': get_env(f'OPENAI_API_KEY_{instance_id}'),
        'minimax': get_env(f'MINIMAX_API_KEY_{instance_id}'), 
        'stability': get_env(f'STABILITY_API_KEY_{instance_id}')
    }
```

### 2. 조건부 명령어 로딩 (bot_class.py)
```python
async def setup_commands(self):
    """인스턴스 타입에 따른 조건부 명령어 설정"""
    instance_config = get_instance_config()
    enabled_commands = instance_config['enabled_commands']
    
    if 'chat' in enabled_commands or 'all' in enabled_commands:
        from commands.chat_commands import setup_chat_commands
        await setup_chat_commands(self)
        
    if 'image' in enabled_commands or 'all' in enabled_commands:
        from commands.image_commands import setup_image_commands
        await setup_image_commands(self)
        
    if 'video' in enabled_commands or 'all' in enabled_commands:
        from commands.video_commands import setup_video_commands
        await setup_video_commands(self)
        
    # 관리 명령어는 항상 로드
    from commands.utility_commands import setup_utility_commands
    await setup_utility_commands(self)
```

### 3. 채널별 라우팅 (channel_router.py)
```python
CHANNEL_ROUTES = {
    'chat': {
        'channels': ['채팅방-*', 'ai-지원', '안내-공지'],
        'instance_type': 'chat',
        'fallback_instances': ['admin']
    },
    'image': {
        'channels': ['이미지생성-*', '갤러리', '이미지변환'],
        'instance_type': 'image', 
        'fallback_instances': ['admin']
    },
    'video': {
        'channels': ['비디오생성-*', '비디오-갤러리'],
        'instance_type': 'video',
        'fallback_instances': ['admin']
    }
}

def should_handle_command(interaction, instance_config):
    """이 인스턴스가 해당 명령어를 처리해야 하는지 판단"""
    channel_name = interaction.channel.name
    instance_type = instance_config['instance_type']
    
    # 관리 인스턴스는 모든 채널 처리 가능
    if instance_type == 'admin':
        return True
        
    # 채널별 라우팅 확인
    for cmd_type, config in CHANNEL_ROUTES.items():
        if any(channel_match(channel_name, pattern) for pattern in config['channels']):
            return instance_type == config['instance_type']
    
    return False
```

## 🚨 주의사항 및 해결책

### 1. 동시성 문제
```python
# 문제: 여러 인스턴스가 같은 명령어에 응답
# 해결: 채널 기반 라우팅 + 인스턴스 타입 체크

@bot.tree.command(name="채팅")
async def chat(interaction: discord.Interaction, 질문: str):
    instance_config = get_instance_config()
    
    # 이 인스턴스가 처리해야 하는지 확인
    if not should_handle_command(interaction, instance_config):
        return  # 조용히 무시
        
    # 처리 로직...
```

### 2. 레이트 리미트 관리
```python
# 인스턴스별 독립적인 레이트 리미트
class DistributedRequestManager:
    def __init__(self, instance_id):
        self.instance_id = instance_id
        self.rate_limits = {
            'chat': {'cooldown': 1, 'daily_limit': 2500},  # 4배 증가
            'image': {'cooldown': 1, 'daily_limit': 200},  # 4배 증가
            'video': {'cooldown': 5, 'daily_limit': 40}    # 4배 증가
        }
```

### 3. 로그 및 모니터링
```python
# 인스턴스별 로그 구분
logging.basicConfig(
    filename=f'/app/logs/instance_{instance_id}.log',
    format=f'[Instance-{instance_id}] %(asctime)s - %(levelname)s - %(message)s'
)

# 중앙 모니터링을 위한 메트릭 전송
async def send_metrics():
    metrics = {
        'instance_id': instance_id,
        'processed_requests': stats['processed'],
        'active_users': len(active_users),
        'queue_sizes': get_queue_sizes()
    }
    # 중앙 모니터링 시스템으로 전송
```

### 4. 장애 복구 전략
```python
# Health Check 엔드포인트
@app.route('/health')
def health_check():
    return {
        'status': 'healthy',
        'instance_id': instance_id,
        'uptime': get_uptime(),
        'queue_sizes': get_queue_sizes()
    }

# 인스턴스 간 헬스체크
async def check_peer_instances():
    for peer_url in PEER_INSTANCES:
        try:
            response = await aiohttp.get(f"{peer_url}/health")
            # 다운된 인스턴스의 작업 인계
        except:
            await handle_peer_failure(peer_url)
```

## 📊 성능 최적화

### 1. 부하 분산 효과
```
기존 (단일 인스턴스):
├── 동시 처리: 10개 요청
├── 응답 시간: 평균 5-10초
└── 일일 한계: 1,060개 요청

최적화 (4개 인스턴스):
├── 동시 처리: 40개 요청 (4배)
├── 응답 시간: 평균 2-5초 (2배 빠름)
└── 일일 한계: 4,240개 요청 (4배)
```

### 2. API 키 분산 효과
```
각 서비스별 레이트 리미트 4배 증가:
├── OpenAI: 3,500 RPM → 14,000 RPM
├── MiniMax: 100 RPD → 400 RPD  
└── Stability: 100 RPM → 400 RPM
```

## 🚀 배포 명령어

### 환경 설정
```bash
# 1. 환경 변수 파일 생성
cp .env.multi.example .env.multi

# 2. API 키 설정 (각 4개씩)
vim .env.multi

# 3. 다중 인스턴스 실행
docker-compose -f docker-compose.multi.yml up -d

# 4. 상태 확인
docker-compose -f docker-compose.multi.yml ps
docker-compose -f docker-compose.multi.yml logs -f
```

### 모니터링
```bash
# 전체 로그 확인
tail -f logs/instance*/discord-bot.log

# 성능 모니터링
docker stats

# 개별 인스턴스 상태
curl http://localhost:8001/health  # Instance 1
curl http://localhost:8002/health  # Instance 2
curl http://localhost:8003/health  # Instance 3
curl http://localhost:8004/health  # Instance 4
```

## ⚠️ 핵심 주의사항

### 1. Discord API 레이트 리미트
- **같은 봇 토큰 사용 시 전역 레이트 리미트 공유**
- 명령어 응답은 한 인스턴스만 처리하도록 구현 필수

### 2. 데이터 일관성
- 사용자별 쿨다운은 Redis/DB로 중앙 관리 권장
- 파일 기반 상태는 각 인스턴스별 독립적 관리

### 3. 채널 충돌 방지  
- 명확한 채널 라우팅 규칙 필수
- 인스턴스별 담당 채널 명시

### 4. 장애 대응
- 인스턴스 다운 시 다른 인스턴스가 인계하는 로직
- 헬스체크 및 자동 복구 시스템

이 구성으로 **4배의 처리 성능**과 **높은 가용성**을 확보할 수 있습니다! 🚀
