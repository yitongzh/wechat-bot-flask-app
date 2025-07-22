"""
Flask应用 - 微信机器人
部署到Render的Flask应用，集成微信机器人功能
"""

import os
import sys
import time
import threading
import logging
import base64
import hashlib
import struct
from pathlib import Path
from datetime import datetime
from typing import Optional

from flask import Flask, request, jsonify, render_template_string

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 导入wxbot模块
from src.wx_stockbot.config import WeChatConfig, DEFAULT_CONFIG
from src.wx_stockbot.bot import WeChatBot
from src.wx_stockbot.client import WeChatClient

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 尝试导入AES解密
try:
    # 使用pyaes进行AES解密
    import pyaes
    import base64
    import struct
    import hashlib
    import hmac
    WECHAT_CRYPTO_AVAILABLE = True
    logger.info("pyaes AES模块可用")
except ImportError as e:
    WECHAT_CRYPTO_AVAILABLE = False
    logger.error(f"pyaes AES模块导入失败: {e}")
    logger.error("请确保pyaes已正确安装")

def decrypt_echostr_simple(echostr, encoding_aes_key, corpid):
    """使用pyaes解密企业微信的echostr"""
    try:
        logger.info("开始解密...")
        
        # 检查模块是否可用
        if not WECHAT_CRYPTO_AVAILABLE:
            logger.error("pyaes AES模块不可用")
            return echostr
        
        # Base64解码
        encrypted_data = base64.b64decode(echostr)
        logger.info(f"Base64解码成功，数据长度: {len(encrypted_data)}")
        
        # 获取AES密钥
        aes_key = base64.b64decode(encoding_aes_key + "=")
        logger.info(f"AES密钥长度: {len(aes_key)}")
        
        # 使用前16字节作为IV（企业微信标准）
        iv = encrypted_data[:16]
        logger.info(f"IV: {iv.hex()}")
        
        # 提取加密数据（从第16字节开始）
        ciphertext = encrypted_data[16:]
        logger.info(f"加密数据长度: {len(ciphertext)}")
        
        # AES解密
        def aes_decrypt(ciphertext, key, iv):
            aes = pyaes.AESModeOfOperationCBC(key, iv=iv)
            decrypted = b''
            for i in range(0, len(ciphertext), 16):
                block = ciphertext[i:i+16]
                if len(block) == 16:
                    decrypted += aes.decrypt(block)
            return decrypted
        
        # PKCS7去填充
        def pkcs7_unpad(data):
            pad_len = data[-1]
            if pad_len <= 16 and pad_len > 0:
                # 验证填充
                padding_bytes = data[-pad_len:]
                if all(b == pad_len for b in padding_bytes):
                    return data[:-pad_len]
            return data
        
        # 执行解密
        decrypted = aes_decrypt(ciphertext, aes_key, iv)
        logger.info(f"AES解密成功，数据长度: {len(decrypted)}")
        
        # 去填充
        unpadded = pkcs7_unpad(decrypted)
        logger.info(f"去填充后数据长度: {len(unpadded)}")
        
        # 解析消息格式：跳过前16字节随机数，直接解析XML
        if len(unpadded) < 16:
            logger.error("解密数据长度不足")
            return echostr
        
        # 跳过前16字节随机数，直接解析XML内容
        xml_content = unpadded[16:].decode('utf-8')
        logger.info(f"XML内容: {xml_content}")
        
        # 验证企业ID是否在XML中
        if corpid in xml_content:
            logger.info("企业ID验证成功")
            return xml_content
        else:
            logger.error(f"企业ID验证失败: 期望='{corpid}'")
            return echostr
            
    except Exception as e:
        logger.error(f"解密异常: {e}")
        import traceback
        logger.error(f"详细错误: {traceback.format_exc()}")
        return echostr


