from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, CallbackContext, CallbackQueryHandler
from shivu import application, user_collection, collection

# 📌 Rarity Sorting Order (Descending)
RARITY_PRIORITY = {
    "⛩️ Celestial": 7,
    "👑 Supreme": 6,
    "🔱 Ultimate": 5,
    "🔮 Limited Edition": 4,
    "🟡 Sparking": 3,
    "🍀 Rare": 2,
    "⛔ Common": 1
}

MAX_TEAM_SIZE = 4 # Users can select 4 characters

# 📌 VIEW TEAM COMMAND
async def view_team(update: Update, context: CallbackContext):
    """Shows user's selected team."""
    user_id = update.effective_user.id
    user = await user_collection.find_one({'id': user_id})

    if not user or "team" not in user or not user["team"]:
        await update.message.reply_text("❌ You haven't set a team yet! Use /maketeam to create one.")
        return

    team_message = "⚔️ <b>Your Current Team</b> ⚔️\n━━━━━━━━━━━━━━━━━━━━\n"
    
    for i, char in enumerate(user["team"], 1):
        team_message += f"{i}. {char['rarity']} {char['name']} (❤️ {char['hp']})\n"

    keyboard = [[InlineKeyboardButton("🔄 Change Team", callback_data="change_team")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(team_message, parse_mode="HTML", reply_markup=reply_markup)

# 📌 MAKE TEAM FUNCTION
async def make_team(update: Update, context: CallbackContext, page=0, query=None):
    """Allows users to select characters for their team."""
    user_id = update.effective_user.id
    user = await user_collection.find_one({'id': user_id})

    if not user or not user.get("characters"):
        await update.message.reply_text("❌ You have no characters to form a team!")
        return

    # ✅ Sort characters by rarity (strongest first)
    characters = sorted(user["characters"], key=lambda c: RARITY_PRIORITY.get(c["rarity"], 0), reverse=True)
    
    # ✅ Pagination (5 characters per page)
    per_page = 10
    total_pages = max(1, -(-len(characters) // per_page))  # Ceiling division
    page = max(0, min(page, total_pages - 1))
    start, end = page * per_page, (page + 1) * per_page
    paginated_chars = characters[start:end]

    # ✅ Display Characters
    team_message = f"⚔️ <b>Select 4 Characters for Your Team</b> ⚔️\nPage {page+1}/{total_pages}\n━━━━━━━━━━━━━━━━━━━━\n"
    keyboard = []

    for char in paginated_chars:
        keyboard.append([InlineKeyboardButton(f"{char['rarity']} {char['name']}", callback_data=f"select_team:{char['id']}")])

    # ✅ Pagination Buttons
    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton("⬅️ Prev", callback_data=f"team_page:{page-1}"))
    if page < total_pages - 1:
        nav_buttons.append(InlineKeyboardButton("Next ➡️", callback_data=f"team_page:{page+1}"))
    
    if nav_buttons:
        keyboard.append(nav_buttons)

    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if query:
        await query.message.edit_text(team_message, parse_mode="HTML", reply_markup=reply_markup)
    else:
        await update.message.reply_text(team_message, parse_mode="HTML", reply_markup=reply_markup)

# 📌 SELECT CHARACTER FOR TEAM
async def select_team(update: Update, context: CallbackContext):
    """Handles team selection logic."""
    query = update.callback_query
    user_id = query.from_user.id
    char_id = query.data.split(":")[1]

    # ✅ Fetch character
    user = await user_collection.find_one({'id': user_id})
    character = next((c for c in user["characters"] if c["id"] == char_id), None)

    if not character:
        await query.answer("❌ Character not found!", show_alert=True)
        return

    # ✅ Fetch existing team
    team = user.get("team", [])

    # ✅ Ensure MAX_TEAM_SIZE
    if len(team) >= MAX_TEAM_SIZE:
        await query.answer("❌ You can only select 3 characters!", show_alert=True)
        return

    # ✅ Add character with HP, ATK, DEF
    character_stats = {
        "id": character["id"],
        "name": character["name"],
        "rarity": character["rarity"],
        "hp": RARITY_PRIORITY.get(character["rarity"], 3000) * 100,
        "atk": RARITY_PRIORITY.get(character["rarity"], 3000) * 1.5,
        "def": RARITY_PRIORITY.get(character["rarity"], 3000) * 1.2
    }
    team.append(character_stats)

    await user_collection.update_one({'id': user_id}, {'$set': {'team': team}})

    if len(team) == MAX_TEAM_SIZE:
        await query.message.edit_text("✅ Team selection complete! Use /myteam to view your team.")
    else:
        await query.answer(f"✅ {character['name']} added! ({len(team)}/3)", show_alert=True)

# 📌 CHANGE TEAM
async def change_team(update: Update, context: CallbackContext):
    """Resets team and allows re-selection."""
    user_id = update.effective_user.id
    await user_collection.update_one({'id': user_id}, {'$set': {'team': []}})
    await make_team(update, context)

# 📌 HANDLE PAGINATION
async def team_pagination(update: Update, context: CallbackContext):
    """Handles team pagination properly."""
    query = update.callback_query
    page = int(query.data.split(":")[1])
    await make_team(update, context, page=page, query=query)

# ✅ REGISTER HANDLERS
application.add_handler(CommandHandler("myteam", view_team, block=False))
application.add_handler(CommandHandler("maketeam", make_team, block=False))
application.add_handler(CommandHandler("changeteam", change_team, block=False))
application.add_handler(CallbackQueryHandler(select_team, pattern="^select_team:", block=False))
application.add_handler(CallbackQueryHandler(team_pagination, pattern="^team_page:", block=False))
application.add_handler(CallbackQueryHandler(change_team, pattern="^change_team$", block=False))
