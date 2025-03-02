import asyncio
import random
from telegram import Update, Chat, User, ChatPermissions
from telegram.ext import CommandHandler, CallbackContext, MessageHandler, filters
from shivu import application

async def mute(update: Update, context: CallbackContext):
    if not update.message.reply_to_message:
        await update.message.reply_text("Reply to a user to mute them.")
        return

    user_id = update.message.reply_to_message.from_user.id
    chat_id = update.effective_chat.id

    await context.bot.restrict_chat_member(chat_id, user_id, permissions=ChatPermissions(can_send_messages=False))
    await update.message.reply_text(f"Muted {update.message.reply_to_message.from_user.full_name}.")

async def unmute(update: Update, context: CallbackContext):
    if not update.message.reply_to_message:
        await update.message.reply_text("Reply to a user to unmute them.")
        return

    user_id = update.message.reply_to_message.from_user.id
    chat_id = update.effective_chat.id

    await context.bot.restrict_chat_member(chat_id, user_id, permissions=ChatPermissions(can_send_messages=True))
    await update.message.reply_text(f"Unmuted {update.message.reply_to_message.from_user.full_name}.")

async def ban(update: Update, context: CallbackContext):
    if not update.message.reply_to_message:
        await update.message.reply_text("Reply to a user to ban them.")
        return

    user_id = update.message.reply_to_message.from_user.id
    chat_id = update.effective_chat.id

    await context.bot.ban_chat_member(chat_id, user_id)
    await update.message.reply_text(f"Banned {update.message.reply_to_message.from_user.full_name}.")

async def unban(update: Update, context: CallbackContext):
    if len(context.args) == 0:
        await update.message.reply_text("Provide a user ID to unban.")
        return

    user_id = int(context.args[0])
    chat_id = update.effective_chat.id

    await context.bot.unban_chat_member(chat_id, user_id)
    await update.message.reply_text(f"Unbanned user with ID {user_id}.")

async def promote(update: Update, context: CallbackContext):
    if not update.message.reply_to_message:
        await update.message.reply_text("Reply to a user to promote them.")
        return

    user_id = update.message.reply_to_message.from_user.id
    chat_id = update.effective_chat.id

    await context.bot.promote_chat_member(chat_id, user_id, can_manage_chat=True, can_delete_messages=True)
    await update.message.reply_text(f"Promoted {update.message.reply_to_message.from_user.full_name} to admin.")

async def demote(update: Update, context: CallbackContext):
    if not update.message.reply_to_message:
        await update.message.reply_text("Reply to a user to demote them.")
        return

    user_id = update.message.reply_to_message.from_user.id
    chat_id = update.effective_chat.id

    await context.bot.promote_chat_member(chat_id, user_id, can_manage_chat=False, can_delete_messages=False)
    await update.message.reply_text(f"Demoted {update.message.reply_to_message.from_user.full_name}.")

locked_types = {}

async def lock(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    if len(context.args) == 0:
        await update.message.reply_text("Specify a media type to lock (e.g., stickers, photos, videos).")
        return

    media_type = context.args[0].lower()
    locked_types[chat_id] = locked_types.get(chat_id, set())
    locked_types[chat_id].add(media_type)

    await update.message.reply_text(f"Locked {media_type} in this group.")

async def unlock(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    if len(context.args) == 0:
        await update.message.reply_text("Specify a media type to unlock.")
        return

    media_type = context.args[0].lower()
    if chat_id in locked_types and media_type in locked_types[chat_id]:
        locked_types[chat_id].remove(media_type)
        await update.message.reply_text(f"Unlocked {media_type} in this group.")
    else:
        await update.message.reply_text(f"{media_type} is not locked.")

welcome_messages = {}

async def set_welcome(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    welcome_messages[chat_id] = update.message.text.split(' ', 1)[1]
    await update.message.reply_text("Welcome message set.")

async def del_welcome(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    if chat_id in welcome_messages:
        del welcome_messages[chat_id]
        await update.message.reply_text("Welcome message deleted.")

slowmode_settings = {}

async def slowmode(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    if len(context.args) == 0:
        await update.message.reply_text("Specify slow mode duration in seconds.")
        return

    delay = int(context.args[0])
    slowmode_settings[chat_id] = delay
    await update.message.reply_text(f"Slow mode enabled: {delay} seconds per message.")

async def antilink(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    text = update.message.text.lower()

    if "http" in text or "www" in text:
        await update.message.delete()
        await update.message.reply_text("Anti-Link is enabled! Links are not allowed.")

async def purge(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    if update.message.reply_to_message:
        for i in range(update.message.message_id, update.message.reply_to_message.message_id, -1):
            try:
                await context.bot.delete_message(chat_id, i)
            except Exception:
                pass


async def get_id(update: Update, context: CallbackContext):
    """Handles the /id command."""
    message = update.message
    chat = update.effective_chat
    args = context.args

    # ✅ If user mentions someone (/id @username)
    if args:
        username = args[0]
        user = await context.bot.get_chat(username)  # Get user info using username
        await message.reply_text(f"🆔 ID of {user.full_name} (@{user.username}): `{user.id}`", parse_mode="Markdown")
        return

    # ✅ If used in a group, return group ID
    if chat.type in [Chat.GROUP, Chat.SUPERGROUP]:
        await message.reply_text(f"🆔 This Group's ID: `{chat.id}`", parse_mode="Markdown")
        return

    # ✅ If used in private chat, return user's own ID
    user: User = update.effective_user
    await message.reply_text(f"🆔 Your User ID: `{user.id}`", parse_mode="Markdown")
async def get_sticker_id(update: Update, context: CallbackContext):
    """Returns the ID of a sticker when replied to."""
    if not update.message.reply_to_message or not update.message.reply_to_message.sticker:
        await update.message.reply_text("❌ Please reply to a sticker to get its ID.")
        return

    sticker = update.message.reply_to_message.sticker
    await update.message.reply_text(f"🆔 Sticker ID: `{sticker.file_id}`", parse_mode="Markdown")


# ✅ Register the /id Command
application.add_handler(CommandHandler("id", get_id))
application.add_handler(CommandHandler("mute", mute))
application.add_handler(CommandHandler("unmute", unmute))
application.add_handler(CommandHandler("ban", ban))
application.add_handler(CommandHandler("unban", unban))
application.add_handler(CommandHandler("promote", promote))
application.add_handler(CommandHandler("demote", demote))
application.add_handler(CommandHandler("lock", lock))
application.add_handler(CommandHandler("unlock", unlock))
application.add_handler(CommandHandler("setwelcome", set_welcome))
application.add_handler(CommandHandler("delwelcome", del_welcome))
application.add_handler(CommandHandler("slowmode", slowmode))
application.add_handler(CommandHandler("antilink", antilink))
application.add_handler(CommandHandler("purge", purge))
application.add_handler(CommandHandler("fileid", get_sticker_id))
