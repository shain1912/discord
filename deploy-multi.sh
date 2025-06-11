#!/bin/bash

# Discord AI Bot 다중 인스턴스 배포 스크립트
# 사용법: ./deploy-multi.sh [start|stop|restart|status|logs]

set -e

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 로그 함수들
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 설정 확인
check_requirements() {
    log_info "시스템 요구사항 확인 중..."
    
    # Docker 확인
    if ! command -v docker &> /dev/null; then
        log_error "Docker가 설치되지 않았습니다."
        exit 1
    fi
    
    # Docker Compose 확인
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose가 설치되지 않았습니다."
        exit 1
    fi
    
    # 환경 변수 파일 확인
    if [ ! -f ".env.multi" ]; then
        log_warning ".env.multi 파일이 없습니다."
        if [ -f ".env.multi.example" ]; then
            log_info ".env.multi.example을 복사하여 .env.multi를 생성합니다..."
            cp .env.multi.example .env.multi
            log_warning ".env.multi 파일에 실제 API 키를 입력해주세요!"
            echo "파일 위치: $(pwd)/.env.multi"
            exit 1
        else
            log_error ".env.multi.example 파일도 없습니다."
            exit 1
        fi
    fi
    
    log_success "시스템 요구사항 확인 완료"
}

# 환경 변수 검증
validate_env() {
    log_info "환경 변수 검증 중..."
    
    source .env.multi
    
    # 필수 변수들
    required_vars=(
        "DISCORD_TOKEN"
        "OPENAI_API_KEY_1" "OPENAI_API_KEY_2" "OPENAI_API_KEY_3" "OPENAI_API_KEY_4"
        "MINIMAX_API_KEY_1" "MINIMAX_API_KEY_2" "MINIMAX_API_KEY_3" "MINIMAX_API_KEY_4"
        "STABILITY_API_KEY_1" "STABILITY_API_KEY_2" "STABILITY_API_KEY_3" "STABILITY_API_KEY_4"
    )
    
    missing_vars=()
    
    for var in "${required_vars[@]}"; do
        if [ -z "${!var}" ] || [ "${!var}" = "your_${var,,}_here" ]; then
            missing_vars+=("$var")
        fi
    done
    
    if [ ${#missing_vars[@]} -ne 0 ]; then
        log_error "다음 환경 변수들이 설정되지 않았습니다:"
        for var in "${missing_vars[@]}"; do
            echo "  - $var"
        done
        log_error ".env.multi 파일을 수정하고 다시 시도해주세요."
        exit 1
    fi
    
    log_success "환경 변수 검증 완료 (${#required_vars[@]}개 변수 확인)"
}

# 디렉토리 생성
create_directories() {
    log_info "필요한 디렉토리 생성 중..."
    
    mkdir -p logs/instance1
    mkdir -p logs/instance2
    mkdir -p logs/instance3
    mkdir -p logs/instance4
    mkdir -p backups
    mkdir -p data
    mkdir -p monitoring
    
    log_success "디렉토리 생성 완료"
}

# 인스턴스 시작
start_instances() {
    log_info "다중 인스턴스 시작 중..."
    
    # 환경 변수 파일 지정
    export ENV_FILE=".env.multi"
    
    # Docker Compose로 시작
    docker-compose -f docker-compose.multi.yml --env-file .env.multi up -d
    
    log_success "모든 인스턴스가 시작되었습니다!"
    
    # 시작 후 상태 확인
    sleep 5
    show_status
}

# 인스턴스 중지
stop_instances() {
    log_info "다중 인스턴스 중지 중..."
    
    docker-compose -f docker-compose.multi.yml down
    
    log_success "모든 인스턴스가 중지되었습니다."
}

# 인스턴스 재시작
restart_instances() {
    log_info "다중 인스턴스 재시작 중..."
    
    stop_instances
    sleep 3
    start_instances
}

# 상태 확인
show_status() {
    log_info "인스턴스 상태 확인 중..."
    
    echo ""
    echo "=== Docker 컨테이너 상태 ==="
    docker-compose -f docker-compose.multi.yml ps
    
    echo ""
    echo "=== 리소스 사용량 ==="
    docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}" \
        discord-bot-chat discord-bot-image discord-bot-video discord-bot-admin 2>/dev/null || \
        log_warning "일부 컨테이너가 실행되지 않았습니다."
    
    echo ""
    echo "=== 헬스체크 상태 ==="
    for container in discord-bot-chat discord-bot-image discord-bot-video discord-bot-admin; do
        if docker ps --filter "name=$container" --filter "status=running" -q | grep -q .; then
            health=$(docker inspect --format='{{.State.Health.Status}}' $container 2>/dev/null || echo "no-healthcheck")
            echo "$container: $health"
        else
            echo "$container: stopped"
        fi
    done
}

# 로그 보기
show_logs() {
    log_info "로그 확인 옵션:"
    echo "1. 전체 로그 (실시간)"
    echo "2. 특정 인스턴스 로그"
    echo "3. 에러 로그만"
    echo "4. 최근 100줄"
    
    read -p "선택 (1-4): " choice
    
    case $choice in
        1)
            log_info "전체 로그 실시간 모니터링 (Ctrl+C로 종료)"
            docker-compose -f docker-compose.multi.yml logs -f
            ;;
        2)
            echo "인스턴스 선택:"
            echo "1. Chat (Instance 1)"
            echo "2. Image (Instance 2)" 
            echo "3. Video (Instance 3)"
            echo "4. Admin (Instance 4)"
            read -p "선택 (1-4): " instance_choice
            
            case $instance_choice in
                1) docker-compose -f docker-compose.multi.yml logs -f discord-bot-chat ;;
                2) docker-compose -f docker-compose.multi.yml logs -f discord-bot-image ;;
                3) docker-compose -f docker-compose.multi.yml logs -f discord-bot-video ;;
                4) docker-compose -f docker-compose.multi.yml logs -f discord-bot-admin ;;
                *) log_error "잘못된 선택입니다." ;;
            esac
            ;;
        3)
            log_info "에러 로그 검색 중..."
            docker-compose -f docker-compose.multi.yml logs | grep -i error || log_info "에러 로그가 없습니다."
            ;;
        4)
            log_info "최근 100줄 로그"
            docker-compose -f docker-compose.multi.yml logs --tail=100
            ;;
        *)
            log_error "잘못된 선택입니다."
            ;;
    esac
}

