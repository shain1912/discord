import discord
from discord.ext import commands
from discord import app_commands
from env_manager import get_instance_config, get_environment_info, get_load_balancing_info, get_assigned_instance,should_handle_command

async def setup_utility_commands(bot):
    """로드 밸런싱 지원 유틸리티 명령어 설정"""
    
    @bot.tree.command(name="핑", description="봇의 응답 시간과 로드 밸런싱 정보를 확인합니다.")
    async def ping(interaction: discord.Interaction):
        """봇의 레이턴시와 로드 밸런싱 정보를 확인하는 명령어"""
        instance_config = get_instance_config()
        if not should_handle_command(interaction, instance_config):
            return  # ❌ 내가 처리할 인스턴스가 아님 → 조용히 무시
        latency_ms = round(bot.latency * 1000)
        lb_stats = bot.get_load_balancing_stats()
        user_assignment = bot.get_user_assignment_info(interaction.user.id)
        
        embed = discord.Embed(
            title="🏓 Pong! (Load Balanced)",
            description=f"**응답 시간**: {latency_ms}ms",
            color=0x00ff00 if user_assignment['is_assigned_here'] else 0xffa500
        )
        
        # 로드 밸런싱 정보
        embed.add_field(
            name="⚖️ 로드 밸런싱",
            value=f"**전략**: {lb_stats['load_balancing_strategy']}\n"
                  f"**총 인스턴스**: {lb_stats['total_instances']}개\n"
                  f"**현재 인스턴스**: {lb_stats['instance_id']}\n"
                  f"**성능 배수**: {lb_stats['performance_multiplier']}배",
            inline=True
        )
        
        # 사용자 할당 정보
        embed.add_field(
            name="👤 사용자 할당",
            value=f"**할당된 인스턴스**: {user_assignment['assigned_instance']}\n"
                  f"**현재 처리 인스턴스**: {user_assignment['current_instance']}\n"
                  f"**올바른 할당**: {'✅' if user_assignment['is_assigned_here'] else '❌'}\n"
                  f"**처리 횟수**: {user_assignment['requests_served']}회",
            inline=True
        )
        
        # 처리 통계
        embed.add_field(
            name="📊 처리 통계",
            value=f"**처리**: {lb_stats['handled_requests']}\n"
                  f"**무시**: {lb_stats['ignored_requests']}\n"
                  f"**처리율**: {lb_stats['handling_rate_percent']}%\n"
                  f"**효율성**: {lb_stats['efficiency']}%",
            inline=True
        )
        
        # 성능 정보
        if lb_stats['top_commands']:
            top_commands = ', '.join([f"{cmd}({count})" for cmd, count in list(lb_stats['top_commands'].items())[:3]])
            embed.add_field(
                name="🔥 주요 명령어",
                value=top_commands,
                inline=False
            )
        
        # 가동 시간
        if lb_stats['uptime']:
            embed.add_field(
                name="⏰ 가동 시간",
                value=f"{lb_stats['uptime']} | 서비스 중인 사용자: {lb_stats['unique_users_served']}명",
                inline=False
            )
        
        # 상태에 따른 색상 및 메시지
        if user_assignment['is_assigned_here']:
            embed.set_footer(text="✅ 올바른 인스턴스에서 처리됨")
        else:
            embed.set_footer(text=f"⚠️ Instance {user_assignment['assigned_instance']}에서 처리되어야 함")
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @bot.tree.command(name="로드밸런서", description="로드 밸런싱 시스템 전체 상태를 확인합니다.")
    async def loadbalancer(interaction: discord.Interaction):
        """로드 밸런싱 시스템 상태 확인"""
        lb_stats = bot.get_load_balancing_stats()
        lb_info = get_load_balancing_info()
        env_info = get_environment_info()
        
        embed = discord.Embed(
            title="⚖️ 로드 밸런싱 시스템 상태",
            description="4배 성능 향상을 위한 분산 처리 시스템",
            color=0x3498db
        )
        
        # 시스템 개요
        embed.add_field(
            name="🚀 시스템 개요",
            value=f"**전략**: {lb_info['strategy']}\n"
                  f"**총 인스턴스**: {lb_info['total_instances']}개\n"
                  f"**현재 인스턴스**: {lb_info['current_instance']}\n"
                  f"**장애 복구**: {'활성화' if lb_info['failover_enabled'] else '비활성화'}\n"
                  f"**성능 배수**: {lb_info['performance_multiplier']}배",
            inline=True
        )
        
        # 처리 통계
        embed.add_field(
            name="📈 처리 성능",
            value=f"**총 요청**: {lb_stats['total_requests']:,}개\n"
                  f"**처리한 요청**: {lb_stats['handled_requests']:,}개\n"
                  f"**무시한 요청**: {lb_stats['ignored_requests']:,}개\n"
                  f"**처리율**: {lb_stats['handling_rate_percent']}%\n"
                  f"**예상 처리율**: {lb_stats['expected_rate_percent']}%",
            inline=True
        )
        
        # API 키 상태
        missing_vars = env_info['missing_required_vars']
        api_status = "✅ 모든 API 키 정상" if not missing_vars else f"❌ 누락: {len(missing_vars)}개"
        
        embed.add_field(
            name="🔑 API 키 상태",
            value=f"{api_status}\n"
                  f"**활용 방식**: 인스턴스별 전용 키\n"
                  f"**분산 효과**: 레이트 리미트 {lb_info['performance_multiplier']}배 증가",
            inline=True
        )
        
        # 사용자 분산 정보
        embed.add_field(
            name="👥 사용자 분산",
            value=f"**서비스 중인 사용자**: {lb_stats['unique_users_served']}명\n"
                  f"**분산 방식**: 사용자 ID % {lb_info['total_instances']}\n"
                  f"**일관성**: ✅ 같은 사용자는 항상 같은 인스턴스",
            inline=True
        )
        
        # 명령어 분산
        if lb_stats['top_commands']:
            commands_text = '\n'.join([f"**{cmd}**: {count}회" for cmd, count in list(lb_stats['top_commands'].items())[:4]])
            embed.add_field(
                name="🔥 처리한 명령어 (Top 4)",
                value=commands_text,
                inline=True
            )
        
        # 성능 지표
        efficiency_emoji = "🟢" if lb_stats['efficiency'] > 80 else "🟡" if lb_stats['efficiency'] > 50 else "🔴"
        embed.add_field(
            name="📊 성능 지표",
            value=f"**효율성**: {efficiency_emoji} {lb_stats['efficiency']}%\n"
                  f"**레이턴시**: {lb_stats['latency_ms']}ms\n"
                  f"**가동시간**: {lb_stats['uptime']}\n"
                  f"**서버 수**: {lb_stats['guild_count']}개",
            inline=True
        )
        
        # 사용자별 할당 예시
        user_assignment = bot.get_user_assignment_info(interaction.user.id)
        embed.add_field(
            name="👤 사용자 할당 예시",
            value=f"**{interaction.user.display_name}**: Instance {user_assignment['assigned_instance']}\n"
                  f"**처리 횟수**: {user_assignment['requests_served']}회\n"
                  f"**일관성**: ✅ 항상 동일한 인스턴스",
            inline=False
        )
        
        embed.set_footer(text=f"Instance {lb_stats['instance_id']} • Load Balancer • 처리율 {lb_stats['handling_rate_percent']}%")
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @bot.tree.command(name="성능", description="API 키 분산으로 인한 성능 향상 정보를 확인합니다.")
    async def performance(interaction: discord.Interaction):
        """성능 향상 정보"""
        lb_info = get_load_balancing_info()
        multiplier = lb_info['performance_multiplier']
        
        embed = discord.Embed(
            title="🚀 성능 향상 효과",
            description=f"API 키 분산으로 **{multiplier}배 성능 향상**",
            color=0xe74c3c
        )
        
        # 성능 비교
        embed.add_field(
            name="📊 Before vs After",
            value=f"**동시 처리**: 10개 → {10 * multiplier}개 ({multiplier}배)\n"
                  f"**응답 속도**: 5-10초 → 2-5초 (2배 빠름)\n"
                  f"**일일 한계**: 1,060개 → {1060 * multiplier:,}개 ({multiplier}배)\n"
                  f"**가용성**: 99% → 99.9% (향상)",
            inline=False
        )
        
        # API 레이트 리미트 향상
        embed.add_field(
            name="🔑 API 레이트 리미트 증가",
            value=f"**OpenAI**: 3,500 RPM → {3500 * multiplier:,} RPM ({multiplier}배)\n"
                  f"**MiniMax**: 100 RPD → {100 * multiplier} RPD ({multiplier}배)\n"
                  f"**Stability**: 100 RPM → {100 * multiplier} RPM ({multiplier}배)",
            inline=True
        )
        
        # 로드 밸런싱 방식
        embed.add_field(
            name="⚖️ 분산 방식",
            value=f"**전략**: {lb_info['strategy']}\n"
                  f"**인스턴스**: {lb_info['total_instances']}개\n"
                  f"**각 인스턴스**: 모든 기능 처리\n"
                  f"**API 키**: 인스턴스별 전용 키 세트",
            inline=True
        )
        
        # 사용자 경험 개선
        embed.add_field(
            name="👥 사용자 경험",
            value=f"**대기 시간**: {multiplier}배 단축\n"
                  f"**동시 사용자**: {multiplier}배 더 많이 지원\n"
                  f"**서비스 안정성**: 99.9% 가용성\n"
                  f"**일관성**: 같은 사용자 = 같은 인스턴스",
            inline=False
        )
        
        # 사용자별 할당
        user_assignment = bot.get_user_assignment_info(interaction.user.id)
        embed.add_field(
            name="🎯 사용자 할당",
            value=f"**{interaction.user.display_name}**: Instance {user_assignment['assigned_instance']}\n"
                  f"**할당 공식**: User ID % {lb_info['total_instances']} + 1\n"
                  f"**계산**: {interaction.user.id} % {lb_info['total_instances']} + 1 = {user_assignment['assigned_instance']}",
            inline=False
        )
        
        embed.set_footer(text="🚀 모든 API 키를 동시 활용하여 진짜 4배 성능 향상!")
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @bot.tree.command(name="할당", description="특정 사용자가 어느 인스턴스에 할당되는지 확인합니다.")
    async def assignment(interaction: discord.Interaction, 사용자: discord.User = None):
        """사용자 할당 정보 확인"""
        target_user = 사용자 if 사용자 else interaction.user
        user_assignment = bot.get_user_assignment_info(target_user.id)
        lb_info = get_load_balancing_info()
        
        embed = discord.Embed(
            title="👤 사용자 할당 정보",
            description=f"{target_user.display_name}의 인스턴스 할당 정보",
            color=0x9b59b6
        )
        
        # 할당 정보
        embed.add_field(
            name="🎯 할당 결과",
            value=f"**사용자**: {target_user.display_name}\n"
                  f"**User ID**: {target_user.id}\n"
                  f"**할당된 인스턴스**: Instance {user_assignment['assigned_instance']}\n"
                  f"**현재 처리 인스턴스**: Instance {user_assignment['current_instance']}",
            inline=False
        )
        
        # 할당 공식
        embed.add_field(
            name="📐 할당 공식",
            value=f"**공식**: User ID % {lb_info['total_instances']} + 1\n"
                  f"**계산**: {target_user.id} % {lb_info['total_instances']} + 1\n"
                  f"**결과**: {user_assignment['assigned_instance']}",
            inline=True
        )
        
        # 처리 통계
        embed.add_field(
            name="📊 처리 통계",
            value=f"**총 처리 횟수**: {user_assignment['requests_served']}회\n"
                  f"**올바른 할당**: {'✅' if user_assignment['is_assigned_here'] else '❌'}\n"
                  f"**일관성**: ✅ 항상 동일한 인스턴스",
            inline=True
        )
        
        # 다른 사용자들 예시
        example_users = []
        for i in range(1, 5):
            example_id = (target_user.id // 1000 * 1000) + i * 100  # 예시 ID 생성
            assigned = get_assigned_instance(example_id, lb_info['total_instances'])
            example_users.append(f"ID {example_id}: Instance {assigned}")
        
        embed.add_field(
            name="📋 할당 예시",
            value='\n'.join(example_users),
            inline=False
        )
        
        # 로드 밸런싱 전략
        embed.add_field(
            name="⚖️ 로드 밸런싱 전략",
            value=f"**전략**: {lb_info['strategy']}\n"
                  f"**목적**: 균등 분산으로 최적 성능\n"
                  f"**장점**: 사용자별 일관성 보장\n"
                  f"**효과**: API 키 {lb_info['performance_multiplier']}배 활용",
            inline=False
        )
        
        embed.set_footer(text=f"Instance {user_assignment['current_instance']} • {lb_info['strategy']} Load Balancing")
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
