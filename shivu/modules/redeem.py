import random
import string
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, CallbackContext
from shivu import application, user_collection, db, OWNER_ID, sudo_users, collection, redeem_codes_collection, expired_codes_collection

redeem_codes = db.redeem_codes  # Collection for active redeem codes
expired_codes = db.expired_codes  # Collection for expired codes


# ✅ Valid Rarities
RARITIES = ["⛔ Common", "🍀 Rare", "🟡 Sparking", "🔱 Ultimate", "🔮 Limited Edition"]

# ✅ Generate Unique Code
def generate_unique_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))

# ✅ Admin Command: Generate Codes for Specific Rarities
async def generate_code(update: Update, context: CallbackContext):
    """Only bot owners & sudo users can generate codes."""
    user_id = update.effective_user.id
    if user_id != OWNER_ID and user_id not in sudo_users:
        await update.message.reply_text("❌ You don't have permission to generate redeem codes!")
        return

    # ✅ Ensure Proper Usage
    if len(context.args) < 2 or context.args[0].lower() != "rarity":
        await update.message.reply_text(
            "⚠️ Usage: `/generatecode rarity <rarity_name>`\nExample: `/generatecode rarity 🟡 Sparking`",
            parse_mode="Markdown"
        )
        return

    rarity = ' '.join(context.args[1:])  # Join for multi-word rarities

    # ✅ Validate Rarity
    if rarity not in RARITIES:
        await update.message.reply_text(f"❌ Invalid rarity!\nValid rarities: {', '.join(RARITIES)}")
        return

    # ✅ Generate Unique Code
    code = generate_unique_code()

    # ✅ Store Code in Database
    await redeem_codes.insert_one({"code": code, "rarity": rarity, "used": False})

    # ✅ Inline Button for Redeeming
    keyboard = [[InlineKeyboardButton("🎟 Redeem Now", switch_inline_query_current_chat=f"redeem {code}")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # ✅ Announce Code
    await update.message.reply_text(
        f"✅ **Giveaway Code Generated!**\n"
        f"🎟 **Code:** `{code}`\n"
        f"🎖 **Rarity:** {rarity}\n"
        f"⏳ First person to redeem gets a random `{rarity}` character!",
        parse_mode="Markdown",
        reply_markup=reply_markup
    )

# ✅ User Command: Redeem Code
async def redeem(update: Update, context: CallbackContext):
    """Allows users to redeem a code."""
    user_id = update.effective_user.id

    # ✅ Ensure User Provided a Code
    if len(context.args) < 1:
        await update.message.reply_text("⚠️ Usage: `/redeem <code>`\nExample: `/redeem DBLGSPARK100`", parse_mode="Markdown")
        return

    code = context.args[0].strip().upper()

    # ✅ Check if Code Exists
    code_data = await redeem_codes.find_one({"code": code, "used": False})
    if not code_data:
        await update.message.reply_text("❌ Invalid or expired redeem code!")
        return

    # ✅ Mark Code as Used
    await redeem_codes.update_one({"code": code}, {"$set": {"used": True}})
    await expired_codes.insert_one(code_data)  # Store expired code

    # ✅ Fetch a Random Character from the Specified Rarity
    rarity = code_data["rarity"]
    character = await collection.find_one({"rarity": rarity})

    if not character:
        await update.message.reply_text(f"❌ No characters found in `{rarity}` rarity!")
        return

    # ✅ Add Character to User's Collection
    await user_collection.update_one({"id": user_id}, {"$push": {"characters": character}}, upsert=True)

    # ✅ Confirmation Message
    await update.message.reply_text(
        f"🎉 **Code Redeemed Successfully!**\n"
        f"🎖 **You received a random `{rarity}` character!**\n"
        f"🎴 **Character:** {character['name']}\n"
        "🔹 Check your `/collection`!",
        parse_mode="Markdown"
    )

# ✅ Register Handlers
application.add_handler(CommandHandler("generatecode", generate_code, block=False))
application.add_handler(CommandHandler("redeem", redeem, block=False))