def decrypt_message(encrypted_msg, msg_signature, timestamp, nonce, token, encoding_aes_key, corpid):
    """解密企业微信消息"""
    try:
        # 验证签名
        signature = generate_signature(token, timestamp, nonce, encrypted_msg)
        if signature != msg_signature:
            logger.error(f"签名验证失败: 期望={msg_signature}, 实际={signature}")
            return None
        
        logger.info("签名验证成功，开始解密消息...")
        
        # 使用与echostr相同的解密方法
        decrypted_content = decrypt_echostr_simple(encrypted_msg, encoding_aes_key, corpid)
        
        if decrypted_content:
            logger.info(f"消息解密成功: {decrypted_content}")
            return decrypted_content
        else:
            logger.error("消息解密失败")
            return None
            
    except Exception as e:
        logger.error(f"解密消息异常: {e}")
        return None


def generate_signature(token, timestamp, nonce, encrypted_msg):
    """生成签名"""
    try:
        # 按字典序排序
        params = [token, timestamp, nonce, encrypted_msg]
        params.sort()
        
        # 拼接字符串
        string_to_sign = ''.join(params)
        logger.info(f"待签名字符串: {string_to_sign}")
        
        # SHA1哈希
        import hashlib
        signature = hashlib.sha1(string_to_sign.encode('utf-8')).hexdigest()
        logger.info(f"生成的签名: {signature}")
        
        return signature
        
    except Exception as e:
        logger.error(f"生成签名异常: {e}")
        return None


# 创建Flask应用
app = Flask(__name__)

# 全局变量
bot = None
timer_thread = None
running = False

# 应用启动时初始化机器人
def initialize_bot():
    """初始化机器人"""
    global bot
    if bot is None:
        logger.info("初始化微信机器人...")
        if init_bot():
            # 暂时关闭定时发送
            # start_timer()
            logger.info("机器人初始化成功，定时发送已关闭")
        else:
            logger.error("机器人初始化失败")

# 在第一个请求时初始化
_initialized = False

@app.before_request
def before_request():
    """在每个请求前检查是否需要初始化"""
    global _initialized
    if not _initialized:
        initialize_bot()
        _initialized = True


def load_config() -> WeChatConfig:
    """加载配置"""
    # 尝试从环境变量加载
    config = WeChatConfig.from_env()
    
    if config.validate():
        logger.info("从环境变量加载配置成功")
        return config
    
    # 使用默认配置
    logger.warning("环境变量配置不完整，使用默认配置")
    logger.info("请设置以下环境变量:")
    logger.info("WECHAT_CORPID - 企业ID")
    logger.info("WECHAT_CORPSECRET - 应用Secret")
    logger.info("WECHAT_AGENTID - 应用AgentId")
    logger.info("WECHAT_USER_IDS - 用户ID列表（逗号分隔）")
    
    return DEFAULT_CONFIG


def init_bot():
    """初始化机器人"""
    global bot
    
    # 加载配置
    config = load_config()
    
    if not config.validate():
        logger.error("配置验证失败，请检查配置")
        return False
    
    # 创建机器人
    bot = WeChatBot(config)
    
    # 测试连接
    logger.info("测试企业微信连接...")
    test_success = bot.send_message("机器人启动测试")
    if test_success:
        logger.info("连接测试成功")
        return True
    else:
        logger.error("连接测试失败，请检查配置")
        return False


def start_timer():
    """启动定时发送功能"""
    global timer_thread, running
    
    if running:
        logger.warning("定时发送已在运行中")
        return
    
    running = True
    timer_thread = threading.Thread(target=timer_loop, daemon=True)
    timer_thread.start()
    logger.info("启动定时发送功能（每分钟发送'1'）")


def stop_timer():
    """停止定时发送功能"""
    global running
    running = False
    if timer_thread:
        timer_thread.join(timeout=5)
    logger.info("停止定时发送")


def timer_loop():
    """定时发送循环"""
    global running, bot
    
    while running:
        try:
            if bot:
                # 发送定时消息
                success = bot.send_message("1")
                if success:
                    logger.info(f"定时消息发送成功: {datetime.now()}")
                else:
                    logger.error("定时消息发送失败")
            else:
                logger.warning("机器人未初始化，跳过定时发送")
            
            # 等待下次发送
            time.sleep(60)  # 60秒 = 1分钟
            
        except Exception as e:
            logger.error(f"定时发送异常: {e}")
            time.sleep(60)


