"""
Create Advertisement Post - Telegram Bot (Bilingual: Persian & English)
------------------------------------------------------------------------
First asks the user to pick a language (Persian / English), then collects:
Name, Phone, Address, Description, Picture — all prompts in the chosen language.
Then sends the picture with a formatted caption back to the user,
and (optionally) posts it to a Telegram channel if CHANNEL_ID is set.
"""

import logging

from telegram import Update, ReplyKeyboardRemove, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import (
    Application,
    CommandHandler,
    ConversationHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# ---------------------------------------------------------------------------
# Setup - put your token directly here
# ---------------------------------------------------------------------------

BOT_TOKEN = ""
CHANNEL_ID = ""  # optional: e.g. "@mychannel" - leave empty if you don't need it

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# Conversation states
LANGUAGE, NAME, PHONE, ADDRESS, DESCRIPTION, PHOTO = range(6)

# ---------------------------------------------------------------------------
# Text for both languages
# ---------------------------------------------------------------------------

TEXTS = {
    "fa": {
        "ask_name": "👋 به ربات *ساخت آگهی* خوش اومدی!\n\nچند تا سوال ازت می‌پرسم تا آگهی‌تو بسازیم.\nهر موقع خواستی، /cancel رو بفرست تا لغو بشه.\n\nاول بگو، *اسمت* چیه؟",
        "ask_phone": "📞 خیلی خب! حالا *شماره تلفن*‌تو بفرست.",
        "ask_address": "📍 *آدرس* چیه؟",
        "ask_description": "📝 حالا یه *توضیح کوتاه* برای آگهی بنویس.",
        "ask_photo": "🖼️ آخرین مرحله — *عکس* آگهی رو بفرست.",
        "not_a_photo": "این عکس نیست. لطفاً یه تصویر بفرست 🖼️",
        "post_ready": "✅ آگهی‌ت آماده شد! برای ساخت یه آگهی جدید /start رو بفرست.",
        "channel_fail": "⚠️ نتونستم توی کانال پست کنم. مطمئن شو ربات توی کانال ادمینه.",
        "cancelled": "❌ لغو شد. برای شروع دوباره /start رو بفرست.",
        "name_label": "نام",
        "phone_label": "تلفن",
        "address_label": "آدرس",
    },
    "en": {
        "ask_name": "👋 Welcome to *Create Advertisement Post* bot!\n\nI'll ask you a few questions to build your advert.\nYou can send /cancel at any time to stop.\n\nFirst, what's your *name*?",
        "ask_phone": "📞 Great! Now send me your *phone number*.",
        "ask_address": "📍 What's the *address*?",
        "ask_description": "📝 Now write a short *description* for the advert.",
        "ask_photo": "🖼️ Last step — send me the *picture* for the advert.",
        "not_a_photo": "That doesn't look like a photo. Please send an image 🖼️",
        "post_ready": "✅ Your advertisement post is ready! Use /start to create another one.",
        "channel_fail": "⚠️ I couldn't post to the channel. Make sure the bot is added as an admin there.",
        "cancelled": "❌ Cancelled. Send /start to begin again.",
        "name_label": "Name",
        "phone_label": "Phone",
        "address_label": "Address",
    },
}


# ---------------------------------------------------------------------------
# Handlers
# ---------------------------------------------------------------------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.clear()
    keyboard = ReplyKeyboardMarkup(
        [[KeyboardButton("فارسی 🇮🇷"), KeyboardButton("English 🇬🇧")]],
        one_time_keyboard=True,
        resize_keyboard=True,
    )
    await update.message.reply_text(
        "لطفاً زبان خود را انتخاب کنید 👇\nPlease choose your language 👇",
        reply_markup=keyboard,
    )
    return LANGUAGE


async def get_language(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    choice = update.message.text.strip()

    if "فارسی" in choice:
        lang = "fa"
    elif "English" in choice:
        lang = "en"
    else:
        # Didn't tap a valid button — ask again
        keyboard = ReplyKeyboardMarkup(
            [[KeyboardButton("فارسی 🇮🇷"), KeyboardButton("English 🇬🇧")]],
            one_time_keyboard=True,
            resize_keyboard=True,
        )
        await update.message.reply_text(
            "لطفاً یکی از دکمه‌ها رو انتخاب کن 👇\nPlease tap one of the buttons 👇",
            reply_markup=keyboard,
        )
        return LANGUAGE

    context.user_data["lang"] = lang
    t = TEXTS[lang]
    await update.message.reply_text(t["ask_name"], parse_mode="Markdown", reply_markup=ReplyKeyboardRemove())
    return NAME


async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    t = TEXTS[context.user_data["lang"]]
    context.user_data["name"] = update.message.text.strip()
    await update.message.reply_text(t["ask_phone"], parse_mode="Markdown")
    return PHONE


async def get_phone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    t = TEXTS[context.user_data["lang"]]
    context.user_data["phone"] = update.message.text.strip()
    await update.message.reply_text(t["ask_address"], parse_mode="Markdown")
    return ADDRESS


async def get_address(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    t = TEXTS[context.user_data["lang"]]
    context.user_data["address"] = update.message.text.strip()
    await update.message.reply_text(t["ask_description"], parse_mode="Markdown")
    return DESCRIPTION


async def get_description(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    t = TEXTS[context.user_data["lang"]]
    context.user_data["description"] = update.message.text.strip()
    await update.message.reply_text(t["ask_photo"], parse_mode="Markdown")
    return PHOTO


async def get_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    lang = context.user_data["lang"]
    t = TEXTS[lang]

    if not update.message.photo:
        await update.message.reply_text(t["not_a_photo"])
        return PHOTO

    photo_file_id = update.message.photo[-1].file_id

    data = context.user_data
    caption = (
        f"📌 *{data['name']}*\n"
        f"📞 {t['phone_label']}: {data['phone']}\n"
        f"📍 {t['address_label']}: {data['address']}\n\n"
        f"📝 {data['description']}"
    )

    await update.message.reply_photo(photo=photo_file_id, caption=caption, parse_mode="Markdown")
    await update.message.reply_text(t["post_ready"])

    if CHANNEL_ID:
        try:
            await context.bot.send_photo(chat_id=CHANNEL_ID, photo=photo_file_id, caption=caption, parse_mode="Markdown")
        except Exception as e:
            logger.error("Failed to post to channel: %s", e)
            await update.message.reply_text(t["channel_fail"])

    context.user_data.clear()
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    lang = context.user_data.get("lang", "en")
    t = TEXTS[lang]
    context.user_data.clear()
    await update.message.reply_text(t["cancelled"], reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    if not BOT_TOKEN or BOT_TOKEN == "اینجا_توکن_جدیدتو_بذار":
        raise RuntimeError("لطفاً توکن ربات رو توی متغیر BOT_TOKEN بذار.")

    application = Application.builder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            LANGUAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_language)],
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
            PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_phone)],
            ADDRESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_address)],
            DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_description)],
            PHOTO: [MessageHandler(filters.PHOTO, get_photo)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    application.add_handler(conv_handler)

    logger.info("Bot is starting...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()