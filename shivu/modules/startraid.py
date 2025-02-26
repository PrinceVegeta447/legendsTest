import asyncio
import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, CallbackContext, CallbackQueryHandler
from shivu import application, user_collection, boss_collection, db

# ⚔ **Boss Config**
BOSS_HP_BASE = 500000  # Base HP (scales with players)
BOSS_DEFENSE = 15000  # Default Boss Defense
BOSS_ATTACK = 20000  # Boss Counterattack Power
MAX_FIGHTS_PER_DAY = 3  # Max attacks per user per day

# 🛡 **Boss Moves**
BOSS_MOVES = [
    "💥 **Boss unleashes a devastating punch!**",
    "🔥 **Boss charges up and blasts energy waves!**",
    "⚡ **Boss teleports behind and lands a critical hit!**",
    "🌪 **Boss creates a massive shockwave attack!**"
]

async def start_raid(update: Update, context: CallbackContext) -> None:
    """Starts a boss fight if the user has a team set up."""
    user_id = update.effective_user.id
    user = await user_collection.find_one({'id': user_id})

    if not user or "team" not in user or len(user["team"]) == 0:
        await update.message.reply_text("❌ **You must first select a team using /maketeam!**", parse_mode="Markdown")
        return

    # ✅ Check if the user has remaining fights for the day
    fight_data = await db.raid_fights.find_one({'id': user_id}) or {"count": 0}
    if fight_data["count"] >= MAX_FIGHTS_PER_DAY:
        await update.message.reply_text("❌ **You have used all 3 chances today! Come back tomorrow.**", parse_mode="Markdown")
        return

    # ✅ Fetch or create Boss
    boss = await boss_collection.find_one({"active": True})
    if not boss:
        boss_hp = BOSS_HP_BASE + (len(await user_collection.distinct("id")) * 20000)  # Scale HP based on players
        boss = {"hp": boss_hp, "defense": BOSS_DEFENSE, "attack": BOSS_ATTACK, "active": True}
        await boss_collection.insert_one(boss)
    
    keyboard = [
        [InlineKeyboardButton("⚔ Quick Attack", callback_data=f"raidattack:{user_id}:quick")],
        [InlineKeyboardButton("🔥 Power Strike", callback_data=f"raidattack:{user_id}:power")],
        [InlineKeyboardButton("💥 Ultimate Blast", callback_data=f"raidattack:{user_id}:ultimate")],
    ]
    
    await update.message.reply_text(
        "🔥 **Boss Battle Started!**\n\n"
        "🎭 Select your attack:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

async def raid_attack(update: Update, context: CallbackContext) -> None:
    """Handles attack selection and executes damage calculation."""
    query = update.callback_query
    _, user_id, attack_type = query.data.split(":")
    user_id = int(user_id)

    user = await user_collection.find_one({'id': user_id})
    if not user or "team" not in user or len(user["team"]) == 0:
        await query.answer("❌ You have no team!", show_alert=True)
        return

    team_stats = user["team_stats"]
    boss = await boss_collection.find_one({"active": True})
    if not boss:
        await query.message.edit_text("❌ **No active boss battle!**", parse_mode="Markdown")
        return

    # ✅ Attack Power Calculation
    attack_multiplier = {"quick": 0.7, "power": 1.2, "ultimate": 2.0}
    damage_dealt = int(team_stats["atk"] * attack_multiplier.get(attack_type, 1))
    
    # ✅ Boss Counterattack
    boss_damage = max(5000, boss["attack"] - team_stats["def"] // 2)
    
    # ✅ Update Boss HP
    boss["hp"] = max(0, boss["hp"] - damage_dealt)
    await boss_collection.update_one({"active": True}, {"$set": {"hp": boss["hp"]}})

    # ✅ Track User Fights
    await db.raid_fights.update_one({"id": user_id}, {"$inc": {"count": 1}}, upsert=True)

    if boss["hp"] <= 0:
        await boss_collection.update_one({"active": True}, {"$set": {"active": False}})
        await query.message.edit_text(
            f"🎉 **You defeated the Boss!**\n\n"
            f"🔥 **Final Attack:** {damage_dealt} DMG\n"
            f"💀 **Boss has fallen!**",
            parse_mode="Markdown"
        )
    else:
        # ✅ Select Random Boss Attack Animation
        boss_move = random.choice(BOSS_MOVES)

        await query.message.edit_text(
            f"⚔ **Battle Update!**\n\n"
            f"🛡 **Boss HP:** {boss['hp']}\n"
            f"💥 **You Dealt:** {damage_dealt} DMG\n"
            f"☠️ **Boss Counterattack:** {boss_damage} DMG\n\n"
            f"{boss_move}",
            parse_mode="Markdown"
        )

# ✅ **Command Handlers**
application.add_handler(CommandHandler("startraid", start_raid, block=False))
application.add_handler(CallbackQueryHandler(raid_attack, pattern="^raidattack:", block=False))
