from http.server import BaseHTTPRequestHandler
import json
import os
import asyncio
from datetime import datetime, timezone, timedelta
from telegram import Update, Bot, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters
import httpx

# ============== 配置 ==============

BOT_TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID = 7058719105

# API 配置
APIS = {
    "小鸡农场": {
        "url": os.environ.get("API_URL_1"),
        "key": os.environ.get("API_KEY_1"),
        "display_user": "API 1"
    },
    "ekan8": {
        "url": os.environ.get("API_URL_2"),
        "key": os.environ.get("API_KEY_2"),
        "display_user": "API 2"
    },
    "呆呆鸟": {
        "url": os.environ.get("API_URL_3"),
        "key": os.environ.get("API_KEY_3"),
        "display_user": "API 3"
    },
    "Youth": {
        "url": os.environ.get("API_URL_4"),
        "key": os.environ.get("API_KEY_4"),
        "display_user": "API 4"
    },
    "福利Youth": {
        "url": os.environ.get("API_URL_5"),
        "key": os.environ.get("API_KEY_5"),
        "display_user": "API 5"
    }
}

# 模型配置
MODELS = {
    # 小鸡农场
    "第三方4.5s": {
        "api": "小鸡农场",
        "model": "[第三方逆1] claude-sonnet-4.5",
        "cost": 1,
        "admin_only": False,
        "max_tokens": 110000
    },
    "g3pro": {
        "api": "小鸡农场",
        "model": "[官转2] gemini-3-pro",
        "cost": 6,
        "admin_only": False,
        "max_tokens": 990000
    },
    "g3flash": {
        "api": "小鸡农场",
        "model": "[官转2] gemini-3-flash",
        "cost": 2,
        "admin_only": False,
        "max_tokens": 990000
    },
    # ekan8
    "4.5o": {
        "api": "ekan8",
        "model": "福利-claude-opus-4-5",
        "cost": 2,
        "admin_only": False,
        "max_tokens": 190000
    },
    "按量4.5o": {
        "api": "ekan8",
        "model": "按量-claude-opus-4-5-20251101",
        "cost": 0,
        "admin_only": True,
        "max_tokens": 190000
    },
    # 呆呆鸟
    "code 4.5h": {
        "api": "呆呆鸟",
        "model": "[code]claude-haiku-4-5-20251001",
        "cost": 0,
        "admin_only": True,
        "max_tokens": 190000
    },
    "code 4.5s": {
        "api": "呆呆鸟",
        "model": "[code]claude-sonnet-4-5-20250929",
        "cost": 0,
        "admin_only": True,
        "max_tokens": 190000
    },
    "code 4.5o": {
        "api": "呆呆鸟",
        "model": "[code]claude-opus-4-5-20251101",
        "cost": 0,
        "admin_only": True,
        "max_tokens": 190000
    },
    "啾啾4.5s": {
        "api": "呆呆鸟",
        "model": "[啾啾]claude-sonnet-4-5-20250929",
        "cost": 5,
        "admin_only": False,
        "max_tokens": 190000
    },
    "啾啾4.5o": {
        "api": "呆呆鸟",
        "model": "[啾啾]claude-opus-4-5-20251101",
        "cost": 10,
        "admin_only": False,
        "max_tokens": 190000
    },
    # Youth
    "awsq 4.5h": {
        "api": "Youth",
        "model": "(awsq)claude-haiku-4-5-20251001",
        "cost": 0,
        "admin_only": True,
        "max_tokens": 190000
    },
    "awsq 4.5st": {
        "api": "Youth",
        "model": "(awsq)claude-sonnet-4-5-20250929-thinking",
        "cost": 0,
        "admin_only": True,
        "max_tokens": 190000
    },
    "kiro 4.5h": {
        "api": "Youth",
        "model": "(kiro)claude-haiku-4-5-20251001",
        "cost": 0,
        "admin_only": True,
        "max_tokens": 190000
    },
    "kiro 4.5s": {
        "api": "Youth",
        "model": "(kiro)claude-sonnet-4-5-20250929",
        "cost": 0,
        "admin_only": True,
        "max_tokens": 190000
    },
    "kiro 4.5o": {
        "api": "Youth",
        "model": "(kiro)claude-opus-4-5-20251101",
        "cost": 0,
        "admin_only": True,
        "max_tokens": 190000
    },
    "aws 4.5s": {
        "api": "Youth",
        "model": "[aws]claude-sonnet-4-5-20250929",
        "cost": 0,
        "admin_only": True,
        "max_tokens": 190000
    },
    "aws 4.5o": {
        "api": "Youth",
        "model": "[aws]claude-opus-4-5-20251101",
        "cost": 0,
        "admin_only": True,
        "max_tokens": 190000
    },
    # 福利Youth
    "福利4s": {
        "api": "福利Youth",
        "model": "claude-4-sonnet-cs",
        "cost": 0,
        "admin_only": True,
        "max_tokens": 190000
    },
    "福利4.5s": {
        "api": "福利Youth",
        "model": "claude-4.5-sonnet-cs",
        "cost": 0,
        "admin_only": True,
        "max_tokens": 190000
    },
    "福利4.1o": {
        "api": "福利Youth",
        "model": "claude-opus-4.1-cs",
        "cost": 0,
        "admin_only": True,
        "max_tokens": 190000
    }
}

