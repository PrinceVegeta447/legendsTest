import time
from telegram import Update
from telegram.ext import MessageHandler, CallbackContext, filters, CommandHandler
from shivu import application

# Track user messages timestamps
user_messages = {}

# Track temporarily banned users (user_id: unban_time)
banned_users = {}

# Anti-Spam Settings
MESSAGE_LIMIT = 6  # Max messages allowed in time window
TIME_WINDOW = 10  # Time window (seconds)
BAN_DURATION = 600  # Ban duration (10 minutes)

async def anti_spam(update: Update, context: CallbackContext) -> None:
    """Tracks user messages and applies a temporary bot ban if spamming."""
    user_id = update.effective_user.id
    current_time = time.time()

    # ✅ Ignore bots but apply to all human users (Admins included)
    if update.effective_user.is_bot:
        return

    # ✅ Check if user is currently banned
    if user_id in banned_users and current_time < banned_users[user_id]:
        return  

    # ✅ Initialize tracking for the user
    if user_id not in user_messages:
        user_messages[user_id] = []

    # ✅ Add current timestamp and remove old ones
    user_messages[user_id].append(current_time)
    user_messages[user_id] = [t for t in user_messages[user_id] if current_time - t <= TIME_WINDOW]

    # ✅ If user exceeds limit, ban from bot commands for 10 minutes
    if len(user_messages[user_id]) > MESSAGE_LIMIT:
        banned_users[user_id] = current_time + BAN_DURATION  # Store unban time

        await update.message.reply_text(
            f"🚨 <b>Anti-Spam Triggered!</b>\n"
            f"❌ <b>{update.effective_user.first_name}</b>, you are banned from using bot commands for 10 minutes!",
            parse_mode="HTML"
        )

# ✅ Middleware to Block Banned Users from Using Commands
async def command_filter(update: Update, context: CallbackContext) -> bool:
    """Prevents banned users from executing commands."""
    user_id = update.effective_user.id
    current_time = time.time()

    # ✅ If user is banned, prevent execution
    if user_id in banned_users and current_time < banned_users[user_id]:
        await update.message.reply_text("🚫 You are temporarily banned from using bot commands! Try again later.")
        return False

    return True  # ✅ Allow command execution

# ✅ Function to Apply Filter on All Commands
def apply_command_filter(handler):
    """Wraps command handlers to include anti-spam protection."""
    async def wrapper(update: Update, context: CallbackContext):
        if await command_filter(update, context):  # ✅ Check if user is banned
            await handler(update, context)  # ✅ Execute command if not banned
    return wrapper

# ✅ Example Command (Now Auto-Protected)
@apply_command_filter
async def start(update: Update, context: CallbackContext):
    pass  # No reply message


# ✅ Apply Filter to All Commands
command_list = ["start", "claim", "collection", "guess", "powerlevel", "collect", "shop", "inventory"]  # Add all command names here

for command in command_list:
    application.add_handler(CommandHandler(command, apply_command_filter(globals()[command]), block=False))

# ✅ Register Anti-Spam Handler
application.add_handler(MessageHandler(filters.ALL, anti_spam, block=False))  # Track spam
