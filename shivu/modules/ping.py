import time
from telegram import Update
from telegram.ext import CommandHandler, CallbackContext
from shivu import application, sudo_users, OWNER_ID  # Ensure OWNER_ID is imported

async def ping(update: Update, context: CallbackContext) -> None:
    """Pings the bot and returns the response time."""
    user_id = update.effective_user.id

    # ✅ Ensure both Sudo Users and Owner can use it
    if user_id not in sudo_users and user_id != OWNER_ID:
        await update.message.reply_text("🚫 This command is for sudo users only.")
        return

    # ✅ Measure response time
    start_time = time.time()
    message = await update.message.reply_text('🏓 Pong...')
    end_time = time.time()
    elapsed_time = round((end_time - start_time) * 1000, 3)

    # ✅ Edit message with response time
    await message.edit_text(f'🏓 Pong! `{elapsed_time}ms`', parse_mode="Markdown")

# ✅ Register Handler
application.add_handler(CommandHandler("ping", ping, block=False))
