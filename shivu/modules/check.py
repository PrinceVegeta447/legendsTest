from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, CallbackContext, CallbackQueryHandler
from shivu import application, collection, user_collection

async def check_character(update: Update, context: CallbackContext) -> None:
    """Displays character details and collector buttons."""
    if len(context.args) != 1:
        await update.message.reply_text("❌ **Usage:** `/check <character_id>`", parse_mode="Markdown")
        return

    character_id = context.args[0]
    character = await collection.find_one({"id": character_id})

    if not character:
        await update.message.reply_text("❌ **Character not found!**", parse_mode="Markdown")
        return

    # ✅ Extract Character Details
    name = character["name"]
    rarity_text = character.get("rarity", "❓ Unknown Rarity")  
    anime_text = character.get("anime", "❓ Unknown Anime")

    message = (
        f"🎴 <b>Character:</b> {name}\n"
        f"🎖 <b>Rarity:</b> {rarity_text}\n"
        f"📜 <b>Anime:</b> {anime_text}"
    )

    # ✅ Buttons: Top Collectors | Show Collectors Here
    keyboard = [
        [InlineKeyboardButton("🏆 Top Collectors", callback_data=f"show_top_collectors:{character_id}")],
        [InlineKeyboardButton("📍 Show Collectors Here", callback_data=f"show_local_collectors:{character_id}")]
    ]

    file_id = character.get("file_id")
    
    if file_id:
        await update.message.reply_photo(
            photo=file_id,
            caption=message,
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    else:
        await update.message.reply_text(message, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))

async def show_top_collectors(update: Update, context: CallbackContext) -> None:
    """Displays top collectors for a specific character globally."""
    query = update.callback_query
    await query.answer()  # ✅ Ensure button is responsive
    _, character_id = query.data.split(":")  

    # ✅ Fetch Top Collectors
    pipeline = [
        {"$match": {"characters.id": character_id}},  
        {"$unwind": "$characters"},  
        {"$match": {"characters.id": character_id}},  
        {"$group": {
            "_id": "$id",
            "count": {"$sum": 1},  # ✅ Each character counts as one occurrence
            "first_name": {"$first": "$first_name"}  
        }},
        {"$sort": {"count": -1}},  
        {"$limit": 5}  
    ]

    collectors = await user_collection.aggregate(pipeline).to_list(length=5)

    if not collectors:
        await query.answer("❌ No collectors found!", show_alert=True)
        return

    # ✅ Format the Message
    message = "🏆 <b>Top Collectors for this Character:</b>\n\n"
    for i, user in enumerate(collectors, 1):
        message += f"{i}. {user['first_name']} - <b>[{user['count']}]</b> \n"

    await query.message.edit_text(message, parse_mode="HTML")

async def show_local_collectors(update: Update, context: CallbackContext) -> None:
    """Displays collectors of a specific character in the current group."""
    query = update.callback_query
    await query.answer()  # ✅ Ensure button is responsive
    _, character_id = query.data.split(":")
    group_id = query.message.chat.id

    # ✅ Fetch all users who own the character
    pipeline = [
        {"$match": {"characters.id": character_id}},  
        {"$unwind": "$characters"},  
        {"$match": {"characters.id": character_id}},  
        {"$group": {
            "_id": "$id",
            "count": {"$sum": 1},  # ✅ Each character counts as one occurrence
            "first_name": {"$first": "$first_name"}
        }},
        {"$sort": {"count": -1}},  
        {"$limit": 10}  
    ]

    collectors = await user_collection.aggregate(pipeline).to_list(length=10)

    if not collectors:
        await query.answer("❌ No collectors found in this group!", show_alert=True)
        return

    # ✅ Filter Active Members in the Group
    active_collectors = []
    for user in collectors:
        user_id = int(user["_id"])
        try:
            chat_member = await context.bot.get_chat_member(group_id, user_id)
            if chat_member.status in ["member", "administrator", "creator"]:  
                active_collectors.append(user)
        except:
            pass  

    if not active_collectors:
        await query.answer("❌ No active collectors in this group!", show_alert=True)
        return

    # ✅ Format the Message
    message = "📍 <b>Collectors in this Group:</b>\n\n"
    for i, user in enumerate(active_collectors[:5], 1):  
        message += f"{i}. {user['first_name']} - <b>[{user['count']}]</b> \n"

    await query.message.edit_text(message, parse_mode="HTML")

# ✅ Register Handlers
application.add_handler(CommandHandler("check", check_character, block=False))
application.add_handler(CallbackQueryHandler(show_top_collectors, pattern="^show_top_collectors:", block=False))
application.add_handler(CallbackQueryHandler(show_local_collectors, pattern="^show_local_collectors:", block=False))
