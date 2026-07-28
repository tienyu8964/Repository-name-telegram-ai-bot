import os
import tempfile
import google.generativeai as genai

from PIL import Image

from telegram import Update
from telegram.ext import (
    Application,
    ContextTypes,
    MessageHandler,
    filters,
)

# ==========================
# 从 Render 环境变量读取
# ==========================

BOT_TOKEN = os.getenv("BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not BOT_TOKEN:
    raise Exception("没有找到 BOT_TOKEN")

if not GEMINI_API_KEY:
    raise Exception("没有找到 GEMINI_API_KEY")

genai.configure(api_key=GEMINI_API_KEY)

model = genai.GenerativeModel(
    "gemini-1.5-flash"
)

SYSTEM_PROMPT = """
你是一位专业AI助手。

你的职责：

1、回答问题

2、像朋友一样聊天

3、安慰用户

4、给建议

5、如果收到K线图片：

分析：

①趋势

②支撑位

③压力位

④均线

⑤成交量

⑥风险

不要保证盈利。

不要100%预测行情。

回答尽量使用中文。
"""

# ==========================
# 文字聊天
# ==========================

async def text_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not update.message:
        return

    question = update.message.text

    response = model.generate_content(
        SYSTEM_PROMPT +
        "\n\n用户：" +
        question
    )

    await update.message.reply_text(
        response.text
    )
# ==========================
# 图片分析
# ==========================

async def photo_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not update.message:
        return

    photo = update.message.photo

    if not photo:
        return

    # 获取最高质量图片
    file = await photo[-1].get_file()

    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as temp:

        await file.download_to_drive(temp.name)

        image = Image.open(temp.name)

    prompt = """
请分析这张加密货币K线图片。

回答格式：

【趋势】

【支撑位】

【压力位】

【成交量】

【均线】

【风险】

如果图片不是K线，请直接描述图片内容。
"""

    response = model.generate_content(
        [prompt, image]
    )

    await update.message.reply_text(
        response.text
    )
    # ==========================
# 创建机器人
# ==========================

app = (
    Application.builder()
    .token(BOT_TOKEN)
    .build()
)

# 文字
app.add_handler(
    MessageHandler(
        filters.TEXT & (~filters.COMMAND),
        text_message
    )
)

# 图片
app.add_handler(
    MessageHandler(
        filters.PHOTO,
        photo_message
    )
)

print("Bot 已启动...")

app.run_polling()
