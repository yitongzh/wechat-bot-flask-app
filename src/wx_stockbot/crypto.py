"""
企业微信加密验证模块
实现企业微信的签名验证和消息加解密
"""

import hashlib
import hmac
import base64
import struct
import socket
import time
import random
import string
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
import xml.etree.ElementTree as ET
from typing import Optional, Tuple


class WeChatCrypto:
    """企业微信加密解密类"""
    
    def __init__(self, token: str, encoding_aes_key: str, corpid: str):
        """
        初始化加密解密类
        
        Args:
            token: 企业微信Token
            encoding_aes_key: 企业微信EncodingAESKey
            corpid: 企业微信CorpId
        """
        self.token = token
        self.encoding_aes_key = encoding_aes_key
        self.corpid = corpid
        
        # 将EncodingAESKey转换为字节
        self.aes_key = base64.b64decode(encoding_aes_key + "=")
        
    def check_signature(self, signature: str, timestamp: str, nonce: str, echostr: str) -> bool:
        """
        验证签名
        
        Args:
            signature: 企业微信发送的签名
            timestamp: 时间戳
            nonce: 随机数
            echostr: 随机字符串
            
        Returns:
            bool: 签名是否有效
        """
        # 将token、timestamp、nonce、echostr四个参数进行字典序排序
        params = [self.token, timestamp, nonce, echostr]
        params.sort()
        
        # 将四个参数拼接成一个字符串进行sha1加密
        temp_str = ''.join(params)
        hash_sha1 = hashlib.sha1(temp_str.encode('utf-8'))
        
        # 开发者获得加密后的字符串可与signature对比，标识该请求来源于微信
        return hash_sha1.hexdigest() == signature
    
    def decrypt_echostr(self, echostr: str) -> str:
        """
        解密echostr
        
        Args:
            echostr: 企业微信发送的加密字符串
            
        Returns:
            str: 解密后的字符串
        """
        try:
            # 对密文进行解密
            cipher = AES.new(self.aes_key, AES.MODE_CBC, self.aes_key[:16])
            encrypted_msg = base64.b64decode(echostr)
            decrypted_msg = cipher.decrypt(encrypted_msg)
            
            # 去除补位字符
            pad = decrypted_msg[-1]
            content = decrypted_msg[16:-pad]
            
            # 去除4字节的msg_len
            msg_len = struct.unpack("!I", content[:4])[0]
            content = content[4:msg_len+4]
            
            # 去除4字节的随机数
            content = content[4:]
            
            # 去除4字节的corpid
            content = content[4:]
            
            return content.decode('utf-8')
        except Exception as e:
            raise ValueError(f"解密echostr失败: {e}")
    
    def encrypt_msg(self, msg: str, timestamp: str, nonce: str) -> str:
        """
        加密消息
        
        Args:
            msg: 要加密的消息
            timestamp: 时间戳
            nonce: 随机数
            
        Returns:
            str: 加密后的消息
        """
        try:
            # 生成16位随机字符串
            random_str = ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(16))
            
            # 将msg、random_str、timestamp、nonce拼接
            text = msg + random_str + timestamp + nonce
            
            # 使用PKCS7填充
            text_bytes = text.encode('utf-8')
            padded_text = pad(text_bytes, AES.block_size)
            
            # 加密
            cipher = AES.new(self.aes_key, AES.MODE_CBC, self.aes_key[:16])
            encrypted = cipher.encrypt(padded_text)
            
            # Base64编码
            return base64.b64encode(encrypted).decode('utf-8')
        except Exception as e:
            raise ValueError(f"加密消息失败: {e}")
    
    def decrypt_msg(self, encrypted_msg: str) -> str:
        """
        解密消息
        
        Args:
            encrypted_msg: 加密的消息
            
        Returns:
            str: 解密后的消息
        """
        try:
            # Base64解码
            encrypted_bytes = base64.b64decode(encrypted_msg)
            
            # 解密
            cipher = AES.new(self.aes_key, AES.MODE_CBC, self.aes_key[:16])
            decrypted = cipher.decrypt(encrypted_bytes)
            
            # 去除填充
            unpadded = unpad(decrypted, AES.block_size)
            
            # 去除随机字符串和时间戳
            content = unpadded.decode('utf-8')
            # 这里需要根据实际的消息格式进行解析
            return content
        except Exception as e:
            raise ValueError(f"解密消息失败: {e}")


def verify_wechat_signature(token: str, signature: str, timestamp: str, nonce: str, echostr: str) -> bool:
    """
    验证企业微信签名（简化版本）
    
    Args:
        token: 企业微信Token
        signature: 签名
        timestamp: 时间戳
        nonce: 随机数
        echostr: 随机字符串
        
    Returns:
        bool: 签名是否有效
    """
    # 将token、timestamp、nonce、echostr四个参数进行字典序排序
    params = [token, timestamp, nonce, echostr]
    params.sort()
    
    # 将四个参数拼接成一个字符串进行sha1加密
    temp_str = ''.join(params)
    hash_sha1 = hashlib.sha1(temp_str.encode('utf-8'))
    
    # 开发者获得加密后的字符串可与signature对比，标识该请求来源于微信
    return hash_sha1.hexdigest() == signature


def generate_wechat_signature(token: str, timestamp: str, nonce: str, echostr: str) -> str:
    """
    生成企业微信签名
    
    Args:
        token: 企业微信Token
        timestamp: 时间戳
        nonce: 随机数
        echostr: 随机字符串
        
    Returns:
        str: 生成的签名
    """
    # 将token、timestamp、nonce、echostr四个参数进行字典序排序
    params = [token, timestamp, nonce, echostr]
    params.sort()
    
    # 将四个参数拼接成一个字符串进行sha1加密
    temp_str = ''.join(params)
    hash_sha1 = hashlib.sha1(temp_str.encode('utf-8'))
    
    return hash_sha1.hexdigest() 