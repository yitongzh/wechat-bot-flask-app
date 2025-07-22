# 🤖 WeChat Bot Flask App

一个基于Flask的微信机器人应用，可以部署到Render平台。

## ✨ 功能特性

- 🤖 **定时发送**: 每分钟自动发送"1"
- 📨 **消息响应**: 收到"信息更新"后发送"2"
- 🌐 **Web界面**: 提供友好的Web控制面板
- 📡 **API接口**: 支持RESTful API调用
- 🔗 **企业微信集成**: 支持企业微信回调

## 🚀 快速开始

### 本地运行

1. **克隆仓库**
   ```bash
   git clone https://github.com/your-username/wechat-bot-flask-app.git
   cd wechat-bot-flask-app
   ```

2. **安装依赖**
   ```bash
   pip install -r requirements-app.txt
   ```

3. **设置环境变量**
   ```bash
   cp env_app_example.txt .env
   # 编辑.env文件，填入你的企业微信配置
   ```

4. **运行应用**
   ```bash
   python app.py
   ```

### 部署到Render

1. **Fork此仓库**

2. **在Render中创建Web Service**
   - 连接你的Git仓库
   - 环境：Python 3
   - 构建命令：`pip install -r requirements-app.txt`
   - 启动命令：`gunicorn app:app`

3. **设置环境变量**
   ```
   WECHAT_CORPID=your_corp_id_here
   WECHAT_CORPSECRET=your_corp_secret_here
   WECHAT_AGENTID=your_agent_id_here
   WECHAT_USER_IDS=user1,user2,user3
   ```

## 📡 API接口

| 接口 | 方法 | 描述 |
|------|------|------|
| `/` | GET | 主页（Web控制面板） |
| `/status` | GET | 获取机器人状态 |
| `/send` | POST | 发送消息 |
| `/timer/start` | POST | 启动定时发送 |
| `/timer/stop` | POST | 停止定时发送 |
| `/webhook` | POST | 企业微信回调 |
| `/health` | GET | 健康检查 |

### 发送消息示例

```bash
curl -X POST http://localhost:5000/send \
  -H "Content-Type: application/json" \
  -d '{"content": "Hello World", "user_ids": ["user1"]}'
```

## 🔧 企业微信配置

### 1. 创建企业微信应用

1. 登录 [企业微信管理后台](https://work.weixin.qq.com/wework_admin/)
2. 进入 "应用管理" → "应用"
3. 创建自建应用

### 2. 获取配置信息

- **企业ID**: 在 "我的企业" 页面查看
- **应用Secret**: 在应用详情页面查看
- **AgentId**: 在应用详情页面查看
- **用户ID**: 在 "通讯录" 页面查看

### 3. 配置回调URL

在应用详情页面设置：
- **接收消息**: `https://your-app.onrender.com/webhook`
- **Token**: 自定义Token
- **EncodingAESKey**: 自定义EncodingAESKey

## 🎯 功能说明

### 定时发送
- 应用启动后自动开始定时发送
- 每分钟发送一次"1"
- 可通过Web界面或API控制

### 消息响应
- 收到"信息更新"消息时自动回复"2"
- 支持自定义消息处理器

### Web控制面板
- 实时显示机器人状态
- 提供控制按钮
- 显示API接口文档

## 📁 项目结构

```
├── app.py                 # Flask应用主文件
├── requirements-app.txt   # Python依赖
├── Procfile              # Render部署配置
├── env_app_example.txt   # 环境变量示例
├── README.md             # 本文档
└── src/
    └── wx_stockbot/      # 微信机器人模块
        ├── bot.py        # 机器人主类
        ├── client.py     # 企业微信客户端
        ├── config.py     # 配置管理
        └── server.py     # HTTP服务器
```

## 🤝 贡献

欢迎提交Issue和Pull Request！

### 开发环境设置

1. Fork仓库
2. 创建功能分支：`git checkout -b feature/amazing-feature`
3. 提交更改：`git commit -m 'Add amazing feature'`
4. 推送分支：`git push origin feature/amazing-feature`
5. 创建Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🙏 致谢

- [Flask](https://flask.palletsprojects.com/) - Web框架
- [企业微信开放平台](https://work.weixin.qq.com/api/) - 企业微信API
- [Render](https://render.com/) - 部署平台

## 📞 支持

如果你遇到问题，请：

1. 查看 [Issues](https://github.com/your-username/wechat-bot-flask-app/issues)
2. 创建新的Issue
3. 联系维护者

---

⭐ 如果这个项目对你有帮助，请给它一个星标！ 