# 헬스체크
health_check() {
    log_info "상세 헬스체크 실행 중..."
    
    containers=("discord-bot-chat" "discord-bot-image" "discord-bot-video" "discord-bot-admin")
    
    for container in "${containers[@]}"; do
        echo ""
        echo "=== $container 헬스체크 ==="
        
        if docker ps --filter "name=$container" --filter "status=running" -q | grep -q .; then
            # 컨테이너 정보
            echo "상태: 실행중"
            
            # 메모리 사용량
            memory=$(docker stats --no-stream --format "{{.MemUsage}}" $container)
            echo "메모리: $memory"
            
            # CPU 사용량
            cpu=$(docker stats --no-stream --format "{{.CPUPerc}}" $container)
            echo "CPU: $cpu"
            
            # 최근 로그 확인
            echo "최근 로그:"
            docker logs --tail=3 $container 2>/dev/null || echo "로그 없음"
            
        else
            echo "상태: 중지됨"
        fi
    done
}

# 업데이트
update_instances() {
    log_info "인스턴스 업데이트 중..."
    
    # 이미지 재빌드
    log_info "Docker 이미지 재빌드 중..."
    docker-compose -f docker-compose.multi.yml build --no-cache
    
    # 인스턴스 재시작
    restart_instances
    
    log_success "업데이트 완료!"
}

# 완전 제거
cleanup() {
    log_warning "모든 인스턴스와 데이터를 제거합니다. 계속하시겠습니까? (y/N)"
    read -p "입력: " confirm
    
    if [ "$confirm" = "y" ] || [ "$confirm" = "Y" ]; then
        log_info "완전 제거 중..."
        
        # 컨테이너 중지 및 제거
        docker-compose -f docker-compose.multi.yml down -v
        
        # 이미지 제거
        docker rmi $(docker images -q discord*) 2>/dev/null || true
        
        # 로그 파일 제거 (선택사항)
        read -p "로그 파일도 삭제하시겠습니까? (y/N): " log_confirm
        if [ "$log_confirm" = "y" ] || [ "$log_confirm" = "Y" ]; then
            rm -rf logs/
            log_info "로그 파일 삭제됨"
        fi
        
        log_success "완전 제거 완료"
    else
        log_info "취소됨"
    fi
}

# 메인 메뉴
show_menu() {
    echo ""
    echo "=========================================="
    echo "  Discord AI Bot 다중 인스턴스 관리"
    echo "=========================================="
    echo "1. 인스턴스 시작"
    echo "2. 인스턴스 중지"
    echo "3. 인스턴스 재시작"
    echo "4. 상태 확인"
    echo "5. 로그 보기"
    echo "6. 헬스체크"
    echo "7. 업데이트"
    echo "8. 완전 제거"
    echo "9. 종료"
    echo "=========================================="
}

# 메인 함수
main() {
    # 인자가 있으면 직접 실행
    if [ $# -gt 0 ]; then
        case $1 in
            start)
                check_requirements
                validate_env
                create_directories
                start_instances
                ;;
            stop)
                stop_instances
                ;;
            restart)
                check_requirements
                validate_env
                restart_instances
                ;;
            status)
                show_status
                ;;
            logs)
                show_logs
                ;;
            health)
                health_check
                ;;
            update)
                check_requirements
                validate_env
                update_instances
                ;;
            cleanup)
                cleanup
                ;;
            *)
                log_error "사용법: $0 [start|stop|restart|status|logs|health|update|cleanup]"
                exit 1
                ;;
        esac
        return
    fi
    
    # 인터랙티브 모드
    while true; do
        show_menu
        read -p "선택 (1-9): " choice
        
        case $choice in
            1)
                check_requirements
                validate_env
                create_directories
                start_instances
                ;;
            2)
                stop_instances
                ;;
            3)
                check_requirements
                validate_env
                restart_instances
                ;;
            4)
                show_status
                ;;
            5)
                show_logs
                ;;
            6)
                health_check
                ;;
            7)
                check_requirements
                validate_env
                update_instances
                ;;
            8)
                cleanup
                ;;
            9)
                log_info "종료합니다."
                exit 0
                ;;
            *)
                log_error "잘못된 선택입니다."
                ;;
        esac
        
        echo ""
        read -p "계속하려면 Enter를 누르세요..."
    done
}

# 스크립트 실행
main "$@"
