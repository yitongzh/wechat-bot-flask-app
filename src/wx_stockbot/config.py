"""
企业微信配置管理
"""

import os
from typing import Optional
from dataclasses import dataclass


@dataclass
class WeChatConfig:
    """企业微信配置"""
    # 企业ID
    corpid: str
    # 应用Secret
    corpsecret: str
    # 应用AgentId
    agentid: str
    # 接收消息的用户ID列表
    user_ids: list[str]
    # 接收消息的部门ID列表
    dept_ids: list[str]
    # 接收消息的标签ID列表
    tag_ids: list[str]
    # 自定义Token（用于回调验证）
    token: Optional[str] = None
    # 自定义EncodingAESKey（用于消息加解密）
    encoding_aes_key: Optional[str] = None
    
    @classmethod
    def from_env(cls) -> 'WeChatConfig':
        """从环境变量加载配置"""
        return cls(
            corpid=os.getenv('WECHAT_CORPID', ''),
            corpsecret=os.getenv('WECHAT_CORPSECRET', ''),
            agentid=os.getenv('WECHAT_AGENTID', ''),
            user_ids=os.getenv('WECHAT_USER_IDS', '').split(',') if os.getenv('WECHAT_USER_IDS') else [],
            dept_ids=os.getenv('WECHAT_DEPT_IDS', '').split(',') if os.getenv('WECHAT_DEPT_IDS') else [],
            tag_ids=os.getenv('WECHAT_TAG_IDS', '').split(',') if os.getenv('WECHAT_TAG_IDS') else [],
            token=os.getenv('WECHAT_TOKEN'),
            encoding_aes_key=os.getenv('WECHAT_ENCODING_AES_KEY')
        )
    
    def validate(self) -> bool:
        """验证配置是否完整"""
        return all([
            self.corpid,
            self.corpsecret,
            self.agentid
        ])


# 默认配置
DEFAULT_CONFIG = WeChatConfig(
    corpid='',  # 请通过环境变量WECHAT_CORPID设置
    corpsecret='',  # 请通过环境变量WECHAT_CORPSECRET设置
    agentid='',  # 请通过环境变量WECHAT_AGENTID设置
    user_ids=['@all'],  # 默认发送给所有人
    dept_ids=[],
    tag_ids=[]
) 