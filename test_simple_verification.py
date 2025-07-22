#!/usr/bin/env python3
"""
简单的企业微信验证测试
模拟企业微信的验证请求
"""

import requests
import hashlib
import time
import random
import string

def generate_signature(token, timestamp, nonce, echostr):
    """生成企业微信签名"""
    params = [token, timestamp, nonce, echostr]
    params.sort()
    temp_str = ''.join(params)
    return hashlib.sha1(temp_str.encode('utf-8')).hexdigest()

def test_webhook_verification():
    """测试webhook验证"""
    print("🔍 测试企业微信webhook验证")
    print("=" * 50)
    
    # 测试参数
    token = "test_token_123456789012345678901234567890"
    timestamp = str(int(time.time()))
    nonce = ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(10))
    echostr = ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(10))
    
    # 生成签名
    signature = generate_signature(token, timestamp, nonce, echostr)
    
    print(f"测试参数:")
    print(f"  Token: {token}")
    print(f"  Timestamp: {timestamp}")
    print(f"  Nonce: {nonce}")
    print(f"  Echostr: {echostr}")
    print(f"  Signature: {signature}")
    print()
    
    # 构造请求URL（需要替换为实际的URL）
    base_url = "https://your-app-name.onrender.com/webhook"
    url = f"{base_url}?msg_signature={signature}&timestamp={timestamp}&nonce={nonce}&echostr={echostr}"
    
    print(f"请求URL: {url}")
    print()
    
    try:
        # 发送GET请求
        response = requests.get(url, timeout=10)
        
        print(f"响应状态码: {response.status_code}")
        print(f"响应头:")
        for key, value in response.headers.items():
            print(f"  {key}: {value}")
        print()
        print(f"响应内容: {response.text}")
        print()
        
        # 验证响应
        if response.status_code == 200:
            if response.text == echostr:
                print("✅ 验证成功！返回内容正确")
            else:
                print(f"❌ 验证失败！期望: {echostr}, 实际: {response.text}")
        else:
            print(f"❌ 请求失败！状态码: {response.status_code}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ 请求异常: {e}")
        print("\n💡 提示:")
        print("1. 请确保应用已部署到Render")
        print("2. 请将base_url替换为实际的URL")
        print("3. 请确保环境变量已正确配置")

def show_manual_test_steps():
    """显示手动测试步骤"""
    print("\n📝 手动测试步骤:")
    print("=" * 50)
    print("1. 部署应用到Render")
    print("2. 获取应用URL: https://your-app-name.onrender.com")
    print("3. 在企业微信管理后台配置:")
    print("   - URL: https://your-app-name.onrender.com/webhook")
    print("   - Token: your_custom_token")
    print("   - EncodingAESKey: your_encoding_aes_key")
    print("4. 点击'保存并验证'")
    print("5. 查看验证结果")
    print()
    print("🔧 调试技巧:")
    print("- 查看Render应用日志")
    print("- 检查环境变量配置")
    print("- 验证Token和EncodingAESKey是否正确")

def main():
    """主函数"""
    print("🚀 企业微信webhook验证测试")
    print("=" * 60)
    print()
    
    # 显示手动测试步骤
    show_manual_test_steps()
    
    # 测试webhook验证
    test_webhook_verification()
    
    print("\n" + "=" * 60)
    print("测试完成！")

if __name__ == "__main__":
    main() 