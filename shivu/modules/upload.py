import requests
from pymongo import ReturnDocument
from telegram import Update
from telegram.ext import CommandHandler, CallbackContext
from shivu import application, sudo_users, OWNER_ID, collection, db, CHARA_CHANNEL_ID

# ✅ Character Details Mapping
RARITY_MAP = {
    "1": "⛔ Common", "2": "🍀 Rare", "3": "🟣 Extreme", "4": "🟡 Sparking",
    "5": "🔮 Limited Edition", "6": "🔱 Ultimate", "7": "⛩️ Celestial", "8": "👑 Supreme"
}
ANIME_MAP = {
    "1": "🐉 Dragon Ball", "2": "🏴‍☠️ One Piece", "3": "🍃 Naruto",
    "4": "⚔️ Bleach", "5": "⛩️ Demon Slayer", "6": "🛡️ Attack on Titan",
    "7": "👊 Jujutsu Kaisen", "8": "🦸‍♂️ My Hero Academia", "9": "🎯 Hunter x Hunter"
}

async def get_next_sequence_number(sequence_name):
    """Generate a unique character ID."""
    sequence_document = await db.sequences.find_one_and_update(
        {'_id': sequence_name}, {'$inc': {'sequence_value': 1}}, 
        upsert=True, return_document=ReturnDocument.AFTER
    )
    return str(sequence_document['sequence_value']).zfill(3)

async def upload(update: Update, context: CallbackContext):
    """Handles direct character upload."""
    user_id = update.effective_user.id

    # 🔒 **Permission Check**
    if user_id not in sudo_users and user_id != OWNER_ID:
        await update.message.reply_text("🚫 You don't have permission to upload characters!")
        return

    try:
        args = context.args
        message = update.message

        # ✅ **Check if user replied to an image**
        if message.reply_to_message and message.reply_to_message.photo:
            file_id = message.reply_to_message.photo[-1].file_id
        elif len(args) >= 3:
            file_id = args[0]  # File ID given directly
        else:
            await message.reply_text("❌ Reply to an image or provide a valid file ID!")
            return

        # ✅ **Extract character details**
        rarity_input, anime_input = args[-2], args[-1]
        character_name = ' '.join(args[1:-2]).replace('-', ' ').title()

        # ✅ **Validate Rarity**
        rarity = RARITY_MAP.get(rarity_input, None)
        if not rarity:
            await message.reply_text(f"❌ Invalid Rarity! Choose from: {', '.join(RARITY_MAP.values())}")
            return

        # ✅ **Validate Anime**
        anime = ANIME_MAP.get(anime_input, None)
        if not anime:
            await message.reply_text(f"❌ Invalid Anime! Choose from: {', '.join(ANIME_MAP.values())}")
            return

        # ✅ **Generate Character ID**
        char_id = await get_next_sequence_number("character_id")

        # ✅ **Upload to Database**
        character = {
            "file_id": file_id, "name": character_name, "rarity": rarity,
            "anime": anime, "id": char_id
        }

        # ✅ **Send Character Announcement**
        message = await context.bot.send_photo(
            chat_id=CHARA_CHANNEL_ID,
            photo=file_id,
            caption=(
                f"🏆 **New Character Added!**\n\n"
                f"🔥 **Name:** {character_name}\n"
                f"🎖 **Rarity:** {rarity}\n"
                f"🎭 **Anime:** {anime}\n"
                f"🆔 **Character ID:** {char_id}\n\n"
                f"👤 Added by [{update.effective_user.first_name}](tg://user?id={user_id})"
            ),
            parse_mode='Markdown'
        )

        character["message_id"] = message.message_id
        await collection.insert_one(character)

        await update.message.reply_text(f"✅ `{character_name}` successfully added!")

    except Exception as e:
        await update.message.reply_text(f"❌ Upload failed! Error: {str(e)}")

# Function to delete a character
async def delete(update: Update, context: CallbackContext) -> None:
    if update.effective_user.id not in sudo_users and update.effective_user.id != OWNER_ID:
        await update.message.reply_text("🚫 Only bot owners can delete characters!")
        return

    try:
        args = context.args
        if len(args) != 1:
            await update.message.reply_text("❌ Incorrect format! Use: `/delete <Character ID>`")
            return

        character_id = args[0]

        # Find the character in the database
        character = await collection.find_one({"id": character_id})
        if not character:
            await update.message.reply_text("⚠️ Character not found in the database.")
            return

        # Delete the character from the main collection
        await collection.delete_one({"id": character_id})

        # Delete from users' collections
        await user_collection.update_many(
            {}, 
            {"$pull": {"characters": {"id": character_id}}}  # Remove character from all users' collections
        )

        # Try deleting the character's message from the character channel
        try:
            await context.bot.delete_message(chat_id=CHARA_CHANNEL_ID, message_id=character["message_id"])
        except:
            pass  # Ignore if the message doesn't exist

        await update.message.reply_text(f"✅ Character `{character_id}` deleted successfully from database & user collections!")

    except Exception as e:
        await update.message.reply_text(f"❌ Error deleting character: {str(e)}")

# ✅ Function to update character details
async def update(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id

    if user_id not in sudo_users and user_id != OWNER_ID:
        await update.message.reply_text("🚫 You do not have permission to update characters!")
        return

    try:
        args = context.args
        if len(args) < 3:
            await update.message.reply_text("❌ Incorrect format! Use: `/update <ID> <field> <new_value>`")
            return
        
        character_id, field, new_value = args[0], args[1], ' '.join(args[2:])

        valid_fields = ["file_id", "name", "rarity", "anime"]
        if field not in valid_fields:
            await update.message.reply_text(f"❌ Invalid field! Use one of: {', '.join(valid_fields)}")
            return
        
        # Handle rarity separately
        rarity_map = {
            "1": "⛔ Common",
            "2": "🍀 Rare",
            "3": "🟣 Extreme",
            "4": "🟡 Sparking",
            "5": "🔮 Limited Edition",
            "6": "🔱 Ultimate",
            "7": "⛩️ Celestial",
            "8": "👑 Supreme"
        }
        
        if field == "rarity":
            if new_value not in rarity_map:
                await update.message.reply_text("❌ Invalid rarity. Use numbers 1-8.")
                return
            new_value = rarity_map[new_value]

        # Update character in database
        result = await collection.find_one_and_update(
            {'id': character_id}, {'$set': {field: new_value}}
        )

        if result:
            await update.message.reply_text(f"✅ Character `{character_id}` updated successfully!")
        else:
            await update.message.reply_text("❌ Character not found.")

    except Exception as e:
        await update.message.reply_text(f"❌ Update failed! Error: {str(e)}")

# ✅ Add command handlers
application.add_handler(CommandHandler("delete", delete, block=False))
application.add_handler(CommandHandler("update", update, block=False))
application.add_handler(CommandHandler("upload", upload, block=False))
