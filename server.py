from bot.bot_class import MyBot
from channel_manager import setup_bot_events
from config import load_config

def create_bot() -> MyBot:
    """봇 인스턴스 생성"""
    # 봇 생성
    bot = MyBot()
    
    # 채널 및 기본 이벤트 설정
    setup_bot_events(bot)
    
    return bot

def main():
    """메인 함수"""
    try:
        # 설정 로드
        token = load_config()
        
        # 봇 생성 및 실행
        bot = create_bot()
        bot.run(token)
        
    except ValueError as e:
        print(e)
    except Exception as e:
        print(f"Bot failed to start: {e}")

if __name__ == "__main__":
    main()
