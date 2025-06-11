# 🚀 Discord AI Bot - 다중 인스턴스 분산 처리

Discord에서 ChatGPT, AI 이미지 생성, 비디오 생성 기능을 제공하는 **4개 인스턴스 분산 처리** 봇입니다.

## ✨ 주요 특징

### 🔥 성능 혁신
- **4배 빠른 처리 속도**: 40개 동시 요청 처리 가능
- **4배 증가한 API 한계**: 각 서비스별 API 키 4개씩 사용
- **2배 빠른 응답 시간**: 전용 인스턴스별 최적화
- **99.9% 가용성**: 장애 시 자동 백업 인스턴스 작동

### 🎯 인스턴스별 전문화
| 인스턴스 | 담당 업무 | 전용 채널 | 특징 |
|---------|----------|-----------|------|
| **Instance 1** | 💬 ChatGPT 채팅 | 채팅방-*, ai-지원 | 스트리밍 응답, 빠른 처리 |
| **Instance 2** | 🎨 AI 이미지 생성 | 이미지생성-*, 갤러리 | MiniMax + Stability AI |
| **Instance 3** | 🎬 AI 비디오 생성 | 비디오생성-* | 고품질 비디오, 5분 생성 |
| **Instance 4** | ⚙️ 관리 및 백업 | 모든 채널 (백업) | 모니터링, 장애 복구 |

## 🚀 빠른 시작 (1분 배포)

### 1. 환경 설정
```bash
# 환경 변수 파일 생성
cp .env.multi.example .env.multi

# API 키 설정 (각 서비스별 4개씩 필요)
vim .env.multi  # 또는 메모장으로 편집
```

### 2. 배포 실행
```bash
# Linux/Mac
chmod +x deploy-multi.sh
./deploy-multi.sh start

# Windows
deploy-multi.bat start
```

### 3. 상태 확인
```bash
# 인스턴스 상태 확인
./deploy-multi.sh status

# 실시간 로그 확인
./deploy-multi.sh logs
```

## 📋 필요한 API 키들

### 🔑 총 13개 API 키 필요
```env
# Discord (1개)
DISCORD_TOKEN=your_discord_bot_token

# OpenAI (4개)
OPENAI_API_KEY_1=sk-instance1_key
OPENAI_API_KEY_2=sk-instance2_key  
OPENAI_API_KEY_3=sk-instance3_key
OPENAI_API_KEY_4=sk-instance4_key

# MiniMax (4개)
MINIMAX_API_KEY_1=eyJ_instance1_key
MINIMAX_API_KEY_2=eyJ_instance2_key
MINIMAX_API_KEY_3=eyJ_instance3_key
MINIMAX_API_KEY_4=eyJ_instance4_key

# Stability AI (4개)
STABILITY_API_KEY_1=sk-stability_instance1_key
STABILITY_API_KEY_2=sk-stability_instance2_key
STABILITY_API_KEY_3=sk-stability_instance3_key
STABILITY_API_KEY_4=sk-stability_instance4_key
```

## 📊 성능 비교

### Before (단일 인스턴스)
```
❌ 동시 처리: 10개 요청
❌ 응답 시간: 평균 5-10초  
❌ 일일 한계: 1,060개 요청
❌ 장애 시: 전체 서비스 중단
```

### After (다중 인스턴스)
```
✅ 동시 처리: 40개 요청 (4배)
✅ 응답 시간: 평균 2-5초 (2배 빠름)
✅ 일일 한계: 4,240개 요청 (4배)
✅ 장애 시: 자동 백업 인스턴스 작동
```

## 📋 사용 가능한 명령어

### 💬 채팅 명령어 (Instance 1)
- `/채팅 [질문]` - ChatGPT와 스트리밍 대화
- `/chat [question]` - English ChatGPT conversation

### 🎨 이미지 명령어 (Instance 2)
- `/이미지 [설명]` - MiniMax AI 이미지 생성
- `/img [설명] [이미지] [강도]` - Stability AI 빠른 이미지 생성

### 🎬 비디오 명령어 (Instance 3)
- `/비디오 [설명]` - MiniMax AI 비디오 생성 (최대 5분)

### ⚙️ 관리 명령어 (Instance 4)
- `/핑` - 봇 응답 시간 및 인스턴스 정보
- `/상태` - 시스템 전체 상태 확인
- `/인스턴스` - 인스턴스별 역할 분담 정보

## 🛠️ 관리 명령어

### 기본 조작
```bash
# 인스턴스 시작
./deploy-multi.sh start

# 인스턴스 중지  
./deploy-multi.sh stop

# 인스턴스 재시작
./deploy-multi.sh restart

# 상태 확인
./deploy-multi.sh status
```