DEFAULT_MODEL = "第三方4.5s"

# ============== 用户数据存储 ==============

users_data = {}

def get_user(user_id):
    today = datetime.now(timezone(timedelta(hours=8))).strftime("%Y-%m-%d")
    
    if user_id not in users_data:
        users_data[user_id] = {
            "points": 20,
            "default_uses": 100,
            "last_reset": today,
            "model": DEFAULT_MODEL,
            "history": [],
            "context_token_limit": None,
            "context_round_limit": None
        }
    
    user = users_data[user_id]
    
    # 每日重置
    if user["last_reset"] != today:
        user["points"] = 20
        user["default_uses"] = 100
        user["last_reset"] = today
    
    return user

def is_admin(user_id):
    return user_id == ADMIN_ID

# ============== API 调用 ==============

async def call_api(model_key, messages):
    model_config = MODELS[model_key]
    api_config = APIS[model_config["api"]]
    
    url = f"{api_config['url']}/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_config['key']}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": model_config["model"],
        "messages": messages
    }
    
    async with httpx.AsyncClient(timeout=120) as client:
        response = await client.post(url, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]

# ============== 估算 Token ==============

def estimate_tokens(text):
    return len(text) * 2  # 粗略估算：中文约2token/字

def get_context_messages(user, new_message):
    model_key = user["model"]
    model_config = MODELS[model_key]
    
    # 获取限制
    token_limit = user["context_token_limit"] or model_config["max_tokens"]
    round_limit = user["context_round_limit"]
    
    history = user["history"].copy()
    history.append({"role": "user", "content": new_message})
    
    # 应用轮数限制
    if round_limit:
        history = history[-(round_limit * 2):]
    
    # 应用 token 限制
    total_tokens = 0
    result = []
    for msg in reversed(history):
        msg_tokens = estimate_tokens(msg["content"])
        if total_tokens + msg_tokens > token_limit:
            break
        result.insert(0, msg)
        total_tokens += msg_tokens
    
    return result

# ============== 命令处理 ==============

async def start_command(update: Update, context):
    text = """Hey there! 🎉 Welcome to the bot!

I'm your AI assistant powered by multiple models~
Just send me any message and let's chat! 💬

Quick commands:
• /model - Pick your favorite model ✨
• /points - Check your daily credits 💰
• /help - See all commands

Have fun! 🚀"""
    await update.message.reply_text(text)

