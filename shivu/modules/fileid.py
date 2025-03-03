from telegram import Update
from telegram.ext import CommandHandler, CallbackContext
from shivu import application, OWNER_ID, sudo_users, collection

CHANNEL_ID = -1002327002224

async def get_permanent_file_id(update: Update, context: CallbackContext) -> None:
    """Forwards media to a private channel and stores the permanent file ID."""
    user_id = update.effective_user.id

    # ✅ Check permissions
    if user_id not in sudo_users and user_id != OWNER_ID:
        await update.message.reply_text("🚫 You don't have permission to extract file IDs!")
        return

    # ✅ Ensure user replied to a media message
    if not update.message.reply_to_message:
        await update.message.reply_text("❌ Reply to an image, video, or document with `/fileid` to extract the file_id!")
        return

    replied_msg = update.message.reply_to_message

    # ✅ Forward the media to the channel
    forwarded_msg = await replied_msg.forward(chat_id=CHANNEL_ID)
    media_type = None
    file_id = None
    file_unique_id = None

    if forwarded_msg.photo:
        file_id = forwarded_msg.photo[-1].file_id
        file_unique_id = forwarded_msg.photo[-1].file_unique_id
        media_type = "🖼 Photo"
    elif forwarded_msg.video:
        file_id = forwarded_msg.video.file_id
        file_unique_id = forwarded_msg.video.file_unique_id
        media_type = "🎥 Video"
    elif forwarded_msg.document:
        file_id = forwarded_msg.document.file_id
        file_unique_id = forwarded_msg.document.file_unique_id
        media_type = "📄 Document"
    elif forwarded_msg.animation:
        file_id = forwarded_msg.animation.file_id
        file_unique_id = forwarded_msg.animation.file_unique_id
        media_type = "🎞 GIF"
    else:
        await update.message.reply_text("❌ No supported media found! Reply to an image, video, or document.")
        return

    # ✅ Store in Database
    media_data = {
        "file_id": file_id,
        "file_unique_id": file_unique_id,
        "type": media_type,
        "uploaded_by": user_id
    }
    await collection.insert_one(media_data)

    # ✅ Send the extracted File ID
    await update.message.reply_text(
        f"✅ **Extracted & Stored Permanent File ID**\n\n"
        f"📌 **Type:** {media_type}\n"
        f"📂 **Permanent File ID:** `{file_id}`\n"
        f"🆔 **Unique ID:** `{file_unique_id}`\n\n"
        f"🔹 **Use Unique ID to Retrieve a Fresh File ID Anytime!**",
        parse_mode="Markdown"
    )

# ✅ Command to Retrieve File ID from Unique ID
async def fetch_file_id(update: Update, context: CallbackContext) -> None:
    """Retrieves a fresh file_id using file_unique_id."""
    if len(context.args) != 1:
        await update.message.reply_text("❌ Usage: `/fetch <file_unique_id>`")
        return

    unique_id = context.args[0]
    media = await collection.find_one({"file_unique_id": unique_id})

    if not media:
        await update.message.reply_text("❌ No file found with this unique ID!")
        return

    await update.message.reply_text(
        f"✅ **Fetched File ID**\n\n"
        f"📌 **Type:** {media['type']}\n"
        f"📂 **File ID:** `{media['file_id']}`\n"
        f"🆔 **Unique ID:** `{media['file_unique_id']}`\n\n"
        f"🔹 **This File ID can expire, but you can always re-fetch using the Unique ID!**",
        parse_mode="Markdown"
    )

# ✅ Register Handlers
application.add_handler(CommandHandler("fileid", get_permanent_file_id, block=False))
application.add_handler(CommandHandler("fetch", fetch_file_id, block=False))
