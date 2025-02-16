import asyncio
import time
import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, CallbackContext
from shivu import application, user_collection, collection

# 📌 Claim Settings
MAX_CLAIMS = 1  # Users can claim once per day
COOLDOWN_TIME = 24 * 60 * 60  # 24-hour cooldown
SUPPORT_GROUP_ID = -1002483506913  # Replace with actual group ID
SUPPORT_GROUP_LINK = "https://t.me/CollectYourLegends"  # Replace with actual group link
GIF_FILE_ID = "BAACAgUAAyEFAASFUB9IAAIQAAFnsKpbDDyBb9emePMuEFN7gugV2QACIhMAApS5iFUcNzRBeFCYwTYE"

# 🚫 **Rarities NOT allowed in `/claim`**
FORBIDDEN_RARITIES = ["👑 Supreme", "⛩️ Celestial"]

async def claim(update: Update, context: CallbackContext) -> None:
    """Allows users to claim a random character if they are in the support group."""
    user_id = update.effective_user.id

    # ✅ Check if user is in support group
    try:
        chat_member = await context.bot.get_chat_member(SUPPORT_GROUP_ID, user_id)
        if chat_member.status not in ["member", "administrator", "creator"]:
            raise Exception  # Not a member
    except:
        # ✅ Send Inline Button to Join Group
        keyboard = [[InlineKeyboardButton("🔹 Join Our Group", url=SUPPORT_GROUP_LINK)]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            "❌ You must join the Group to claim a character!\n"
            "🔹 Click the button below to join and try again.",
            reply_markup=reply_markup
        )
        return

    # ✅ Fetch or Register User in Database
    user = await user_collection.find_one({"id": user_id})
    if not user:
        user = {
            "id": user_id,
            "username": update.effective_user.username,
            "first_name": update.effective_user.first_name,
            "characters": [],
            "claims": 0,
            "last_claim": 0,
            "coins": 0,
            "chrono_crystals": 0
        }
        await user_collection.insert_one(user)

    # ✅ Fetch Claim Data
    claims = user.get("claims", 0)
    last_claim = user.get("last_claim", 0)
    current_time = time.time()

    # ✅ **Check Claim Limits**
    cooldown_remaining = COOLDOWN_TIME - (current_time - last_claim)

    if claims >= MAX_CLAIMS or cooldown_remaining > 0:
        hours = int(cooldown_remaining // 3600)
        minutes = int((cooldown_remaining % 3600) // 60)
        seconds = int(cooldown_remaining % 60)

        await update.message.reply_text(
            f"⏳ You can claim again in {hours}h {minutes}m {seconds}s!"
        )
        return

    # ✅ Fetch a valid character (Exclude Forbidden Rarities)
    while True:
        total_characters = await collection.count_documents({})
        if total_characters == 0:
            await update.message.reply_text("❌ No characters available to claim!")
            return

        random_character = await collection.find_one({}, skip=random.randint(0, total_characters - 1))

        if random_character and random_character["rarity"] not in FORBIDDEN_RARITIES:
            break  # Found a valid character

    # ✅ Send GIF animation
    gif_message = await update.message.reply_animation(animation=GIF_FILE_ID, caption="✨ Claiming a character...")

    # ✅ **Wait for 7 seconds before proceeding**
    await asyncio.sleep(7)

    # ✅ **Ensure claimed character is saved correctly**
    await user_collection.update_one(
        {"id": user_id},
        {
            "$push": {"characters": random_character},
            "$set": {"last_claim": current_time},
            "$inc": {"claims": 1}
        }
    )

    # ✅ Prepare Character Message
    char_name = random_character["name"]
    char_rarity = random_character.get("rarity", "Unknown")
    char_file_id = random_character.get("file_id")
    char_img_url = random_character.get("img_url")

    character_message = (
        f"🎉 <b>You have claimed:</b>\n"
        f"🎴 <b>{char_name}</b>\n"
        f"🎖 <b>Rarity:</b> {char_rarity}\n"
        "🔹 Use `/collection` to view your collection!"
    )

    # ✅ Delete GIF after the delay
    await gif_message.delete()

    # ✅ Send Character Image After Animation
    if char_file_id:
        await update.message.reply_photo(photo=char_file_id, caption=character_message, parse_mode="HTML")
    elif char_img_url:
        await update.message.reply_photo(photo=char_img_url, caption=character_message, parse_mode="HTML")
    else:
        await update.message.reply_text(character_message, parse_mode="HTML")

# ✅ Register Handler
application.add_handler(CommandHandler("claim", claim, block=False))