async def help_command(update: Update, context):
    text = """🤖 Here's everything you can do:

💬 Chat
Just send me any message!

🎛 Commands:
• /model - Switch between AI models
• /points - Check remaining credits (resets daily!)
• /reset - Clear our conversation history
• /context token <num> - Set max tokens for memory
• /context round <num> - Set max conversation rounds
• /context reset - Reset to default memory settings
• /context - View current memory settings

✨ Tips:
• Default model: 第三方4.5s
• Credits reset at 00:00 daily
• When credits run out, you get 100 more tries with default model!

Need help? Just ask! 😊"""
    await update.message.reply_text(text)

async def points_command(update: Update, context):
    user_id = update.effective_user.id
    
    if is_admin(user_id):
        await update.message.reply_text("You're admin! Unlimited credits~ ∞ ✨")
        return
    
    user = get_user(user_id)
    text = f"""💰 Your Credits:

• Points: {user['points']}/20
• Default model uses left: {user['default_uses']}/100
• Current model: {user['model']}

Resets daily at 00:00! 🔄"""
    await update.message.reply_text(text)

async def reset_command(update: Update, context):
    user_id = update.effective_user.id
    user = get_user(user_id)
    user["history"] = []
    await update.message.reply_text("Conversation cleared! Fresh start~ 🧹✨")

async def context_command(update: Update, context):
    user_id = update.effective_user.id
    user = get_user(user_id)
    args = context.args
    
    if not args:
        # 显示当前设置
        model_config = MODELS[user["model"]]
        token_limit = user["context_token_limit"] or model_config["max_tokens"]
        round_limit = user["context_round_limit"] or "unlimited"
        
        text = f"""📝 Current Context Settings:

• Token limit: {token_limit:,}
• Round limit: {round_limit}
• Model default: {model_config['max_tokens']:,} tokens"""
        await update.message.reply_text(text)
        return
    
    if args[0] == "reset":
        user["context_token_limit"] = None
        user["context_round_limit"] = None
        await update.message.reply_text("Context settings reset to default! 🔄")
        return
    
    if len(args) < 2:
        await update.message.reply_text("Usage: /context token <num> or /context round <num>")
        return
    
    try:
        value = int(args[1])
        if args[0] == "token":
            user["context_token_limit"] = value
            await update.message.reply_text(f"Token limit set to {value:,}! ✅")
        elif args[0] == "round":
            user["context_round_limit"] = value
            await update.message.reply_text(f"Round limit set to {value}! ✅")
        else:
            await update.message.reply_text("Usage: /context token <num> or /context round <num>")
    except ValueError:
        await update.message.reply_text("Please provide a valid number!")

# ============== 模型选择 ==============

async def model_command(update: Update, context):
    user_id = update.effective_user.id
    admin = is_admin(user_id)
    
    keyboard = []
    row = []
    
    for api_name, api_config in APIS.items():
        # 检查该 API 下是否有用户可用的模型
        has_models = False
        for model_key, model_config in MODELS.items():
            if model_config["api"] == api_name:
                if admin or not model_config["admin_only"]:
                    has_models = True
                    break
        
        if has_models:
            display = api_name if admin else api_config["display_user"]
            row.append(InlineKeyboardButton(display, callback_data=f"api_{api_name}"))
            if len(row) == 2:
                keyboard.append(row)
                row = []
    
    if row:
        keyboard.append(row)
    
    user = get_user(user_id)
    text = f"Current model: {user['model']}\n\nSelect API source:"
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

