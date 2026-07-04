import os
import re
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes,
)

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


def analyze_text(text: str) -> dict:
    words = text.split()
    word_count = len(words)
    char_count = len(text)
    char_no_spaces = len(text.replace(" ", "").replace("\n", "").replace("\t", ""))

    sentences = [s.strip() for s in re.split(r"[.!?]+", text) if s.strip()]
    sentence_count = len(sentences)

    paragraphs = [p.strip() for p in re.split(r"\n{2,}", text) if p.strip()]
    paragraph_count = len(paragraphs)

    avg_word_len = (
        round(sum(len(w) for w in words) / word_count, 1) if word_count else 0
    )

    reading_seconds = round((word_count / 238) * 60)
    if reading_seconds < 60:
        reading_time = f"{reading_seconds}s"
    else:
        reading_time = f"{reading_seconds // 60}m {reading_seconds % 60}s"

    cleaned = [re.sub(r"[^\w]", "", w).lower() for w in words]
    unique_words = len(set(w for w in cleaned if w))

    return {
        "words": word_count,
        "characters": char_count,
        "characters_no_spaces": char_no_spaces,
        "sentences": sentence_count,
        "paragraphs": paragraph_count,
        "avg_word_len": avg_word_len,
        "unique_words": unique_words,
        "reading_time": reading_time,
    }


def format_stats(stats: dict) -> str:
    return (
        "📊 *Text Statistics*\n"
        "━━━━━━━━━━━━━━━━━━\n"
        f"📝 Words: `{stats['words']}`\n"
        f"🔤 Characters: `{stats['characters']}`\n"
        f"🔡 Chars (no spaces): `{stats['characters_no_spaces']}`\n"
        f"📌 Sentences: `{stats['sentences']}`\n"
        f"📄 Paragraphs: `{stats['paragraphs']}`\n"
        "━━━━━━━━━━━━━━━━━━\n"
        f"🆎 Unique words: `{stats['unique_words']}`\n"
        f"📏 Avg word length: `{stats['avg_word_len']} chars`\n"
        f"⏱ Reading time: `{stats['reading_time']}`"
    )


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [[InlineKeyboardButton("ℹ️ How to use", callback_data="help")]]
    await update.message.reply_text(
        "👋 *Welcome to Word Counter Bot!*\n\n"
        "Send me *any text* and I'll instantly analyse it:\n\n"
        "• Word & character counts\n"
        "• Sentence & paragraph counts\n"
        "• Unique words & avg word length\n"
        "• Estimated reading time\n\n"
        "_Just paste or type your text below_ 👇",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "📖 *Help*\n\n"
        "*Commands:*\n"
        "/start — Welcome message\n"
        "/help  — Show this message\n\n"
        "*Usage:*\n"
        "Send any text and get a full stats breakdown.\n\n"
        "Works with any language! 🌍",
        parse_mode="Markdown",
    )


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = update.message.text.strip()
    if not text:
        await update.message.reply_text("Please send some text to analyse.")
        return

    stats = analyze_text(text)
    await update.message.reply_text(format_stats(stats), parse_mode="Markdown")
    logger.info(
        "Analysed message from user_id=%s | words=%d",
        update.effective_user.id,
        stats["words"],
    )


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    if query.data == "help":
        await query.message.reply_text(
            "Just send me any text and I'll count everything! 🌍",
            parse_mode="Markdown",
        )


def main() -> None:
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN environment variable is not set.")

    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CallbackQueryHandler(button_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    logger.info("Bot starting…")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
