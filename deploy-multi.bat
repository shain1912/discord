@echo off
setlocal enabledelayedexpansion

:: Discord AI Bot 다중 인스턴스 배포 스크립트 (Windows)
:: 사용법: deploy-multi.bat [start|stop|restart|status|logs]

title Discord AI Bot 다중 인스턴스 관리

:: 색상 코드 (Windows Terminal 지원)
set "RED=[31m"
set "GREEN=[32m"
set "YELLOW=[33m"
set "BLUE=[34m"
set "NC=[0m"

:: 로그 함수들
:log_info
echo %BLUE%[INFO]%NC% %~1
goto :eof

:log_success
echo %GREEN%[SUCCESS]%NC% %~1
goto :eof

:log_warning
echo %YELLOW%[WARNING]%NC% %~1
goto :eof

:log_error
echo %RED%[ERROR]%NC% %~1
goto :eof

:: 시스템 요구사항 확인
:check_requirements
call :log_info "시스템 요구사항 확인 중..."

:: Docker 확인
docker --version >nul 2>&1
if errorlevel 1 (
    call :log_error "Docker가 설치되지 않았습니다."
    pause
    exit /b 1
)

:: Docker Compose 확인
docker-compose --version >nul 2>&1
if errorlevel 1 (
    call :log_error "Docker Compose가 설치되지 않았습니다."
    pause
    exit /b 1
)

:: 환경 변수 파일 확인
if not exist ".env.multi" (
    call :log_warning ".env.multi 파일이 없습니다."
    if exist ".env.multi.example" (
        call :log_info ".env.multi.example을 복사하여 .env.multi를 생성합니다..."
        copy ".env.multi.example" ".env.multi" >nul
        call :log_warning ".env.multi 파일에 실제 API 키를 입력해주세요!"
        echo 파일 위치: %CD%\.env.multi
        pause
        exit /b 1
    ) else (
        call :log_error ".env.multi.example 파일도 없습니다."
        pause
        exit /b 1
    )
)

call :log_success "시스템 요구사항 확인 완료"
goto :eof

:: 환경 변수 검증
:validate_env
call :log_info "환경 변수 검증 중..."

:: .env.multi 파일에서 필수 변수 확인
findstr /C:"DISCORD_TOKEN=your_" .env.multi >nul
if not errorlevel 1 (
    call :log_error "DISCORD_TOKEN이 설정되지 않았습니다."
    pause
    exit /b 1
)

:: API 키들 확인
for %%i in (1 2 3 4) do (
    findstr /C:"OPENAI_API_KEY_%%i=your_" .env.multi >nul
    if not errorlevel 1 (
        call :log_error "OPENAI_API_KEY_%%i가 설정되지 않았습니다."
        pause
        exit /b 1
    )
)

call :log_success "환경 변수 검증 완료"
goto :eof

:: 디렉토리 생성
:create_directories
call :log_info "필요한 디렉토리 생성 중..."

if not exist "logs\instance1" mkdir "logs\instance1"
if not exist "logs\instance2" mkdir "logs\instance2"
if not exist "logs\instance3" mkdir "logs\instance3"
if not exist "logs\instance4" mkdir "logs\instance4"
if not exist "backups" mkdir "backups"
if not exist "data" mkdir "data"
if not exist "monitoring" mkdir "monitoring"

call :log_success "디렉토리 생성 완료"
goto :eof

:: 인스턴스 시작
:start_instances
call :log_info "다중 인스턴스 시작 중..."

docker-compose -f docker-compose.multi.yml --env-file .env.multi up -d

call :log_success "모든 인스턴스가 시작되었습니다!"

:: 시작 후 상태 확인
timeout /t 5 /nobreak >nul
call :show_status
goto :eof

:: 인스턴스 중지
:stop_instances
call :log_info "다중 인스턴스 중지 중..."

docker-compose -f docker-compose.multi.yml down

call :log_success "모든 인스턴스가 중지되었습니다."
goto :eof

:: 인스턴스 재시작
:restart_instances
call :log_info "다중 인스턴스 재시작 중..."

call :stop_instances
timeout /t 3 /nobreak >nul
call :start_instances
goto :eof

:: 상태 확인
:show_status
call :log_info "인스턴스 상태 확인 중..."

echo.
echo === Docker 컨테이너 상태 ===
docker-compose -f docker-compose.multi.yml ps

echo.
echo === 리소스 사용량 ===
docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}" discord-bot-chat discord-bot-image discord-bot-video discord-bot-admin 2>nul

echo.
echo === 헬스체크 상태 ===
for %%c in (discord-bot-chat discord-bot-image discord-bot-video discord-bot-admin) do (
    docker ps --filter "name=%%c" --filter "status=running" -q >nul 2>&1
    if not errorlevel 1 (
        echo %%c: running
    ) else (
        echo %%c: stopped
    )
)
goto :eof

