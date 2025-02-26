from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, CallbackContext, CallbackQueryHandler
from shivu import application, user_collection, collection

# 🛡 **Character Stats Based on Rarity**
RARITY_STATS = {
    "⛔ Common": {"hp": 3000, "atk": 500, "def": 400},
    "🍀 Rare": {"hp": 6000, "atk": 800, "def": 600},
    "🟡 Sparking": {"hp": 18000, "atk": 1600, "def": 1200},
    "🔮 Limited Edition": {"hp": 36000, "atk": 3200, "def": 2400},
    "🔱 Ultimate": {"hp": 72000, "atk": 6400, "def": 4800},
    "👑 Supreme": {"hp": 144000, "atk": 12800, "def": 9600},
    "⛩️ Celestial": {"hp": 300000, "atk": 20000, "def": 15000},
}

async def maketeam(update: Update, context: CallbackContext) -> None:
    """Allows users to select up to 3 characters for their team."""
    user_id = update.effective_user.id
    user = await user_collection.find_one({'id': user_id})

    if not user or not user.get("characters"):
        await update.message.reply_text("❌ **You don't have any characters to form a team!**", parse_mode="Markdown")
        return

    # Fetch user's characters
    characters = user["characters"]
    keyboard = []
    
    for char in characters[:10]:  # Show first 10 characters
        keyboard.append([InlineKeyboardButton(f"{char['name']} [{char['rarity']}]", callback_data=f"teamselect:{char['id']}")])

    keyboard.append([InlineKeyboardButton("✅ Finish Selection", callback_data="teamconfirm")])
    await update.message.reply_text("🎖 **Select 3 characters for your team:**", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

# 🛡 **Handle Character Selection**
async def teamselect(update: Update, context: CallbackContext) -> None:
    """Handles character selection for the team."""
    query = update.callback_query
    user_id = query.from_user.id
    character_id = query.data.split(":")[1]

    user = await user_collection.find_one({'id': user_id})
    if not user:
        await query.answer("❌ You don't have any characters!", show_alert=True)
        return

    # ✅ Get selected character
    character = next((c for c in user["characters"] if c["id"] == character_id), None)
    if not character:
        await query.answer("❌ Invalid character!", show_alert=True)
        return

    # ✅ Ensure the team does not exceed 3 members
    team = user.get("team", [])
    if len(team) >= 3:
        await query.answer("❌ You can only select 3 characters!", show_alert=True)
        return

    # ✅ Add character to team if not already selected
    if character in team:
        await query.answer("⚠️ Character already selected!", show_alert=True)
    else:
        team.append(character)
        await user_collection.update_one({"id": user_id}, {"$set": {"team": team}})
        await query.answer(f"✅ {character['name']} added to your team!")

async def teamconfirm(update: Update, context: CallbackContext) -> None:
    """Finalizes team selection and calculates stats."""
    query = update.callback_query
    user_id = query.from_user.id
    user = await user_collection.find_one({'id': user_id})

    team = user.get("team", [])
    if len(team) < 1:
        await query.answer("❌ Select at least 1 character!", show_alert=True)
        return

    # ✅ Calculate Total Team Stats
    total_hp = sum(RARITY_STATS[c['rarity']]["hp"] for c in team)
    total_atk = sum(RARITY_STATS[c['rarity']]["atk"] for c in team)
    total_def = sum(RARITY_STATS[c['rarity']]["def"] for c in team)

    await user_collection.update_one({"id": user_id}, {"$set": {"team_stats": {"hp": total_hp, "atk": total_atk, "def": total_def}}})

    # ✅ Show Team Stats
    message = f"✅ **Your Team is Ready!**\n\n" \
              f"🛡 **Total HP:** {total_hp}\n" \
              f"⚔ **Total Attack:** {total_atk}\n" \
              f"🛡 **Total Defense:** {total_def}\n\n" \
              f"⚔ Use `/startraid` to battle bosses!"
    
    await query.message.edit_text(message, parse_mode="Markdown")

# ✅ **Command Handlers**
application.add_handler(CommandHandler("maketeam", maketeam, block=False))
application.add_handler(CallbackQueryHandler(teamselect, pattern="^teamselect:", block=False))
application.add_handler(CallbackQueryHandler(teamconfirm, pattern="^teamconfirm$", block=False))
