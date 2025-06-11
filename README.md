# Discord AI Bot - 심플 버전

Discord에서 ChatGPT와 AI 이미지 생성 기능을 제공하는 간단한 봇입니다.

## ✨ 주요 기능

- **💬 ChatGPT 대화**: OpenAI GPT-4를 사용한 자연스러운 대화
- **🎨 AI 이미지 생성**: MiniMax API를 사용한 이미지 생성 및 변환
- **📊 간단한 사용량 관리**: 레이트 리미팅 및 일일 사용량 제한
- **🔧 자동 채널 설정**: 봇 참가 시 자동으로 서비스 채널 생성

## 🛠️ 설치 및 설정

### 1. 요구사항

- Python 3.8 이상
- Discord Bot Token
- OpenAI API Key  
- MiniMax API Key
- Stability AI API Key

### 2. 의존성 설치

```bash
pip install -r requirements.txt
```

### 3. 환경 변수 설정

`.env` 파일을 생성하고 다음 내용을 입력하세요:

```env
DISCORD_TOKEN=your_discord_bot_token_here
OPENAI_API_KEY=your_openai_api_key_here
MINIMAX_API_KEY=your_minimax_api_key_here
STABILITY_API_KEY=your_stability_api_key_here
```

### 4. 봇 실행

```bash
python server.py
```

## 📋 사용 가능한 명령어

- `/채팅 [질문]` - ChatGPT와 대화 (스트리밍 방식)
- `/이미지 [설명/URL] [설명/URL]` - MiniMax AI 이미지 생성/변환
- `/img [설명] [이미지] [강도]` - Stability AI 빠른 이미지 생성/변환
- `/핑` - 봇 응답 시간 확인

## 🎨 이미지 명령어 사용법

### MiniMax AI (`/이미지`) - 다양한 기능

1. **텍스트로 이미지 생성**:
   ```
   /이미지 "고양이가 우주에서 피자를 먹는 모습"
   ```

2. **이미지 변환 (설명 + URL)**:
   ```
   /이미지 "만화 스타일로 변환" "https://example.com/image.jpg"
   ```

3. **URL 기반 변환**:
   ```
   /이미지 "https://example.com/image.jpg" "수채화 스타일"
   ```

### Stability AI (`/img`) - 빠르고 고품질 ⚡

1. **빠른 이미지 생성** (Text-to-Image):
   ```
   /img "마법의 숲에서 요정이 춤추는 모습"
   ```

2. **이미지 변환** (Image-to-Image):
   ```
   /img "만화 스타일로 변환" + 이미지 첫부
   ```

3. **강도 조절** (0.1-1.0):
   ```
   /img "수채화 그림" + 이미지 + 강도:0.3 (원본 유지)
   /img "완전히 다른 스타일" + 이미지 + 강도:0.9 (대폭 변환)
   ```

### 💡 **어떤 명령어를 선택할까?**

- **빠른 이미지 생성**: `/img` (Stability AI) 추천
- **이미지 변환**: `/img` + 이미지 첫부 (Image-to-Image)
- **이미지 편집**: `/이미지` (MiniMax) 추천
- **다양한 스타일**: 둘 다 시도해보세요!

## 📁 프로젝트 구조

```
discord/
├── server.py              # 메인 봇 파일
├── ai_handlers.py          # AI API 핸들러
├── request_manager.py      # 간단한 요청 관리
├── channel_manager.py      # 채널 자동 생성
├── utils.py               # 유틸리티 함수
├── requirements.txt       # 의존성 목록
├── .env                  # 환경 변수 (직접 생성)
└── README.md            # 프로젝트 문서
```

## ⚙️ 기본 설정

### 레이트 리미트
- **채팅**: 3초 쿨다운, 일일 1000회 제한
- **이미지**: 3초 쿨다운, 일일 50회 제한

### 자동 생성 채널
봇이 서버에 참가하면 자동으로 다음 채널들을 생성합니다:

- 📢 안내-공지 (읽기 전용)
- 💭 채팅방-1,2,3 (ChatGPT 대화용)
- 🎨 이미지생성-1,2,3 (이미지 생성용)

## 🐛 문제 해결

### 일반적인 문제

1. **봇이 시작되지 않는 경우**:
   - `.env` 파일의 토큰이 올바른지 확인
   - 모든 의존성이 설치되었는지 확인

2. **명령어가 작동하지 않는 경우**:
   - 봇에게 필요한 권한이 있는지 확인
   - 슬래시 명령어 동기화가 완료되었는지 확인

3. **MiniMax 이미지 생성이 실패하는 경우**:
   - MiniMax API 키가 유효한지 확인
   - 네트워크 연결 상태 확인
   - 대신 `/img` 명령어 사용 (Stability AI)

4. **Stability AI 이미지 생성이 실패하는 경우**:
   - Stability AI API 키가 유효한지 확인
   - 크레딧 잔액 확인
   - 대신 `/이미지` 명령어 사용 (MiniMax)

## 📝 라이센스

이 프로젝트는 개인용 및 교육용으로 자유롭게 사용할 수 있습니다.

## 🤝 기여

버그 리포트나 기능 개선 제안은 언제든 환영합니다!
