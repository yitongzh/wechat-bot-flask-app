# 企业微信验证调试指南

## 问题描述

企业微信显示 "The request for openapi callback address failed" 错误。

## 可能的原因

### 1. 返回值格式问题
- **问题**: 企业微信期望纯文本响应，但收到了其他格式
- **解决**: 确保返回的是纯文本，不是JSON或其他格式

### 2. 签名验证失败
- **问题**: Token配置错误或签名算法有问题
- **解决**: 检查Token配置和签名验证逻辑

### 3. 参数缺失
- **问题**: 缺少必要的验证参数
- **解决**: 确保所有参数都正确传递

### 4. 网络连接问题
- **问题**: 企业微信无法访问您的URL
- **解决**: 检查URL是否可访问

## 调试步骤

### 步骤1: 检查应用状态
```bash
# 访问应用主页
curl https://your-app-name.onrender.com/

# 检查健康状态
curl https://your-app-name.onrender.com/health
```

### 步骤2: 测试webhook端点
```bash
# 测试webhook验证
curl "https://your-app-name.onrender.com/webhook?msg_signature=test&timestamp=1234567890&nonce=test&echostr=test123"

# 测试简化端点
curl "https://your-app-name.onrender.com/test_webhook?echostr=test123"
```

### 步骤3: 检查Render日志
1. 登录Render控制台
2. 进入您的应用
3. 点击 "Logs" 标签
4. 查看应用日志，寻找错误信息

### 步骤4: 验证环境变量
确保在Render中设置了正确的环境变量：
```
WECHAT_TOKEN=your_custom_token_here
WECHAT_ENCODING_AES_KEY=your_encoding_aes_key_here
```

## 常见解决方案

### 方案1: 简化验证（推荐）
如果签名验证有问题，可以先使用简化验证：

1. 在企业微信管理后台：
   - URL: `https://your-app-name.onrender.com/webhook`
   - Token: 留空或使用简单值
   - EncodingAESKey: 留空

2. 应用会自动使用简化验证模式

### 方案2: 检查Token配置
1. 确保Token长度正确（建议32位）
2. 确保Token只包含字母和数字
3. 确保Token在企业微信和Render中完全一致

### 方案3: 检查URL格式
1. 确保URL以 `/webhook` 结尾
2. 确保URL使用HTTPS协议
3. 确保URL可以正常访问

## 测试工具

### 本地测试
```bash
# 在public-wxbot目录中运行
python test_verification.py
```

### 在线测试
访问您的测试端点：
```
https://your-app-name.onrender.com/test_webhook?echostr=test123
```

应该返回：`test123`

## 日志分析

### 成功日志示例
```
INFO - 收到企业微信URL验证请求:
INFO -   msg_signature: xxx
INFO -   timestamp: xxx
INFO -   nonce: xxx
INFO -   echostr: xxx
INFO - 签名验证成功
INFO - URL验证成功（简化验证）
```

### 失败日志示例
```
WARNING - URL验证失败：缺少必要参数
ERROR - 签名验证失败
ERROR - 解密echostr失败: xxx
```

## 企业微信配置检查清单

- [ ] URL格式正确：`https://your-app-name.onrender.com/webhook`
- [ ] Token配置正确（如果使用）
- [ ] EncodingAESKey配置正确（如果使用）
- [ ] 应用已部署并正常运行
- [ ] 网络连接正常

## 联系支持

如果问题仍然存在，请提供以下信息：
1. Render应用URL
2. 企业微信配置截图
3. Render应用日志
4. 测试结果

## 更新日志

- **2024-01-XX**: 初始版本
- **2024-01-XX**: 添加调试工具和测试端点 