import discord
from discord.ext import commands
from discord import app_commands
from typing import Optional
import logging
import asyncio

# 로드 밸런싱 모듈들
from env_manager import (
    get_instance_config, 
    should_handle_command,
    get_environment_info,
    get_assigned_instance,
    get_load_balancing_info,
    init_environment
)
from request_manager_enhanced import EnhancedRequestManager
from utils import split_message

class LoadBalancedBot(commands.Bot):
    def __init__(self):
        # 환경 변수 초기화
        init_environment()
        
        # 인스턴스 설정 로드
        self.instance_config = get_instance_config()
        self.load_balancing_info = get_load_balancing_info()
        
        # 인텐트 설정
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        
        # 봇 초기화
        super().__init__(
            command_prefix=f"!lb{self.instance_config['instance_id']}", 
            intents=intents
        )
        
        # Enhanced 매니저 초기화
        self.request_manager = EnhancedRequestManager()
        
        # 로드 밸런싱 통계
        self.lb_stats = {
            'total_requests': 0,
            'handled_requests': 0,
            'ignored_requests': 0,
            'user_distribution': {},  # 사용자별 처리 통계
            'command_distribution': {},  # 명령어별 처리 통계
            'errors': 0,
            'uptime_start': None
        }
        
        # 로거 설정
        self.setup_logging()
        
    def setup_logging(self):
        """로드 밸런싱 로거 설정"""
        log_file = self.instance_config.get('log_file', f"logs/instance_{self.instance_config['instance_id']}.log")
        
        self.logger = logging.getLogger(f"lb_instance_{self.instance_config['instance_id']}")
        self.logger.setLevel(logging.INFO)
        
        if not self.logger.handlers:
            handler = logging.FileHandler(log_file, encoding='utf-8')
            formatter = logging.Formatter(
                f"[LoadBalancer-{self.instance_config['instance_id']}] "
                "%(asctime)s - %(levelname)s - %(message)s"
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
        
    async def setup_hook(self):
        """봇 초기 설정 - 로드 밸런싱 방식"""
        import datetime
        self.lb_stats['uptime_start'] = datetime.datetime.now()
        
        instance_id = self.instance_config['instance_id']
        strategy = self.load_balancing_info['strategy']
        total_instances = self.load_balancing_info['total_instances']
        
        self.logger.info(f"Load Balanced Bot Instance {instance_id} starting...")
        self.logger.info(f"Strategy: {strategy}, Total Instances: {total_instances}")
        print(f"🚀 Load Balancer Instance {instance_id} ({strategy}) is setting up...")
        
        # 모든 명령어 설정 (로드 밸런싱은 모든 기능 활성화)
        await self.setup_all_commands()
        
        # 에러 이벤트 설정
        from bot.events import setup_error_events
        await setup_error_events(self)
        
        # Enhanced Queue processor 시작
        self.request_manager.start_queue_processor(self)
        
        # Primary 인스턴스만 슬래시 명령어 동기화
        if self.instance_config.get('is_primary', False):
            await self.tree.sync()
            self.logger.info("Primary instance - slash commands synced")
        else:
            self.logger.info("Secondary instance - skipping command sync")
        
        self.logger.info(f"Load Balancer Instance {instance_id} setup completed")
        print(f"✅ Load Balancer Instance {instance_id} ready for traffic!")

    async def setup_all_commands(self):
        """모든 명령어 설정 (로드 밸런싱은 모든 기능 활성화)"""
        self.logger.info("Setting up all commands for load balancing...")
        
        # 모든 명령어 로드
        from commands.chat_commands import setup_chat_commands
        from commands.image_commands import setup_image_commands
        from commands.video_commands import setup_video_commands
        from commands.utility_commands import setup_utility_commands
        
        await setup_chat_commands(self)
        await setup_image_commands(self)
        await setup_video_commands(self)
        await setup_utility_commands(self)
        
        self.logger.info("All commands loaded successfully")

    async def on_interaction(self, interaction: discord.Interaction):
        """로드 밸런싱 인터셉터"""
        if interaction.type != discord.InteractionType.application_command:
            return # await super().on_interaction(interaction)
        
        # 통계 업데이트
        self.lb_stats['total_requests'] += 1
        
        # 명령어와 사용자 정보 추출
        command_name = interaction.data.get('name', '')
        user_id = interaction.user.id
        
        # 이 인스턴스가 처리해야 하는지 확인 (로드 밸런싱)
        should_handle = should_handle_command(interaction, self.instance_config)
        
        if should_handle:
            # 처리 통계 업데이트
            self.lb_stats['handled_requests'] += 1
            
            # 사용자별 통계
            if user_id not in self.lb_stats['user_distribution']:
                self.lb_stats['user_distribution'][user_id] = 0
            self.lb_stats['user_distribution'][user_id] += 1
            
            # 명령어별 통계
            if command_name not in self.lb_stats['command_distribution']:
                self.lb_stats['command_distribution'][command_name] = 0
            self.lb_stats['command_distribution'][command_name] += 1
            
            # 할당 정보 로깅
            assigned_instance = get_assigned_instance(user_id, self.load_balancing_info['total_instances'])
            self.logger.info(
                f"Processing '{command_name}' for user {user_id} "
                f"(assigned: {assigned_instance}, current: {self.instance_config['instance_id']})"
            )
            
            return # await super().on_interaction(interaction)
        else:
            # 무시 통계 업데이트
            self.lb_stats['ignored_requests'] += 1
            
            assigned_instance = get_assigned_instance(user_id, self.load_balancing_info['total_instances'])
            self.logger.debug(
                f"Ignoring '{command_name}' for user {user_id} "
                f"(assigned: {assigned_instance}, current: {self.instance_config['instance_id']})"
            )
            # 조용히 무시 (다른 인스턴스가 처리)
            return

    async def send_long_message(self, interaction: discord.Interaction, content: str):
        """긴 메시지를 여러 청크로 분할하여 전송"""
        chunks = split_message(content, 2000)
        
        if chunks:
            await interaction.followup.send(chunks[0])
            for chunk in chunks[1:]:
                await interaction.channel.send(chunk)

    async def close(self):
        """봇 종료 시 정리 작업"""
        instance_id = self.instance_config['instance_id']
        self.logger.info(f"Load Balancer Instance {instance_id} is shutting down...")
        print(f"🛑 Load Balancer Instance {instance_id} shutting down...")
        
        # Enhanced queue processor 중지
        await self.request_manager.stop_queue_processor()
        
        # 최종 통계 로그
        self.logger.info(f"Final load balancing stats: {self.get_load_balancing_stats()}")
        
        await super().close()

    def get_load_balancing_stats(self) -> dict:
        """로드 밸런싱 통계 반환"""
        import datetime
        
        uptime = None
        if self.lb_stats['uptime_start']:
            uptime = datetime.datetime.now() - self.lb_stats['uptime_start']
        
        # 처리율 계산
        total_requests = self.lb_stats['total_requests']
        handled_requests = self.lb_stats['handled_requests']
        handling_rate = (handled_requests / total_requests * 100) if total_requests > 0 else 0
        
        # 예상 처리율 (균등 분산 시)
        expected_rate = 100 / self.load_balancing_info['total_instances']
        
        return {
            'instance_id': self.instance_config['instance_id'],
            'load_balancing_strategy': self.load_balancing_info['strategy'],
            'total_instances': self.load_balancing_info['total_instances'],
            'total_requests': total_requests,
            'handled_requests': handled_requests,
            'ignored_requests': self.lb_stats['ignored_requests'],
            'handling_rate_percent': round(handling_rate, 2),
            'expected_rate_percent': round(expected_rate, 2),
            'efficiency': round((handling_rate / expected_rate * 100), 2) if expected_rate > 0 else 0,
            'unique_users_served': len(self.lb_stats['user_distribution']),
            'top_commands': dict(sorted(
                self.lb_stats['command_distribution'].items(), 
                key=lambda x: x[1], 
                reverse=True
            )[:5]),
            'errors': self.lb_stats['errors'],
            'uptime': str(uptime) if uptime else None,
            'latency_ms': round(self.latency * 1000, 2),
            'guild_count': len(self.guilds),
            'performance_multiplier': self.load_balancing_info['performance_multiplier']
        }

    def get_user_assignment_info(self, user_id: int) -> dict:
        """특정 사용자의 할당 정보 반환"""
        assigned_instance = get_assigned_instance(user_id, self.load_balancing_info['total_instances'])
        is_assigned_here = assigned_instance == int(self.instance_config['instance_id'])
        
        return {
            'user_id': user_id,
            'assigned_instance': assigned_instance,
            'current_instance': self.instance_config['instance_id'],
            'is_assigned_here': is_assigned_here,
            'requests_served': self.lb_stats['user_distribution'].get(user_id, 0)
        }

# 하위 호환성을 위한 별칭
MyBot = LoadBalancedBot