:: 로그 보기
:show_logs
call :log_info "로그 확인 옵션:"
echo 1. 전체 로그 (실시간)
echo 2. 특정 인스턴스 로그
echo 3. 에러 로그만
echo 4. 최근 100줄

set /p choice="선택 (1-4): "

if "%choice%"=="1" (
    call :log_info "전체 로그 실시간 모니터링 (Ctrl+C로 종료)"
    docker-compose -f docker-compose.multi.yml logs -f
) else if "%choice%"=="2" (
    echo 인스턴스 선택:
    echo 1. Chat (Instance 1)
    echo 2. Image (Instance 2)
    echo 3. Video (Instance 3)
    echo 4. Admin (Instance 4)
    set /p instance_choice="선택 (1-4): "
    
    if "!instance_choice!"=="1" docker-compose -f docker-compose.multi.yml logs -f discord-bot-chat
    if "!instance_choice!"=="2" docker-compose -f docker-compose.multi.yml logs -f discord-bot-image
    if "!instance_choice!"=="3" docker-compose -f docker-compose.multi.yml logs -f discord-bot-video
    if "!instance_choice!"=="4" docker-compose -f docker-compose.multi.yml logs -f discord-bot-admin
) else if "%choice%"=="3" (
    call :log_info "에러 로그 검색 중..."
    docker-compose -f docker-compose.multi.yml logs | findstr /i error
) else if "%choice%"=="4" (
    call :log_info "최근 100줄 로그"
    docker-compose -f docker-compose.multi.yml logs --tail=100
) else (
    call :log_error "잘못된 선택입니다."
)
goto :eof

:: 업데이트
:update_instances
call :log_info "인스턴스 업데이트 중..."

call :log_info "Docker 이미지 재빌드 중..."
docker-compose -f docker-compose.multi.yml build --no-cache

call :restart_instances

call :log_success "업데이트 완료!"
goto :eof

:: 완전 제거
:cleanup
call :log_warning "모든 인스턴스와 데이터를 제거합니다. 계속하시겠습니까? (y/N)"
set /p confirm="입력: "

if /i "%confirm%"=="y" (
    call :log_info "완전 제거 중..."
    
    docker-compose -f docker-compose.multi.yml down -v
    
    for /f "tokens=*" %%i in ('docker images -q discord* 2^>nul') do docker rmi %%i 2>nul
    
    set /p log_confirm="로그 파일도 삭제하시겠습니까? (y/N): "
    if /i "!log_confirm!"=="y" (
        rmdir /s /q logs 2>nul
        call :log_info "로그 파일 삭제됨"
    )
    
    call :log_success "완전 제거 완료"
) else (
    call :log_info "취소됨"
)
goto :eof

:: 메인 메뉴
:show_menu
echo.
echo ==========================================
echo   Discord AI Bot 다중 인스턴스 관리
echo ==========================================
echo 1. 인스턴스 시작
echo 2. 인스턴스 중지
echo 3. 인스턴스 재시작
echo 4. 상태 확인
echo 5. 로그 보기
echo 6. 업데이트
echo 7. 완전 제거
echo 8. 종료
echo ==========================================
goto :eof

:: 메인 함수
:main
:: 인자가 있으면 직접 실행
if not "%~1"=="" (
    if "%~1"=="start" (
        call :check_requirements
        call :validate_env
        call :create_directories
        call :start_instances
    ) else if "%~1"=="stop" (
        call :stop_instances
    ) else if "%~1"=="restart" (
        call :check_requirements
        call :validate_env
        call :restart_instances
    ) else if "%~1"=="status" (
        call :show_status
    ) else if "%~1"=="logs" (
        call :show_logs
    ) else if "%~1"=="update" (
        call :check_requirements
        call :validate_env
        call :update_instances
    ) else if "%~1"=="cleanup" (
        call :cleanup
    ) else (
        call :log_error "사용법: %0 [start|stop|restart|status|logs|update|cleanup]"
        pause
        exit /b 1
    )
    goto :eof
)

:: 인터랙티브 모드
:interactive_loop
call :show_menu
set /p choice="선택 (1-8): "

if "%choice%"=="1" (
    call :check_requirements
    call :validate_env
    call :create_directories
    call :start_instances
) else if "%choice%"=="2" (
    call :stop_instances
) else if "%choice%"=="3" (
    call :check_requirements
    call :validate_env
    call :restart_instances
) else if "%choice%"=="4" (
    call :show_status
) else if "%choice%"=="5" (
    call :show_logs
) else if "%choice%"=="6" (
    call :check_requirements
    call :validate_env
    call :update_instances
) else if "%choice%"=="7" (
    call :cleanup
) else if "%choice%"=="8" (
    call :log_info "종료합니다."
    goto :end
) else (
    call :log_error "잘못된 선택입니다."
)

echo.
pause
goto :interactive_loop

:end
pause
