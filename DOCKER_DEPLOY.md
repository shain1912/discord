# 🐳 Discord AI Bot - Docker 배포 가이드

Docker를 사용하여 Discord AI 봇을 배포하는 방법입니다.

## 📋 사전 준비

### 1. Docker 설치
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) 설치
- [Docker Compose](https://docs.docker.com/compose/install/) 설치

### 2. API 키 준비
다음 API 키들이 필요합니다:
- **Discord Bot Token** (필수)
- **OpenAI API Key** (필수)
- **MiniMax API Key** (필수)
- **Stability AI API Key** (필수)

## 🚀 배포 방법

### 방법 1: Docker Compose (추천)

1. **환경변수 파일 생성**
   ```bash
   cp .env.docker .env
   ```

2. **환경변수 설정**
   `.env` 파일을 열어서 실제 API 키들로 변경:
   ```env
   DISCORD_TOKEN=your_actual_discord_token
   OPENAI_API_KEY=your_actual_openai_key
   MINIMAX_API_KEY=your_actual_minimax_key
   STABILITY_API_KEY=your_actual_stability_key
   ```

3. **봇 실행**
   ```bash
   docker-compose up -d
   ```

4. **상태 확인**
   ```bash
   docker-compose logs -f
   ```

### 방법 2: Docker 단독 실행

1. **이미지 빌드**
   ```bash
   docker build -t discord-ai-bot .
   ```

2. **컨테이너 실행**
   ```bash
   docker run -d \\
     --name discord-ai-bot \\
     --restart unless-stopped \\
     -e DISCORD_TOKEN="your_token" \\
     -e OPENAI_API_KEY="your_openai_key" \\
     -e MINIMAX_API_KEY="your_minimax_key" \\
     -e STABILITY_API_KEY="your_stability_key" \\
     discord-ai-bot
   ```

## ⚙️ 환경변수 설정

### 필수 환경변수
```env
DISCORD_TOKEN=your_discord_bot_token
OPENAI_API_KEY=your_openai_api_key
MINIMAX_API_KEY=your_minimax_api_key
STABILITY_API_KEY=your_stability_api_key
```

### 선택적 환경변수
```env
# 쿨다운 시간 (초)
CHAT_COOLDOWN=3
IMAGE_COOLDOWN=3
VIDEO_COOLDOWN=10

# 일일 사용 제한
CHAT_DAILY_LIMIT=1000
IMAGE_DAILY_LIMIT=50
VIDEO_DAILY_LIMIT=10

# 로그 레벨
LOG_LEVEL=INFO
```

## 🔧 유용한 명령어

### 로그 확인
```bash
# 실시간 로그 보기
docker-compose logs -f

# 최근 로그만 보기
docker-compose logs --tail=100
```

### 봇 재시작
```bash
docker-compose restart
```

### 봇 중지
```bash
docker-compose down
```

### 봇 완전 제거
```bash
docker-compose down -v
docker rmi discord-ai-bot
```

### 컨테이너 상태 확인
```bash
docker-compose ps
```

## 🐛 문제 해결

### 봇이 시작되지 않는 경우
1. **환경변수 확인**
   ```bash
   docker-compose config
   ```

2. **로그 확인**
   ```bash
   docker-compose logs
   ```

3. **컨테이너 디버깅**
   ```bash
   docker-compose exec discord-bot bash
   ```

### 자주 발생하는 문제들

#### ❌ "DISCORD_TOKEN이 설정되지 않았습니다"
- `.env` 파일에 올바른 토큰이 설정되어 있는지 확인
- 환경변수 형식이 올바른지 확인

#### ❌ "API 키가 설정되지 않았습니다"
- 모든 필수 API 키가 `.env` 파일에 설정되어 있는지 확인
- API 키에 특수문자가 있는 경우 따옴표로 감싸기

#### ❌ 컨테이너가 계속 재시작됨
- 로그를 확인하여 에러 원인 파악
- 메모리 부족이 아닌지 확인

## 🔒 보안 주의사항

1. **환경변수 파일 보안**
   - `.env` 파일을 git에 커밋하지 마세요
   - 프로덕션 환경에서는 Docker secrets 사용 권장

2. **API 키 관리**
   - API 키는 절대 코드에 하드코딩하지 마세요
   - 정기적으로 API 키 교체 권장

3. **네트워크 보안**
   - 필요한 포트만 열어두기
   - 방화벽 설정 확인

## 📊 모니터링

### 시스템 리소스 확인
```bash
# CPU, 메모리 사용량 확인
docker stats discord-ai-bot

# 컨테이너 정보 확인
docker inspect discord-ai-bot
```

### 로그 로테이션 설정
```yaml
# docker-compose.yml에 추가
logging:
  driver: "json-file"
  options:
    max-size: "10m"
    max-file: "3"
```

## 🔄 업데이트 방법

1. **새 코드 받기**
   ```bash
   git pull origin main
   ```

2. **이미지 재빌드**
   ```bash
   docker-compose build --no-cache
   ```

3. **봇 재시작**
   ```bash
   docker-compose up -d
   ```

## 📈 스케일링

### 여러 인스턴스 실행
```bash
docker-compose up -d --scale discord-bot=3
```

### 로드 밸런서 사용
Docker Swarm이나 Kubernetes와 함께 사용하여 고가용성 확보

---

## 🆘 지원

문제가 발생하면 다음을 확인해주세요:
1. 로그 파일 확인
2. 환경변수 설정 재확인
3. Docker 및 네트워크 상태 확인
4. API 키 유효성 및 크레딧 잔액 확인
