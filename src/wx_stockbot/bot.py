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
    
    def register_message_handler(self, keyword: str, handler: Callable):
        """注册消息处理器"""
        self.message_handlers[keyword] = handler
        logger.info(f"注册消息处理器: {keyword}")
    
    def _handle_info_update(self, message: str, user_id: str) -> str:
        """处理信息更新指令"""
        logger.info(f"收到信息更新指令，来自用户: {user_id}")
        return "2"
    
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
                # 发送定时消息
                success = self.client.send_text_message("1")
                if success:
                    logger.info(f"定时消息发送成功: {datetime.now()}")
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