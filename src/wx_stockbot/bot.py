"""
微信机器人主类
实现定时发送和消息响应功能
"""

import time
import threading
import logging
from typing import Optional, Callable
from datetime import datetime

from .client import WeChatClient
from .config import WeChatConfig

logger = logging.getLogger(__name__)


class WeChatBot:
    """微信机器人"""
    
    def __init__(self, config: WeChatConfig):
        self.config = config
        self.client = WeChatClient(config)
        self.running = False
        self.timer_thread = None
        self.message_handlers: dict[str, Callable] = {}
        
        # 注册默认消息处理器
        self.register_message_handler("信息更新", self._handle_info_update)
        self.register_message_handler("打开推送", self._handle_start_timer)
        self.register_message_handler("关闭推送", self._handle_stop_timer)
        self.register_message_handler("定时推送状态", self._handle_timer_status)
    
    def register_message_handler(self, keyword: str, handler: Callable):
        """注册消息处理器"""
        self.message_handlers[keyword] = handler
        logger.info(f"注册消息处理器: {keyword}")
    
    def _handle_info_update(self, message: str, user_id: str) -> str:
        """处理信息更新指令"""
        logger.info(f"收到信息更新指令，来自用户: {user_id}")
        return """📊 股票技术分析报告

🔍 **NVDA 技术指标分析**

**📈 价格走势**
- 当前价格: $875.42 (+2.3%)
- 日内高点: $881.15
- 日内低点: $868.92
- 成交量: 2.8M (较昨日+15%)

**📊 技术指标**

**WR指标 (威廉指标)**
- WR(14): 23.5 (超买区域)
- WR(21): 18.2 (强烈超买)
- 信号: 短期回调风险增加

**SAR指标 (抛物线转向)**
- 当前SAR: $872.30
- 趋势: 上升趋势持续
- 止损位: $870.50

**KDJ指标**
- K值: 78.5 (高位)
- D值: 72.3 (高位)
- J值: 90.8 (超买)
- 信号: 短期可能回调

**📋 综合分析**

**优势因素:**
✅ AI芯片需求持续强劲
✅ 数据中心业务增长稳定
✅ 新产品线市场反应积极

**风险提示:**
⚠️ 技术指标显示超买
⚠️ 短期回调压力增大
⚠️ 市场情绪过于乐观

**🎯 操作建议**
- 短期: 谨慎观望，等待回调
- 中期: 逢低布局，目标$900
- 长期: 基本面支撑，继续看好

**📅 重要日期**
- 下周三: 财报发布
- 下周五: 期权到期日

---
*数据更新时间: 2025-01-22 15:30 EST*
*仅供参考，投资有风险*"""
    
    def _handle_start_timer(self, message: str, user_id: str) -> str:
        """处理打开推送指令"""
        logger.info(f"收到打开推送指令，来自用户: {user_id}")
        if not self.running:
            self.start_timer(60)  # 每分钟推送
            return "✅ 定时推送已打开"
        else:
            return "⚠️ 定时推送已经在运行中"
    
    def _handle_stop_timer(self, message: str, user_id: str) -> str:
        """处理关闭推送指令"""
        logger.info(f"收到关闭推送指令，来自用户: {user_id}")
        if self.running:
            self.stop_timer()
            return "🛑 定时推送已关闭"
        else:
            return "⚠️ 定时推送已经是关闭状态"
    
    def _handle_timer_status(self, message: str, user_id: str) -> str:
        """处理定时推送状态查询指令"""
        logger.info(f"收到定时推送状态查询，来自用户: {user_id}")
        if self.running:
            return "🟢 定时推送状态：正在运行中"
        else:
            return "🔴 定时推送状态：已关闭"
    
    def start_timer(self, interval: int = 60):
        """启动定时发送功能"""
        if self.running:
            logger.warning("机器人已在运行中")
            return
        
        self.running = True
        self.timer_thread = threading.Thread(
            target=self._timer_loop,
            args=(interval,),
            daemon=True
        )
        self.timer_thread.start()
        logger.info(f"启动定时发送，间隔: {interval}秒")
    
    def stop_timer(self):
        """停止定时发送功能"""
        self.running = False
        if self.timer_thread:
            self.timer_thread.join(timeout=5)
        logger.info("停止定时发送")
    
    def _timer_loop(self, interval: int):
        """定时发送循环"""
        while self.running:
            try:
                # 发送当前时间戳
                current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                success = self.client.send_text_message(f"⏰ 定时推送时间: {current_time}")
                if success:
                    logger.info(f"定时消息发送成功: {current_time}")
                else:
                    logger.error("定时消息发送失败")
                
                # 等待下次发送
                time.sleep(interval)
                
            except Exception as e:
                logger.error(f"定时发送异常: {e}")
                time.sleep(interval)
    
    def send_message(self, content: str, user_ids: Optional[list] = None) -> bool:
        """发送消息"""
        return self.client.send_text_message(content, user_ids)
    
    def send_markdown(self, content: str, user_ids: Optional[list] = None) -> bool:
        """发送Markdown消息"""
        return self.client.send_markdown_message(content, user_ids)
    
    def handle_incoming_message(self, message: str, user_id: str) -> Optional[str]:
        """处理接收到的消息"""
        logger.info(f"收到消息: {message}, 来自用户: {user_id}")
        
        # 检查是否有匹配的处理器
        for keyword, handler in self.message_handlers.items():
            if keyword in message:
                try:
                    response = handler(message, user_id)
                    if response:
                        logger.info(f"生成回复: {response}")
                        return response
                except Exception as e:
                    logger.error(f"处理消息异常: {e}")
                    return None
        
        logger.info("没有匹配的消息处理器")
        return None
    
    def get_status(self) -> dict:
        """获取机器人状态"""
        return {
            "running": self.running,
            "config_valid": self.config.validate(),
            "handlers_count": len(self.message_handlers),
            "timestamp": datetime.now().isoformat()
        } 