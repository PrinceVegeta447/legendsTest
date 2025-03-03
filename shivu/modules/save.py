from telegram import Update
from telegram.ext import CommandHandler, CallbackContext
from shivu import application, collection  # Your MongoDB collection

async def save_photo(update: Update, context: CallbackContext):
    """Saves a new photo's file_id and file_unique_id."""
    if not update.message.reply_to_message or not update.message.reply_to_message.photo:
        await update.message.reply_text("❌ Reply to a photo to save it!")
        return

    photo = update.message.reply_to_message.photo[-1]  # Get the highest resolution photo
    file_id = photo.file_id
    unique_id = photo.file_unique_id

    # Check if already stored
    existing = await collection.find_one({"file_unique_id": unique_id})
    if existing:
        await update.message.reply_text("✅ This image is already stored!")
        return

    # Save to database
    await collection.insert_one({"file_id": file_id, "file_unique_id": unique_id})
    await update.message.reply_text("✅ Image saved permanently!")

async def send_photo(update: Update, context: CallbackContext):
    """Sends a stored photo using its file_unique_id."""
    if len(context.args) != 1:
        await update.message.reply_text("❌ Usage: `/send <file_unique_id>`")
        return

    unique_id = context.args[0]

    # Find stored image
    image = await collection.find_one({"file_unique_id": unique_id})
    if not image:
        await update.message.reply_text("❌ Image not found in database!")
        return

    try:
        await update.message.reply_photo(photo=image["file_id"])
    except:
        await update.message.reply_text("⚠️ File ID expired! Please re-upload.")

application.add_handler(CommandHandler("send", send_photo, block=False))
application.add_handler(CommandHandler("save", save_photo, block=False))
