import os
from io import BytesIO
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env

from PIL import Image, ImageDraw, ImageFont
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

# --- CONFIG ---
TOKEN = os.getenv("TELEGRAM_TOKEN")
if not TOKEN:
    raise Exception("Please set TELEGRAM_TOKEN in your .env file")

PORT = int(os.environ.get("PORT", 5000))  # Render provides PORT automatically
WEBHOOK_URL = os.environ.get("WEBHOOK_URL")  # Set this in Render's environment

FONTS_FOLDER = "fonts"
IMAGE_SIZE = (800, 200)
FONT_SIZE = 60

# Load fonts
fonts = [f for f in os.listdir(FONTS_FOLDER) if f.endswith(".ttf")]
if not fonts:
    raise Exception("No TTF fonts found in fonts folder!")

# Predefined colors
colors = {
    "Black": (0, 0, 0),
    "White": (255, 255, 255),
    "Red": (255, 0, 0),
    "Green": (0, 255, 0),
    "Blue": (0, 0, 255),
    "Yellow": (255, 255, 0),
    "Pink": (255, 105, 180),
    "Purple": (128, 0, 128),
}

# Store user data
user_data = {}

# --- COMMANDS ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in user_data:
        user_data[user_id] = {
            "text": "Hello World!",
            "font": fonts[0],
            "text_color": (0, 0, 0),
            "bg_color": (255, 255, 255),
        }

    buttons = [
        [InlineKeyboardButton("Set Font", callback_data="btn:font")],
        [InlineKeyboardButton("Set Text Color", callback_data="btn:text_color")],
        [InlineKeyboardButton("Set Background Color", callback_data="btn:bg_color")],
        [InlineKeyboardButton("Render Image", callback_data="btn:render")],
        [InlineKeyboardButton("About", callback_data="btn:about")],
    ]
    reply_markup = InlineKeyboardMarkup(buttons)

    await update.message.reply_text(
        "👋 Welcome! Use the buttons below to customize your text image.",
        reply_markup=reply_markup,
    )


# --- CALLBACK HANDLER ---
async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    if user_id not in user_data:
        user_data[user_id] = {
            "text": "Hello World!",
            "font": fonts[0],
            "text_color": (0, 0, 0),
            "bg_color": (255, 255, 255),
        }

    data = query.data

    # --- FONT SELECTION ---
    if data == "btn:font":
        buttons = [[InlineKeyboardButton(f, callback_data=f"font:{f}")] for f in fonts[:10]]
        buttons.append([InlineKeyboardButton("More fonts...", callback_data="font:all")])
        await query.message.reply_text(
            "Choose a font:", reply_markup=InlineKeyboardMarkup(buttons)
        )

    elif data.startswith("font:"):
        font_name = data.split(":")[1]
        if font_name == "all":
            font_list = fonts
        else:
            font_list = [font_name]

        user_data[user_id]["font"] = font_list[0]
        await query.message.reply_text(f"✅ Font set to: {user_data[user_id]['font']}")

    # --- TEXT COLOR ---
    elif data == "btn:text_color":
        buttons = [[InlineKeyboardButton(name, callback_data=f"color:text:{name}")] for name in colors]
        await query.message.reply_text(
            "Choose a text color:", reply_markup=InlineKeyboardMarkup(buttons)
        )

    elif data.startswith("color:text:"):
        color_name = data.split(":")[2]
        user_data[user_id]["text_color"] = colors[color_name]
        await query.message.reply_text(f"✅ Text color set to: {color_name}")

    # --- BACKGROUND COLOR ---
    elif data == "btn:bg_color":
        buttons = [[InlineKeyboardButton(name, callback_data=f"color:bg:{name}")] for name in colors]
        await query.message.reply_text(
            "Choose a background color:", reply_markup=InlineKeyboardMarkup(buttons)
        )

    elif data.startswith("color:bg:"):
        color_name = data.split(":")[2]
        user_data[user_id]["bg_color"] = colors[color_name]
        await query.message.reply_text(f"✅ Background color set to: {color_name}")

    # --- RENDER IMAGE ---
    elif data == "btn:render":
        data_user = user_data[user_id]
        text = data_user["text"]
        font_path = os.path.join(FONTS_FOLDER, data_user["font"])
        text_color = data_user["text_color"]
        bg_color = data_user["bg_color"]

        try:
            font = ImageFont.truetype(font_path, FONT_SIZE)
            img = Image.new("RGB", IMAGE_SIZE, color=bg_color)
            draw = ImageDraw.Draw(img)
            bbox = draw.textbbox((0, 0), text, font=font)
            w = bbox[2] - bbox[0]
            h = bbox[3] - bbox[1]
            position = ((IMAGE_SIZE[0] - w) // 2, (IMAGE_SIZE[1] - h) // 2)
            draw.text(position, text, font=font, fill=text_color)

            bio = BytesIO()
            img.save(bio, format="PNG")
            bio.seek(0)
            await query.message.reply_photo(photo=bio)
        except Exception as e:
            await query.message.reply_text(f"❌ Failed to render image: {e}")

    # --- ABOUT PAGE ---
    elif data == "btn:about":
        await query.message.reply_text(
            "🖌 Font Bot v1.0\n"
            "Developed to generate text images with custom fonts and colors.\n"
            "Commands are button-driven for ease of use.\n"
            "Created by Hanix."
        )


# --- APPLICATION SETUP ---
app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(callback_handler))

print("✅ Bot is ready for webhook deployment...")

# --- RUN WEBHOOK ---
if WEBHOOK_URL:
    app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        webhook_url=WEBHOOK_URL
    )
else:
    # fallback to polling if webhook URL not set (local dev)
    app.run_polling()
