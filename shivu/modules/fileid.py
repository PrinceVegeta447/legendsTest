from telegram import Update
from telegram.ext import CommandHandler, CallbackContext
from shivu import application, OWNER_ID, sudo_users

# ✅ Your Channel ID (Make sure the bot is an admin there)
CHANNEL_ID = -1002396392630  

async def get_permanent_file_id(update: Update, context: CallbackContext) -> None:
    """Forwards media to the channel and returns its permanent file_id."""
    user_id = update.effective_user.id

    # ✅ Check permissions
    if user_id not in sudo_users and user_id != OWNER_ID:
        await update.message.reply_text("🚫 You don't have permission to extract file IDs!")
        return

    # ✅ Ensure user replied to a message
    if not update.message.reply_to_message:
        await update.message.reply_text("❌ Reply to an image, video, or document with `/fileid` to extract the file_id!")
        return

    replied_msg = update.message.reply_to_message

    # ✅ Forward the media to the private channel
    forwarded_msg = None
    if replied_msg.photo:
        forwarded_msg = await replied_msg.forward(chat_id=CHANNEL_ID)
        file_type = "🖼 Photo"
    elif replied_msg.video:
        forwarded_msg = await replied_msg.forward(chat_id=CHANNEL_ID)
        file_type = "🎥 Video"
    elif replied_msg.document:
        forwarded_msg = await replied_msg.forward(chat_id=CHANNEL_ID)
        file_type = "📄 Document"
    elif replied_msg.animation:
        forwarded_msg = await replied_msg.forward(chat_id=CHANNEL_ID)
        file_type = "🎞 GIF"
    else:
        await update.message.reply_text("❌ No supported media found! Reply to an image, video, or document.")
        return

    # ✅ Extract the permanent file ID from the forwarded message
    if forwarded_msg.photo:
        file_id = forwarded_msg.photo[-1].file_id
    elif forwarded_msg.video:
        file_id = forwarded_msg.video.file_id
    elif forwarded_msg.document:
        file_id = forwarded_msg.document.file_id
    elif forwarded_msg.animation:
        file_id = forwarded_msg.animation.file_id
    else:
        await update.message.reply_text("❌ Failed to retrieve the file ID.")
        return

    # ✅ Send the permanent file ID to the user
    await update.message.reply_text(
        f"✅ **Extracted Permanent File ID**\n\n"
        f"📌 **Type:** {file_type}\n"
        f"📂 **Permanent File ID:** `{file_id}`\n\n"
        f"🔹 **This ID won't expire. Use it for reliable uploads!**",
        parse_mode="Markdown"
    )

# ✅ Add Command Handler
application.add_handler(CommandHandler("fileid", get_permanent_file_id, block=False))
