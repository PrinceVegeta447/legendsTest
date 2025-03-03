from telegram import Update, InputMediaPhoto, InputMediaVideo, InputMediaDocument
from telegram.ext import CommandHandler, CallbackContext
from shivu import application, OWNER_ID, sudo_users, db

CHANNEL_ID = -1002327002224  # Your private channel ID

async def get_permanent_file_id(update: Update, context: CallbackContext) -> None:
    """Forwards media to a private channel and retrieves a reliable file_id."""
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
    media_group = []

    # ✅ Detect Media Type & Wrap it Correctly
    if replied_msg.photo:
        file_id = replied_msg.photo[-1].file_id
        unique_id = replied_msg.photo[-1].file_unique_id
        media_type = "🖼 Photo"
        media_group.append(InputMediaPhoto(media=file_id))

    elif replied_msg.video:
        file_id = replied_msg.video.file_id
        unique_id = replied_msg.video.file_unique_id
        media_type = "🎥 Video"
        media_group.append(InputMediaVideo(media=file_id))

    elif replied_msg.document:
        file_id = replied_msg.document.file_id
        unique_id = replied_msg.document.file_unique_id
        media_type = "📄 Document"
        media_group.append(InputMediaDocument(media=file_id))

    else:
        await update.message.reply_text("❌ No supported media found! Reply to an image, video, or document.")
        return

    # ✅ Forward media to the private channel correctly
    if len(media_group) > 0:
        forwarded_msgs = await context.bot.send_media_group(chat_id=CHANNEL_ID, media=media_group)

        # ✅ Extract the new file ID from the forwarded message
        new_file_id = None
        for msg in forwarded_msgs:
            if msg.photo:
                new_file_id = msg.photo[-1].file_id
            elif msg.video:
                new_file_id = msg.video.file_id
            elif msg.document:
                new_file_id = msg.document.file_id

        # ✅ Store in Database
        if new_file_id:
            file_data = {
                "file_unique_id": unique_id,
                "file_id": new_file_id,
                "type": media_type
            }
            await db.file_storage.update_one(
                {"file_unique_id": unique_id}, 
                {"$set": file_data}, 
                upsert=True
            )

            # ✅ Send the new permanent file ID
            await update.message.reply_text(
                f"✅ **Permanent File ID Stored!**\n\n"
                f"📌 **Type:** {media_type}\n"
                f"📂 **New File ID:** `{new_file_id}`\n"
                f"🆔 **File Unique ID:** `{unique_id}`\n\n"
                f"🔹 **Use this File ID for reliable uploads!**",
                parse_mode="Markdown"
            )
        else:
            await update.message.reply_text("❌ Failed to retrieve new file ID!")

# ✅ Register Command
application.add_handler(CommandHandler("fileid", get_permanent_file_id, block=False))
