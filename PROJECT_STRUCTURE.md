# 📁 프로젝트 파일 구조 및 정리 가이드

Discord AI Bot 프로젝트의 파일 구조와 각 파일의 용도를 설명합니다.

## 🚀 배포용 파일들 (Production)

### 📦 메인 애플리케이션
```
├── server.py                    # 봇 엔트리 포인트
├── env_manager.py              # 환경 변수 통합 관리 (Docker 최적화)
├── config.py                   # 설정 로드 및 검증
├── utils.py                    # 공통 유틸리티 함수
├── channel_manager.py          # Discord 채널 자동 생성
├── message_manager.py          # 메시지 처리 유틸리티
├── request_manager_enhanced.py # Enhanced 요청 관리 (큐 시스템)
└── ai_handlers.py             # AI 서비스 통합 인터페이스
```

### 🤖 봇 모듈
```
bot/
├── __init__.py
├── bot_class.py               # 메인 봇 클래스 (Enhanced 버전)
└── events.py                  # 봇 이벤트 핸들러
```

### 🧠 AI 서비스
```
ai_services/
├── __init__.py
├── openai_service.py          # OpenAI ChatGPT 통합
├── minimax_service.py         # MiniMax 이미지/비디오 생성
└── stability_service.py       # Stability AI 이미지 생성
```

### ⚡ 명령어
```
commands/
├── __init__.py
├── chat_commands.py           # ChatGPT 채팅 명령어
├── image_commands.py          # 이미지 생성 명령어
├── video_commands.py          # 비디오 생성 명령어
└── utility_commands.py        # 유틸리티 명령어 (핑 등)
```

### 🐳 Docker 배포
```
├── Dockerfile                 # Docker 이미지 빌드
├── docker-compose.yml         # Docker Compose 설정
├── .dockerignore              # Docker 빌드 제외 파일
├── requirements.txt           # Python 의존성
└── DOCKER_DEPLOY.md          # Docker 배포 가이드
```

### 📄 문서 및 설정
```
├── README.md                  # 프로젝트 문서
├── .gitignore                # Git 제외 파일
├── .env.example              # 환경 변수 예시
└── .env.docker               # Docker 환경 변수 템플릿
```

## 🔧 개발 전용 파일들 (Development Only)

```
dev_only/
├── bot_class_simple.py        # 기본 RequestManager 사용 봇
├── request_manager.py         # 기본 요청 관리자 (큐 시스템 없음)
└── openai_service_enhanced.py # Enhanced 버전 OpenAI 서비스
```

## 📦 백업 파일들 (Backups)

```
backups/
├── ai_handlers_backup.py      # 기존 AI 핸들러
├── config_backup.py           # 기존 설정 파일
├── message_manager_backup.py  # 기존 메시지 매니저
├── request_manager_backup2.py # 기존 요청 매니저
├── server_backup.py           # 기존 서버 파일
└── old_versions/              # 이전 버전들
    ├── openai_service_backup.py
    ├── openai_service_backup2.py
    ├── minimax_service_backup2.py
    ├── stability_service_backup2.py
    ├── bot_class_backup.py
    ├── image_commands_backup.py
    └── video_commands_backup.py
```

## 🚫 배포에서 제외되는 파일들

### .gitignore로 제외
- `__pycache__/` - Python 캐시 파일
- `*.log` - 로그 파일
- `.env` - 환경 변수 파일 (보안)
- `backups/` - 백업 파일들
- `dev_only/` - 개발 전용 파일들

### .dockerignore로 제외
- `.git/` - Git 저장소
- `backups/` - 백업 파일들
- `dev_only/` - 개발 전용 파일들
- `*.log` - 로그 파일
- `.env` - 환경 변수 파일

## 🎯 사용 가이드

### 프로덕션 배포
```bash
# Docker 배포 (추천)
docker-compose up -d

# 로컬 실행
python server.py
```

### 개발 환경
```bash
# 기본 버전으로 테스트하려면
cp dev_only/bot_class_simple.py bot/bot_class.py
cp dev_only/request_manager.py ./

# Enhanced 버전으로 되돌리려면
git checkout bot/bot_class.py
```

## 📊 파일 의존성

### 핵심 의존성 체인
```
server.py
├── config.py
│   └── env_manager.py
├── bot/bot_class.py
│   ├── request_manager_enhanced.py
│   │   └── env_manager.py
│   └── commands/*.py
│       └── ai_services/*.py
│           └── env_manager.py
└── channel_manager.py
```

### 환경 변수 관리
- 모든 환경 변수는 `env_manager.py`를 통해 중앙 관리
- Docker 환경에서 최적화된 성능
- 한 번만 `load_dotenv()` 호출

## 🔄 업데이트 프로세스

### 1. 코드 변경 시
```bash
# 백업 생성
cp important_file.py backups/important_file_backup_$(date +%Y%m%d).py

# 코드 수정
# ...

# 테스트 후 배포
```

### 2. Docker 이미지 업데이트
```bash
docker-compose build --no-cache
docker-compose up -d
```

## ⚠️ 주의사항

1. **환경 변수 보안**
   - `.env` 파일은 절대 Git에 커밋하지 마세요
   - 프로덕션에서는 Docker secrets 사용 권장

2. **백업 파일**
   - `backups/` 디렉토리는 정기적으로 정리하세요
   - 중요한 변경 전에는 항상 백업 생성

3. **개발 파일**
   - `dev_only/` 파일들은 배포에 포함되지 않습니다
   - 테스트 목적으로만 사용하세요

---

**정리 완료!** 이제 프로젝트가 깔끔하게 정리되었고, 배포와 개발이 분리되었습니다. 🎉