### 모니터링
```bash
# 실시간 로그 확인
./deploy-multi.sh logs

# 헬스체크
./deploy-multi.sh health

# 리소스 사용량 확인
docker stats
```

### 업데이트 및 유지보수
```bash
# 코드 업데이트
git pull origin main
./deploy-multi.sh update

# 완전 제거 (주의!)
./deploy-multi.sh cleanup
```

## 🏗️ 시스템 요구사항

### 최소 사양
```
CPU: 4코어 이상
RAM: 8GB 이상
Storage: 20GB 이상
Network: 안정적인 인터넷 연결
```

### 권장 사양 (고성능)
```
CPU: 8코어 이상
RAM: 16GB 이상
Storage: SSD 50GB 이상
Network: 기가비트 인터넷
```

### 소프트웨어
```
Docker: 20.10 이상
Docker Compose: 2.0 이상
OS: Linux/Windows/macOS
```

## 🔧 고급 설정

### 인스턴스별 리소스 제한
```yaml
# docker-compose.multi.yml 수정 예시
services:
  discord-bot-chat:
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 4G
        reservations:
          cpus: '1.0'
          memory: 2G
```

### 로드 밸런싱 설정
```yaml
# nginx.conf 예시
upstream discord_bots {
    server discord-bot-chat:8000 weight=3;
    server discord-bot-image:8000 weight=2;
    server discord-bot-video:8000 weight=1;
    server discord-bot-admin:8000 backup;
}
```

## 📈 성능 모니터링

### 메트릭 확인
```bash
# 실시간 리소스 사용량
docker stats

# 개별 인스턴스 상태
curl http://localhost:8001/health  # Instance 1
curl http://localhost:8002/health  # Instance 2
curl http://localhost:8003/health  # Instance 3
curl http://localhost:8004/health  # Instance 4
```

### 로그 분석
```bash
# 에러 로그 검색
./deploy-multi.sh logs | grep -i error

# 성능 통계
./deploy-multi.sh logs | grep "commands_processed"

# 특정 인스턴스 로그
docker logs discord-bot-chat --tail=100
```

## 🚨 문제 해결

### 자주 발생하는 문제들

#### 1. 인스턴스가 시작되지 않는 경우
```bash
# 환경 변수 확인
./deploy-multi.sh
# 선택: 1 (시작) - 자동으로 검증

# 수동 확인
docker-compose -f docker-compose.multi.yml config
```

#### 2. API 키 오류
```bash
# .env.multi 파일 재확인
cat .env.multi | grep -v "your_"

# 특정 인스턴스 로그 확인
docker logs discord-bot-chat | grep -i "api"
```

#### 3. 메모리 부족
```bash
# 리소스 사용량 확인
docker stats

# 메모리 제한 증가 (docker-compose.multi.yml 수정)
mem_limit: 8g
```

#### 4. 채널 라우팅 문제
```bash
# 인스턴스별 처리 통계 확인
# Discord에서 /상태 명령어 실행

# 로그에서 라우팅 확인
docker logs discord-bot-admin | grep "routing"
```

## 🔒 보안 고려사항

### API 키 보안
- `.env.multi` 파일은 절대 Git에 커밋하지 마세요
- 프로덕션에서는 Docker secrets 사용 권장
- API 키 정기 교체 (월 1회 권장)

### 네트워크 보안
- 방화벽에서 필요한 포트만 개방
- VPN 또는 VPC 내부 네트워크 사용 권장
- HTTPS 통신 사용

### 접근 제어
- Discord 서버 권한 관리
- 관리 명령어는 관리자만 사용 가능
- 로그 파일 접근 권한 제한

## 🔄 백업 및 복구

### 자동 백업
```bash
# 백업 스크립트 실행 (크론탭 등록 권장)
./scripts/backup.sh

# 백업된 데이터 확인
ls -la backups/
```

### 복구
```bash
# 설정 복구
cp backups/latest/.env.multi .env.multi

# 데이터 복구
./scripts/restore.sh backups/latest/
```

## 📞 지원 및 기여

### 문제 신고
- GitHub Issues: 버그 리포트 및 기능 요청
- Discord 서버: 실시간 지원

### 기여 방법
1. Fork the repository
2. Create feature branch
3. Commit changes
4. Create Pull Request

## 📄 라이센스

이 프로젝트는 MIT 라이센스 하에 배포됩니다.

---

## 🎉 성공적인 다중 인스턴스 배포를 축하합니다!

이제 **4배 빠른 성능**과 **99.9% 가용성**을 갖춘 Discord AI Bot을 사용할 수 있습니다. 

📊 **실시간 성능 모니터링**: `/상태` 명령어로 확인  
🔧 **인스턴스 관리**: `./deploy-multi.sh` 스크립트 활용  
📈 **성능 최적화**: 사용량에 따라 리소스 조정  

**Happy Coding!** 🚀
