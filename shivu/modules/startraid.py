import random
import asyncio
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext, CommandHandler, CallbackQueryHandler
from shivu import application, user_collection, raid_collection, leaderboard_collection, OWNER_ID, sudo_users

# 📌 RARITY BASED STATS
RARITY_STATS = {
    "⛔ Common": {"hp": 3000, "atk": 500, "def": 400},
    "🍀 Rare": {"hp": 6000, "atk": 800, "def": 600},
    "🟡 Sparking": {"hp": 18000, "atk": 1600, "def": 1200},
    "🔮 Limited Edition": {"hp": 36000, "atk": 3200, "def": 2400},
    "🔱 Ultimate": {"hp": 72000, "atk": 6400, "def": 4800},
    "👑 Supreme": {"hp": 144000, "atk": 12800, "def": 9600},
    "⛩️ Celestial": {"hp": 300000, "atk": 20000, "def": 15000}
}

# 📌 ATTACK MOVES
ATTACK_TYPES = {
    "light": {"power": 0.8, "crit_chance": 5, "accuracy": 95, "emoji": "⚡"},
    "heavy": {"power": 1.5, "crit_chance": 15, "accuracy": 75, "emoji": "🔥"},
    "special": {"power": 2.0, "crit_chance": 25, "accuracy": 60, "emoji": "✨"}
}

# 📌 RAID SETTINGS
MAX_ATTACKS_PER_DAY = 9
BASE_BOSS_HP = 500000  # Initial boss HP (scales with players)

# 📌 CURRENT RAID STATE
CURRENT_RAID = {
    "boss_name": "Shenron",
    "boss_hp": 0,  # Default 0 so a new raid can start
    "boss_max_hp": 0,
    "active": False,
    "last_reset": datetime.utcnow()
}

# 📌 START RAID FUNCTION
async def start_raid(update: Update, context: CallbackContext):
    """Starts a new global boss raid."""
    if CURRENT_RAID["active"]:
        await update.message.reply_text("⚠️ A raid is already active!")
        return

    total_players = await user_collection.count_documents({})
    boss_hp = BASE_BOSS_HP + (total_players * 10000)  # Scale boss HP with active players

    CURRENT_RAID.update({
        "boss_name": "Shenron",
        "boss_hp": boss_hp,
        "boss_max_hp": boss_hp,
        "active": True,
        "last_reset": datetime.utcnow()
    })

    await raid_collection.update_one({}, {"$set": CURRENT_RAID}, upsert=True)
    
    keyboard = [[InlineKeyboardButton("⚔️ Attack the Boss", callback_data="attack_menu")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        f"🐉 **A New Boss Appears!** 🐉\n\n"
        f"💀 **Boss:** {CURRENT_RAID['boss_name']}\n"
        f"❤️ **HP:** {CURRENT_RAID['boss_hp']:,}\n"
        f"⚔️ Use the button below to fight!",
        parse_mode="Markdown",
        reply_markup=reply_markup
    )

# 📌 ATTACK MENU FUNCTION
async def attack_menu(update: Update, context: CallbackContext):
    """Shows attack options."""
    query = update.callback_query
    user_id = query.from_user.id

    # ✅ Check if user has attacks left
    user = await user_collection.find_one({"id": user_id}) or {"attacks_left": MAX_ATTACKS_PER_DAY}
    if user.get("attacks_left", 0) <= 0:
        await query.answer("❌ You've used all attacks for today!", show_alert=True)
        return

    keyboard = [
        [InlineKeyboardButton("⚡ Light Attack", callback_data="attack:light")],
        [InlineKeyboardButton("🔥 Heavy Attack", callback_data="attack:heavy")],
        [InlineKeyboardButton("✨ Special Attack", callback_data="attack:special")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.message.edit_text("⚔️ **Choose Your Attack:**", parse_mode="Markdown", reply_markup=reply_markup)

# 📌 ATTACK FUNCTION
async def attack_boss(update: Update, context: CallbackContext):
    """Handles attacks on the boss."""
    query = update.callback_query
    user_id = query.from_user.id
    attack_type = query.data.split(":")[1]

    # ✅ Fetch user and their strongest character
    user = await user_collection.find_one({"id": user_id})
    if not user or not user.get("characters"):
        await query.answer("❌ You have no characters to fight!", show_alert=True)
        return

    character = max(user["characters"], key=lambda c: RARITY_STATS.get(c["rarity"], {}).get("atk", 0))
    char_stats = RARITY_STATS.get(character["rarity"], RARITY_STATS["⛔ Common"])

    # ✅ Get attack details
    attack = ATTACK_TYPES[attack_type]
    damage = int(char_stats["atk"] * attack["power"])

    # 🎯 Accuracy & Critical Hit
    if random.randint(1, 100) > attack["accuracy"]:
        damage = 0  # Attack missed!
    elif random.randint(1, 100) <= attack["crit_chance"]:
        damage *= 5  # Critical Hit!

    # 🔻 Boss HP Reduction
    CURRENT_RAID["boss_hp"] = max(0, CURRENT_RAID["boss_hp"] - damage)

    # 🏆 Update Leaderboard
    await leaderboard_collection.update_one(
        {"user_id": user_id}, {"$inc": {"damage_dealt": damage}}, upsert=True
    )

    # ✅ Deduct Attack
    await user_collection.update_one({"id": user_id}, {"$inc": {"attacks_left": -1}})

    # 🏆 BOSS DEFEATED?
    if CURRENT_RAID["boss_hp"] == 0:
        await query.message.edit_text(f"🏆 **{CURRENT_RAID['boss_name']} has been defeated!** 🏆")
        CURRENT_RAID.update({"active": False, "boss_hp": 0})  # ✅ Reset active state
        await raid_collection.update_one({}, {"$set": CURRENT_RAID})
        return

    # ✅ Update Attack Message
    await query.message.edit_text(
        f"💥 **{query.from_user.first_name} used {attack['emoji']} {attack_type.title()} Attack!**\n"
        f"⚔️ **Damage Dealt:** `{damage}`\n"
        f"🐉 **Boss HP Left:** `{CURRENT_RAID['boss_hp']:,}`",
        parse_mode="Markdown"
    )

# 📌 RESET RAID FUNCTION (OWNER ONLY)
async def reset_raid(update: Update, context: CallbackContext):
    """Manually resets the raid for bot owners."""
    user_id = update.effective_user.id
    if user_id not in sudo_users and user_id != OWNER_ID:
        await update.message.reply_text("🚫 Only bot owners can reset the raid!")
        return

    CURRENT_RAID.update({"active": False, "boss_hp": 0})
    await raid_collection.update_one({}, {"$set": CURRENT_RAID})

    await update.message.reply_text("✅ Raid has been reset! You can now start a new raid.")

# 📌 DAILY RESET FUNCTION
async def reset_attacks():
    """Resets attack counts for all users at midnight UTC."""
    await user_collection.update_many({}, {"$set": {"attacks_left": MAX_ATTACKS_PER_DAY}})
    print("✅ Player attacks have been reset!")

# ✅ REGISTER HANDLERS
application.add_handler(CommandHandler("raid", start_raid))
application.add_handler(CommandHandler("resetraid", reset_raid))  # ✅ NEW COMMAND
application.add_handler(CallbackQueryHandler(attack_menu, pattern="^attack_menu$"))
application.add_handler(CallbackQueryHandler(attack_boss, pattern="^attack:"))

# ✅ SCHEDULE ATTACK RESET DAILY
application.job_queue.run_daily(reset_attacks, time=datetime.utcnow().replace(hour=0, minute=0, second=0))
