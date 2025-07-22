"""
企业微信API客户端
"""

import time
import json
import logging
from typing import Optional, Dict, Any
import requests

from .config import WeChatConfig

logger = logging.getLogger(__name__)


class WeChatClient:
    """企业微信API客户端"""
    
    def __init__(self, config: WeChatConfig):
        self.config = config
        self.access_token = None
        self.token_expires_at = 0
        
    def _get_access_token(self) -> str:
        """获取访问令牌"""
        now = time.time()
        
        # 如果令牌未过期，直接返回
        if self.access_token and now < self.token_expires_at:
            return self.access_token
        
        # 获取新令牌
        url = "https://qyapi.weixin.qq.com/cgi-bin/gettoken"
        params = {
            "corpid": self.config.corpid,
            "corpsecret": self.config.corpsecret
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data.get("errcode") == 0:
                self.access_token = data.get("access_token")
                # 令牌有效期7200秒，提前5分钟刷新
                self.token_expires_at = now + data.get("expires_in", 7200) - 300
                logger.info("成功获取访问令牌")
                return self.access_token
            else:
                logger.error(f"获取访问令牌失败: {data}")
                raise Exception(f"获取访问令牌失败: {data}")
                
        except Exception as e:
            logger.error(f"获取访问令牌异常: {e}")
            raise
    
    def send_text_message(self, content: str, user_ids: Optional[list] = None) -> bool:
        """发送文本消息"""
        try:
            url = "https://qyapi.weixin.qq.com/cgi-bin/message/send"
            access_token = self._get_access_token()
            
            # 确定接收者
            if user_ids is None:
                user_ids = self.config.user_ids
            
            touser = "|".join(user_ids) if user_ids else "@all"
            
            data = {
                "touser": touser,
                "msgtype": "text",
                "agentid": self.config.agentid,
                "text": {
                    "content": content
                }
            }
            
            params = {"access_token": access_token}
            response = requests.post(url, params=params, json=data, timeout=10)
            response.raise_for_status()
            result = response.json()
            
            if result.get("errcode") == 0:
                logger.info(f"消息发送成功: {content[:50]}...")
                return True
            else:
                logger.error(f"消息发送失败: {result}")
                return False
                
        except Exception as e:
            logger.error(f"发送消息异常: {e}")
            return False
    
    def send_markdown_message(self, content: str, user_ids: Optional[list] = None) -> bool:
        """发送Markdown消息"""
        try:
            url = "https://qyapi.weixin.qq.com/cgi-bin/message/send"
            access_token = self._get_access_token()
            
            # 确定接收者
            if user_ids is None:
                user_ids = self.config.user_ids
            
            touser = "|".join(user_ids) if user_ids else "@all"
            
            data = {
                "touser": touser,
                "msgtype": "markdown",
                "agentid": self.config.agentid,
                "markdown": {
                    "content": content
                }
            }
            
            params = {"access_token": access_token}
            response = requests.post(url, params=params, json=data, timeout=10)
            response.raise_for_status()
            result = response.json()
            
            if result.get("errcode") == 0:
                logger.info(f"Markdown消息发送成功: {content[:50]}...")
                return True
            else:
                logger.error(f"Markdown消息发送失败: {result}")
                return False
                
        except Exception as e:
            logger.error(f"发送Markdown消息异常: {e}")
            return False 