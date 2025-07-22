# 企业微信股票机器人

基于企业微信自建应用功能的量化交易信息推送机器人。

## 功能特性

- ✅ 定时发送消息（每分钟发送"1"）
- ✅ 响应指令消息（收到"信息更新"回复"2"）
- ✅ 支持文本和Markdown消息
- ✅ HTTP服务器接收回调消息
- ✅ 可扩展的消息处理器

## 快速开始

### 1. 环境准备

安装依赖：
```bash
pip install requests flask
```

### 2. 企业微信配置

在企业微信管理后台创建自建应用，获取以下信息：
- 企业ID (corpid)
- 应用Secret (corpsecret)
- 应用AgentId (agentid)

### 3. 环境变量配置

设置环境变量：
```bash
export WECHAT_CORPID="your_corpid"
export WECHAT_CORPSECRET="your_corpsecret"
export WECHAT_AGENTID="your_agentid"
export WECHAT_USER_IDS="user1,user2"  # 可选，默认发送给所有人
```

### 4. 运行机器人

#### 基础模式（仅定时发送）
```bash
python src/wx_stockbot/main.py
```

#### 服务器模式（支持接收消息）
```bash
python src/wx_stockbot/main.py --server
```

### 5. 测试功能

```bash
# 基础功能测试
python src/wx_stockbot/test_bot.py

# 定时发送测试
python src/wx_stockbot/test_bot.py timer
```

## 功能说明

### 定时发送
- 默认每分钟发送消息"1"
- 可通过修改`interval`参数调整发送间隔

### 消息响应
- 收到包含"信息更新"的消息时，自动回复"2"
- 支持自定义消息处理器

### HTTP API

#### 获取状态
```bash
curl http://localhost:5000/status
```

#### 手动发送消息
```bash
curl -X POST http://localhost:5000/send \
  -H "Content-Type: application/json" \
  -d '{"content": "测试消息", "user_ids": ["user1"]}'
```

## 配置说明

### WeChatConfig 配置项

| 参数 | 说明 | 必填 |
|------|------|------|
| corpid | 企业ID | 是 |
| corpsecret | 应用Secret | 是 |
| agentid | 应用AgentId | 是 |
| user_ids | 接收消息的用户ID列表 | 否 |
| dept_ids | 接收消息的部门ID列表 | 否 |
| tag_ids | 接收消息的标签ID列表 | 否 |

### 消息处理器

可以注册自定义消息处理器：

```python
def custom_handler(message: str, user_id: str) -> str:
    if "自定义指令" in message:
        return "自定义回复"
    return None

bot.register_message_handler("自定义指令", custom_handler)
```

## 部署说明

### 1. 生产环境部署

建议使用gunicorn部署HTTP服务器：

```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 src.wx_stockbot.server:app
```

### 2. 反向代理配置

如果使用Nginx反向代理，配置示例：

```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### 3. 企业微信回调配置

在企业微信应用设置中配置回调URL：
```
http://your-domain.com/webhook
```

## 扩展开发

### 添加新的消息类型

1. 在`bot.py`中添加新的处理器方法
2. 在`__init__`中注册处理器
3. 根据需要修改`server.py`中的消息处理逻辑

### 集成量化交易数据

1. 创建数据获取模块
2. 在定时发送中集成数据
3. 添加数据格式化功能

## 故障排除

### 常见问题

1. **连接失败**
   - 检查企业微信配置是否正确
   - 确认网络连接正常

2. **消息发送失败**
   - 检查应用权限设置
   - 确认用户ID格式正确

3. **回调接收失败**
   - 检查服务器端口是否开放
   - 确认回调URL配置正确

### 日志查看

程序运行时会输出详细日志，包括：
- 连接状态
- 消息发送结果
- 错误信息

## 许可证

MIT License 