from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, CallbackContext
from shivu import application, OWNER_ID, sudo_users, db

# ✅ Your Private Channel (Bot must be an admin)
CHANNEL_ID = -1002327002224  # Replace with your private channel ID

async def get_permanent_file_id(update: Update, context: CallbackContext) -> None:
    """Forwards media to a channel and retrieves a truly permanent file_id."""
    user_id = update.effective_user.id

    # ✅ Permission Check
    if user_id not in sudo_users and user_id != OWNER_ID:
        await update.message.reply_text("🚫 You don't have permission to extract file IDs!")
        return

    # ✅ Ensure user replied to a message with media
    if not update.message.reply_to_message:
        await update.message.reply_text("❌ Reply to an image, video, or document with `/fileid` to extract the file_id!")
        return

    replied_msg = update.message.reply_to_message
    media_type, file_id, unique_id = None, None, None

    # ✅ Detect Media Type
    if replied_msg.photo:
        file_id = replied_msg.photo[-1].file_id
        unique_id = replied_msg.photo[-1].file_unique_id
        media_type = "🖼 Photo"
    elif replied_msg.video:
        file_id = replied_msg.video.file_id
        unique_id = replied_msg.video.file_unique_id
        media_type = "🎥 Video"
    elif replied_msg.document:
        file_id = replied_msg.document.file_id
        unique_id = replied_msg.document.file_unique_id
        media_type = "📄 Document"
    elif replied_msg.animation:
        file_id = replied_msg.animation.file_id
        unique_id = replied_msg.animation.file_unique_id
        media_type = "🎞 GIF"
    else:
        await update.message.reply_text("❌ No supported media found! Reply to an image, video, or document.")
        return

    # ✅ Re-upload media to the private channel
    forwarded_msg = await context.bot.send_media_group(
        chat_id=CHANNEL_ID,
        media=[replied_msg]
    )

    new_file_id = None
    for msg in forwarded_msg:
        if msg.photo:
            new_file_id = msg.photo[-1].file_id
        elif msg.video:
            new_file_id = msg.video.file_id
        elif msg.document:
            new_file_id = msg.document.file_id
        elif msg.animation:
            new_file_id = msg.animation.file_id

    # ✅ Store File Info in Database
    file_data = {
        "file_unique_id": unique_id,  # This ID is permanent
        "file_id": new_file_id,  # New reliable file ID
        "type": media_type
    }
    await db.file_storage.update_one(
        {"file_unique_id": unique_id}, 
        {"$set": file_data}, 
        upsert=True
    )

    # ✅ Send the permanent file ID to the user
    await update.message.reply_text(
        f"✅ **Permanent File ID Stored!**\n\n"
        f"📌 **Type:** {media_type}\n"
        f"📂 **New File ID:** `{new_file_id}`\n"
        f"🆔 **File Unique ID:** `{unique_id}` (Always remains the same)\n\n"
        f"🔹 **Use this File ID for reliable uploads!**",
        parse_mode="Markdown"
    )

# ✅ Add Command Handler
application.add_handler(CommandHandler("fileid", get_permanent_file_id, block=False))