# Flask路由
@app.route('/', methods=['GET', 'POST'])
def index():
    """主页 - 同时处理企业微信回调"""
    if request.method == 'GET':
        # 检查是否是企业微信验证请求
        msg_signature = request.args.get('msg_signature', '')
        timestamp = request.args.get('timestamp', '')
        nonce = request.args.get('nonce', '')
        echostr = request.args.get('echostr', '')
        
        # 如果包含企业微信验证参数，则进行验证
        if all([msg_signature, timestamp, nonce, echostr]):
            logger.info("根路径收到企业微信验证请求，转发到verify_url")
            return verify_url(request)
    
    elif request.method == 'POST':
        # 处理企业微信POST消息
        logger.info("根路径收到企业微信POST消息，转发到handle_message")
        return handle_message(request)
    
    # 否则显示主页
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>微信机器人 - Flask应用</title>
        <meta charset="utf-8">
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; }
            .container { max-width: 800px; margin: 0 auto; }
            .status { padding: 10px; margin: 10px 0; border-radius: 5px; }
            .success { background-color: #d4edda; color: #155724; }
            .error { background-color: #f8d7da; color: #721c24; }
            .warning { background-color: #fff3cd; color: #856404; }
            .info { background-color: #d1ecf1; color: #0c5460; }
            button { padding: 10px 20px; margin: 5px; border: none; border-radius: 5px; cursor: pointer; }
            .btn-primary { background-color: #007bff; color: white; }
            .btn-success { background-color: #28a745; color: white; }
            .btn-danger { background-color: #dc3545; color: white; }
            .btn-warning { background-color: #ffc107; color: black; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🤖 微信机器人 Flask应用</h1>
            
            <div class="status info">
                <h3>📊 应用状态</h3>
                <p><strong>机器人状态:</strong> {{ "运行中" if bot_status.running else "未运行" }}</p>
                <p><strong>配置状态:</strong> {{ "有效" if bot_status.config_valid else "无效" }}</p>
                <p><strong>处理器数量:</strong> {{ bot_status.handlers_count }}</p>
                <p><strong>最后更新:</strong> {{ bot_status.timestamp }}</p>
            </div>
            
            <div class="status info">
                <h3>🔧 功能说明</h3>
                <ul>
                    <li><strong>定时发送:</strong> 每分钟自动发送"1"</li>
                    <li><strong>消息响应:</strong> 收到"信息更新"后发送"2"</li>
                    <li><strong>Webhook:</strong> 接收企业微信回调消息</li>
                </ul>
            </div>
            
            <div class="status info">
                <h3>🎮 控制面板</h3>
                <button class="btn-primary" onclick="sendTestMessage()">发送测试消息</button>
                <button class="btn-success" onclick="startTimer()">启动定时发送</button>
                <button class="btn-danger" onclick="stopTimer()">停止定时发送</button>
                <button class="btn-warning" onclick="refreshStatus()">刷新状态</button>
            </div>
            
            <div class="status info">
                <h3>📡 API接口</h3>
                <ul>
                    <li><strong>GET /</strong> - 主页（同时处理企业微信验证）</li>
                    <li><strong>GET /status</strong> - 获取机器人状态</li>
                    <li><strong>POST /send</strong> - 发送消息</li>
                    <li><strong>POST /webhook</strong> - 企业微信回调</li>
                </ul>
            </div>
        </div>
        
        <script>
            function sendTestMessage() {
                fetch('/send', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({content: '测试消息'})
                })
                .then(response => response.json())
                .then(data => alert('发送结果: ' + JSON.stringify(data)));
            }
            
            function startTimer() {
                fetch('/timer/start', {method: 'POST'})
                .then(response => response.json())
                .then(data => alert('启动结果: ' + JSON.stringify(data)));
            }
            
            function stopTimer() {
                fetch('/timer/stop', {method: 'POST'})
                .then(response => response.json())
                .then(data => alert('停止结果: ' + JSON.stringify(data)));
            }
            
            function refreshStatus() {
                location.reload();
            }
        </script>
    </body>
    </html>
    """
    
    bot_status = bot.get_status() if bot else {
        "running": False,
        "config_valid": False,
        "handlers_count": 0,
        "timestamp": datetime.now().isoformat()
    }
    
    return render_template_string(html, bot_status=bot_status)


@app.route('/status')
def status():
    """获取机器人状态"""
    if bot:
        return jsonify(bot.get_status())
    else:
        return jsonify({
            "running": False,
            "config_valid": False,
            "handlers_count": 0,
            "timestamp": datetime.now().isoformat(),
            "error": "机器人未初始化"
        })


@app.route('/send', methods=['POST'])
def send_message():
    """发送消息"""
    try:
        data = request.get_json()
        content = data.get('content', '')
        user_ids = data.get('user_ids', None)
        
        if not content:
            return jsonify({'error': '消息内容不能为空'}), 400
        
        if not bot:
            return jsonify({'error': '机器人未初始化'}), 500
        
        success = bot.send_message(content, user_ids)
        return jsonify({'success': success})
        
    except Exception as e:
        logger.error(f"发送消息异常: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/timer/start', methods=['POST'])
def start_timer_route():
    """启动定时发送"""
    try:
        start_timer()
        return jsonify({'success': True, 'message': '定时发送已启动'})
    except Exception as e:
        logger.error(f"启动定时发送异常: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/timer/stop', methods=['POST'])
def stop_timer_route():
    """停止定时发送"""
    try:
        stop_timer()
        return jsonify({'success': True, 'message': '定时发送已停止'})
    except Exception as e:
        logger.error(f"停止定时发送异常: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/webhook', methods=['GET', 'POST'])
def webhook():
    """企业微信回调接口"""
    if not bot:
        return jsonify({'error': '机器人未初始化'}), 500
    
    if request.method == 'GET':
        # 验证回调URL
        return verify_url(request)
    elif request.method == 'POST':
        # 处理消息
        return handle_message(request)


@app.route('/test_webhook', methods=['GET'])
def test_webhook():
    """测试webhook验证功能"""
    try:
        # 获取参数
        echostr = request.args.get('echostr', 'test_echostr_123456')
        
        logger.info(f"测试webhook验证，返回echostr: {echostr}")
        return echostr
        
    except Exception as e:
        logger.error(f"测试webhook异常: {e}")
        return f"测试异常: {str(e)}", 500


@app.route('/test_message', methods=['POST'])
def test_message():
    """测试消息处理功能"""
    try:
        # 模拟企业微信的消息格式
        test_data = {
            'ToUserName': 'ww38cb388d243c322e',
            'FromUserName': 'test_user_123',
            'CreateTime': int(time.time()),
            'MsgType': 'text',
            'Content': '信息更新',
            'MsgId': '123456789'
        }
        
        logger.info("=== 测试消息处理 ===")
        logger.info(f"测试数据: {test_data}")
        
        # 模拟处理消息
        if not bot:
            return jsonify({'error': '机器人未初始化'}), 500
        
        response = bot.handle_incoming_message(test_data['Content'], test_data['FromUserName'])
        logger.info(f"测试响应: {response}")
        
        if response:
            xml_response = f"""<xml>
<ToUserName><![CDATA[{test_data['FromUserName']}]]></ToUserName>
<FromUserName><![CDATA[{test_data['ToUserName']}]]></FromUserName>
<CreateTime>{test_data['CreateTime']}</CreateTime>
<MsgType><![CDATA[text]]></MsgType>
<Content><![CDATA[{response}]]></Content>
</xml>"""
            return xml_response, 200, {'Content-Type': 'application/xml'}
        else:
            return '', 200
            
    except Exception as e:
        logger.error(f"测试消息处理异常: {e}")
        return jsonify({'error': str(e)}), 500


def verify_url(request):
    """验证回调URL - 企业微信验证接口"""
    try:
        # 调试：检查所有环境变量
        logger.info("=== 环境变量调试信息 ===")
        wechat_env_vars = [
            'WECHAT_CORPID', 'WECHAT_CORPSECRET', 'WECHAT_AGENTID', 
            'WECHAT_USER_IDS', 'WECHAT_TOKEN', 'WECHAT_ENCODING_AES_KEY'
        ]
        for var in wechat_env_vars:
            value = os.getenv(var)
            if value:
                # 隐藏敏感信息
                if 'SECRET' in var or 'TOKEN' in var or 'KEY' in var:
                    display_value = value[:8] + '*' * (len(value) - 8)
                else:
                    display_value = value
                logger.info(f"  {var}: {display_value}")
            else:
                logger.info(f"  {var}: 未设置")
        logger.info("=== 环境变量调试结束 ===")
        
        # 获取企业微信验证参数
        msg_signature = request.args.get('msg_signature', '')
        timestamp = request.args.get('timestamp', '')
        nonce = request.args.get('nonce', '')
        echostr = request.args.get('echostr', '')
        
        logger.info(f"收到企业微信URL验证请求:")
        logger.info(f"  msg_signature: {msg_signature}")
        logger.info(f"  timestamp: {timestamp}")
        logger.info(f"  nonce: {nonce}")
        logger.info(f"  echostr: {echostr}")
        
        # 检查必要参数
        if not all([msg_signature, timestamp, nonce, echostr]):
            logger.warning("URL验证失败：缺少必要参数")
            return "验证失败：参数不完整", 400
        
        # 获取配置
        config = load_config()
        logger.info(f"配置检查:")
        logger.info(f"  encoding_aes_key: {'已设置' if config.encoding_aes_key else '未设置'}")
        logger.info(f"  corpid: {'已设置' if config.corpid else '未设置'}")
        
        # 如果配置了EncodingAESKey，尝试解密echostr
        if config.encoding_aes_key and config.corpid:
            logger.info("尝试解密echostr")
            logger.info(f"  encoding_aes_key: {config.encoding_aes_key[:10]}...")
            logger.info(f"  corpid: {config.corpid}")
            
            # 使用pyaes解密
            decrypted_echostr = decrypt_echostr_simple(echostr, config.encoding_aes_key, config.corpid)
            if decrypted_echostr and decrypted_echostr != echostr:
                logger.info(f"解密成功，返回: {decrypted_echostr}")
                return decrypted_echostr
            else:
                logger.warning("解密失败或返回原始值")
        else:
            logger.info("未配置EncodingAESKey或CorpID，跳过解密")
        
        # 如果解密失败或未配置EncodingAESKey，直接返回原始echostr
        logger.info("URL验证成功，返回原始echostr")
        return echostr
            
    except Exception as e:
        logger.error(f"URL验证异常: {e}")
        return f"验证异常: {str(e)}", 500


def handle_message(request):
    """处理接收到的消息"""
    try:
        # 诊断：记录原始请求数据
        logger.info("=== 消息接收诊断 ===")
        logger.info(f"请求方法: {request.method}")
        logger.info(f"请求头: {dict(request.headers)}")
        logger.info(f"请求体长度: {len(request.get_data())}")
        
        # 获取原始数据
        raw_data = request.get_data(as_text=True)
        logger.info(f"原始请求数据: {raw_data}")
        
        # 检查是否是加密消息（XML格式）
        if raw_data.strip().startswith('<xml>'):
            logger.info("检测到XML格式的加密消息，开始解密...")
            
            # 解析XML获取加密数据
            try:
                import xml.etree.ElementTree as ET
                root = ET.fromstring(raw_data)
                
                # 获取加密消息
                encrypt_elem = root.find('Encrypt')
                if encrypt_elem is None:
                    logger.error("XML中未找到Encrypt元素")
                    return jsonify({'error': '无效的加密消息格式'}), 400
                
                encrypted_msg = encrypt_elem.text
                logger.info(f"获取到加密消息: {encrypted_msg}")
                
                # 获取URL参数
                msg_signature = request.args.get('msg_signature', '')
                timestamp = request.args.get('timestamp', '')
                nonce = request.args.get('nonce', '')
                
                logger.info(f"解密参数: msg_signature={msg_signature}, timestamp={timestamp}, nonce={nonce}")
                
                # 解密消息
                config = load_config()
                decrypted_xml = decrypt_message(encrypted_msg, msg_signature, timestamp, nonce, config.token, config.encoding_aes_key, config.corpid)
                
                if decrypted_xml:
                    logger.info(f"解密成功，原始内容: {decrypted_xml}")
                    
                    # 直接解析解密后的XML内容
                    try:
                        # 检查XML是否完整，如果不完整则补充
                        if not decrypted_xml.startswith('<xml>'):
                            # 查找XML开始位置
                            xml_start = decrypted_xml.find('<xml>')
                            if xml_start == -1:
                                xml_start = decrypted_xml.find('<ToUserName>')
                                if xml_start != -1:
                                    decrypted_xml = '<xml>' + decrypted_xml[xml_start:]
                                    logger.info("补充XML头部标签")
                        
                        # 移除末尾的企业ID和填充
                        xml_end = decrypted_xml.find('</xml>')
                        if xml_end != -1:
                            decrypted_xml = decrypted_xml[:xml_end + 6]
                            logger.info("移除末尾多余内容")
                        
                        logger.info(f"处理后的XML: {decrypted_xml}")
                        
                        # 解析XML
                        decrypted_root = ET.fromstring(decrypted_xml)
                        
                        # 提取消息内容
                        data = {}
                        for child in decrypted_root:
                            data[child.tag] = child.text
                        
                        logger.info(f"解析后的消息数据: {data}")
                        
                    except Exception as e:
                        logger.error(f"解析解密内容异常: {e}")
                        return jsonify({'error': f'解析解密内容异常: {str(e)}'}), 400
                else:
                    logger.error("消息解密失败")
                    return jsonify({'error': '消息解密失败'}), 400
                    
            except Exception as e:
                logger.error(f"XML解析或解密异常: {e}")
                return jsonify({'error': f'XML处理异常: {str(e)}'}), 400
        else:
            # 尝试解析JSON（非加密消息）
            try:
                data = request.get_json()
                logger.info(f"解析的JSON数据: {data}")
            except Exception as e:
                logger.error(f"JSON解析失败: {e}")
                return jsonify({'error': '无效的JSON数据'}), 400
        
        if not data:
            logger.error("消息数据为空")
            return jsonify({'error': '无效的消息数据'}), 400
        
        # 解析消息
        msg_type = data.get('MsgType', '')
        logger.info(f"消息类型: {msg_type}")
        logger.info("=== 消息接收诊断结束 ===")
        
        if msg_type == 'text':
            content = data.get('Content', '')
            user_id = data.get('FromUserName', '')
            
            logger.info(f"收到文本消息: {content}, 来自: {user_id}")
            
            # 处理消息
            response = bot.handle_incoming_message(content, user_id)
            
            if response:
                # 返回XML格式的回复
                xml_response = f"""<xml>
<ToUserName><![CDATA[{user_id}]]></ToUserName>
<FromUserName><![CDATA[{data.get('ToUserName', '')}]]></FromUserName>
<CreateTime>{int(time.time())}</CreateTime>
<MsgType><![CDATA[text]]></MsgType>
<Content><![CDATA[{response}]]></Content>
</xml>"""
                logger.info(f"返回XML回复: {xml_response}")
                return xml_response, 200, {'Content-Type': 'application/xml'}
            else:
                # 如果没有回复，返回空字符串
                return '', 200
        
        elif msg_type == 'event':
            event = data.get('Event', '')
            user_id = data.get('FromUserName', '')
            
            logger.info(f"收到事件: {event}, 来自: {user_id}")
            
            # 处理事件
            if event == 'subscribe':
                # 用户关注
                bot.send_message("欢迎使用量化交易机器人！", [user_id])
            
            return jsonify({'errcode': 0, 'errmsg': 'ok'})
        
        else:
            logger.info(f"收到其他类型消息: {msg_type}")
            return jsonify({'errcode': 0, 'errmsg': 'ok'})
            
    except Exception as e:
        logger.error(f"处理消息异常: {e}")
        return jsonify({'errcode': 1, 'errmsg': str(e)}), 500


@app.route('/health')
def health():
    """健康检查接口"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'bot_initialized': bot is not None,
        'timer_running': running
    })


if __name__ == '__main__':
    # 初始化机器人
    logger.info("初始化微信机器人...")
    if init_bot():
        # 启动定时发送
        start_timer()
        logger.info("机器人初始化成功，定时发送已启动")
    else:
        logger.error("机器人初始化失败")
    
    # 启动Flask应用
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False) 