async def callback_handler(update: Update, context):
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    admin = is_admin(user_id)
    data = query.data
    
    if data.startswith("api_"):
        api_name = data[4:]
        
        keyboard = []
        row = []
        
        for model_key, model_config in MODELS.items():
            if model_config["api"] == api_name:
                if admin or not model_config["admin_only"]:
                    cost_text = f" ({model_config['cost']})" if model_config["cost"] > 0 else ""
                    row.append(InlineKeyboardButton(
                        f"{model_key}{cost_text}",
                        callback_data=f"model_{model_key}"
                    ))
                    if len(row) == 2:
                        keyboard.append(row)
                        row = []
        
        if row:
            keyboard.append(row)
        
        keyboard.append([InlineKeyboardButton("← Back", callback_data="back_to_apis")])
        
        display = api_name if admin else APIS[api_name]["display_user"]
        await query.edit_message_text(
            f"Models in {display}:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    elif data.startswith("model_"):
        model_key = data[6:]
        user = get_user(user_id)
        user["model"] = model_key
        await query.edit_message_text(f"Model switched to: {model_key} ✅")
    
    elif data == "back_to_apis":
        keyboard = []
        row = []
        
        for api_name, api_config in APIS.items():
            has_models = False
            for model_key, model_config in MODELS.items():
                if model_config["api"] == api_name:
                    if admin or not model_config["admin_only"]:
                        has_models = True
                        break
            
            if has_models:
                display = api_name if admin else api_config["display_user"]
                row.append(InlineKeyboardButton(display, callback_data=f"api_{api_name}"))
                if len(row) == 2:
                    keyboard.append(row)
                    row = []
        
        if row:
            keyboard.append(row)
        
        user = get_user(user_id)
        await query.edit_message_text(
            f"Current model: {user['model']}\n\nSelect API source:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

# ============== 消息处理 ==============

async def message_handler(update: Update, context):
    user_id = update.effective_user.id
    user = get_user(user_id)
    text = update.message.text
    admin = is_admin(user_id)
    
    model_key = user["model"]
    model_config = MODELS[model_key]
    
    # 权限检查
    if model_config["admin_only"] and not admin:
        user["model"] = DEFAULT_MODEL
        model_key = DEFAULT_MODEL
        model_config = MODELS[model_key]
    
    # 积分检查（非管理员）
    if not admin:
        cost = model_config["cost"]
        
        if user["points"] >= cost:
            user["points"] -= cost
        elif model_key == DEFAULT_MODEL and user["default_uses"] > 0:
            user["default_uses"] -= 1
        elif model_key != DEFAULT_MODEL:
            # 积分不够，切换到默认模型
            if user["default_uses"] > 0:
                user["model"] = DEFAULT_MODEL
                user["default_uses"] -= 1
                await update.message.reply_text(
                    "You've run out of credits! Switched to default model. "
                    f"({user['default_uses']} uses left)"
                )
                model_key = DEFAULT_MODEL
                model_config = MODELS[model_key]
            else:
                await update.message.reply_text(
                    "You've run out of all credits! Please wait until 00:00 for reset."
                )
                return
        else:
            await update.message.reply_text(
                "You've run out of all credits! Please wait until 00:00 for reset."
            )
            return
    
    # 构建消息
    messages = get_context_messages(user, text)
    
    try:
        await update.message.chat.send_action("typing")
        response = await call_api(model_key, messages)
        
        # 保存历史
        user["history"].append({"role": "user", "content": text})
        user["history"].append({"role": "assistant", "content": response})
        
        await update.message.reply_text(response)
        
    except Exception as e:
        await update.message.reply_text(f"Error: {str(e)}")

# ============== Vercel 入口 ==============
async def process_update(update_data):
    app = Application.builder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("points", points_command))
    app.add_handler(CommandHandler("reset", reset_command))
    app.add_handler(CommandHandler("context", context_command))
    app.add_handler(CommandHandler("model", model_command))
    app.add_handler(CallbackQueryHandler(callback_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
    
    await app.initialize()
    await app.bot.initialize()
    
    update = Update.de_json(update_data, app.bot)
    await app.process_update(update)
    
    await app.shutdown()

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write("Bot is alive! 🤖".encode())
    
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        body = self.rfile.read(content_length)
        data = json.loads(body.decode())
        
        asyncio.run(process_update(data))
        
        self.send_response(200)
        self.end_headers()
        self.wfile.write("OK".encode())
