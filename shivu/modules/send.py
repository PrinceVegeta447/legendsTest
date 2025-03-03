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
