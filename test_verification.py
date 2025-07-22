#!/usr/bin/env python3
"""
企业微信URL验证测试脚本
"""

import hashlib
import time
import random
import string

def generate_wechat_signature(token, timestamp, nonce, echostr):
    """生成企业微信签名"""
    # 将token、timestamp、nonce、echostr四个参数进行字典序排序
    params = [token, timestamp, nonce, echostr]
    params.sort()
    
    # 将四个参数拼接成一个字符串进行sha1加密
    temp_str = ''.join(params)
    hash_sha1 = hashlib.sha1(temp_str.encode('utf-8'))
    
    return hash_sha1.hexdigest()

def verify_wechat_signature(token, signature, timestamp, nonce, echostr):
    """验证企业微信签名"""
    # 将token、timestamp、nonce、echostr四个参数进行字典序排序
    params = [token, timestamp, nonce, echostr]
    params.sort()
    
    # 将四个参数拼接成一个字符串进行sha1加密
    temp_str = ''.join(params)
    hash_sha1 = hashlib.sha1(temp_str.encode('utf-8'))
    
    # 开发者获得加密后的字符串可与signature对比，标识该请求来源于微信
    return hash_sha1.hexdigest() == signature

def main():
    """主函数"""
    print("🚀 企业微信URL验证功能测试")
    print("=" * 50)
    
    # 生成测试参数
    token = "test_token_123456789012345678901234567890"
    timestamp = str(int(time.time()))
    nonce = ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(10))
    echostr = ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(10))
    
    print(f"测试参数:")
    print(f"  Token: {token}")
    print(f"  Timestamp: {timestamp}")
    print(f"  Nonce: {nonce}")
    print(f"  Echostr: {echostr}")
    print()
    
    # 生成正确的签名
    correct_signature = generate_wechat_signature(token, timestamp, nonce, echostr)
    print(f"正确签名: {correct_signature}")
    
    # 测试正确签名
    result1 = verify_wechat_signature(token, correct_signature, timestamp, nonce, echostr)
    print(f"正确签名验证结果: {'✅ 通过' if result1 else '❌ 失败'}")
    
    # 测试错误签名
    wrong_signature = "wrong_signature_1234567890"
    result2 = verify_wechat_signature(token, wrong_signature, timestamp, nonce, echostr)
    print(f"错误签名验证结果: {'❌ 失败（期望）' if not result2 else '⚠️ 意外通过'}")
    
    print()
    
    # 构造验证URL
    base_url = "https://your-app-name.onrender.com/webhook"
    url = f"{base_url}?msg_signature={correct_signature}&timestamp={timestamp}&nonce={nonce}&echostr={echostr}"
    
    print(f"验证URL示例:")
    print(f"  {url}")
    print()
    
    # 总结
    if result1 and not result2:
        print("🎉 测试通过！企业微信URL验证功能正常。")
    else:
        print("⚠️  测试失败，请检查实现。")
    
    print("\n📝 企业微信验证流程:")
    print("1. 企业微信发送GET请求到您的URL")
    print("2. 您的服务器验证签名并返回echostr")
    print("3. 企业微信验证返回内容")

if __name__ == "__main__":
    main() 