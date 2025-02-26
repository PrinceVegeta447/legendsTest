from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, CallbackContext
from shivu import user_collection, application, OWNER_ID, sudo_users

async def inventory(update: Update, context: CallbackContext) -> None:
    """Displays the user's inventory with enhanced UI."""
    user_id = update.effective_user.id
    user = await user_collection.find_one({'id': user_id}) or {}

    # ✅ Ensure inventory exists
    user.setdefault('tokens', 0)
    user.setdefault('diamonds', 0)
    user.setdefault('summon_tickets', 0)
    user.setdefault('exclusive_tokens', 0)

    tokens = user['tokens']
    diamonds = user['diamonds']
    summon_tickets = user['summon_tickets']
    exclusive_tokens = user['exclusive_tokens']

    # 🎒 **Enhanced Inventory Message**
    inventory_message = (
        f"🎒 <b>{update.effective_user.first_name}'s Inventory</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"💴 <b>Tokens:</b> <code>{tokens:,}</code>\n"
        f"💎 <b>Diamonds:</b> <code>{diamonds:,}</code>\n"
        f"🎟 <b>Summon Tickets:</b> <code>{summon_tickets:,}</code>\n"
        f"🛡️ <b>Exclusive Tokens:</b> <code>{exclusive_tokens:,}</code>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🔹 Earn more rewards by guessing characters!\n"
    )

    # 🔘 **Inline Buttons for Better Navigation**
    keyboard = [
        [InlineKeyboardButton("🏪 Open Shop", callback_data="open_shop")],
        [InlineKeyboardButton("🏆 Top Players", callback_data="top_players")]
    ]

    await update.message.reply_text(
        inventory_message,
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def modify_inventory(update: Update, context: CallbackContext, add: bool) -> None:
    """Allows the owner or sudo users to add/remove items from a user's inventory."""
    user_id = update.effective_user.id

    if user_id not in sudo_users and user_id != OWNER_ID:
        await update.message.reply_text("🚫 You don't have permission to modify inventories!")
        return

    try:
        args = context.args
        if len(args) != 3:
            await update.message.reply_text(
                "❌ <b>Usage:</b>\n"
                "➤ `/additem <user_id> <token/diamonds/ticket/etoken> <amount>`\n"
                "➤ `/removeitem <user_id> <token/diamonds/ticket/etoken> <amount>`",
                parse_mode="HTML"
            )
            return

        target_id = int(args[0])  
        item = args[1].lower()
        amount = int(args[2])

        item_map = {
            "tokens": "tokens",
            "diamonds": "diamonds",
            "ticket": "summon_tickets",
            "etoken": "exclusive_tokens"
        }

        if item not in item_map:
            await update.message.reply_text("❌ Invalid item! Use `token`, `diamond`, `ticket`, or `etoken`.", parse_mode="HTML")
            return

        field = item_map[item]

        user = await user_collection.find_one({'id': target_id}) or {}
        user.setdefault(field, 0)

        new_value = max(0, user[field] + (amount if add else -amount))

        await user_collection.update_one({'id': target_id}, {'$set': {field: new_value}})

        action = "added to" if add else "removed from"
        await update.message.reply_text(
            f"✅ <b>{amount:,} {item.capitalize()} {action} user {target_id}'s inventory!</b>", 
            parse_mode="HTML"
        )

    except ValueError:
        await update.message.reply_text("❌ Invalid number format! Please enter a valid amount.", parse_mode="HTML")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}", parse_mode="HTML")

async def open_shop(update: Update, context: CallbackContext) -> None:
    """Displays the shop where users can spend tokens."""
    query = update.callback_query
    await query.answer()

    shop_message = (
        "🏪 <b>Welcome to the Shop!</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "💎 **Diamonds:** 1000 Tokens 💰\n"
        "🎟 **Summon Ticket:** 1500 Tokens 🎫\n"
        "🛡️ **Exclusive Token:** 500 Tokens 🔥\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "Use `/buy <item>` to purchase!"
    )

    await query.message.edit_text(shop_message, parse_mode="HTML")

async def top_players(update: Update, context: CallbackContext) -> None:
    """Displays top players based on their tokens."""
    query = update.callback_query
    await query.answer()

    # ✅ Fetch top 5 players sorted by tokens
    top_users = await user_collection.find({}, {"id": 1, "tokens": 1, "first_name": 1}).sort("tokens", -1).limit(5).to_list(length=5)

    if not top_users:
        await query.message.edit_text("❌ No players found!", parse_mode="HTML")
        return

    leaderboard = "🏆 <b>Top Players by Tokens</b>\n━━━━━━━━━━━━━━━━━━━━━━\n"
    for rank, user in enumerate(top_users, 1):
        leaderboard += f"{rank}. {user.get('first_name', 'Unknown')} - 💰 {user['tokens']:,} Tokens\n"

    await query.message.edit_text(leaderboard, parse_mode="HTML")

# ✅ Command Handlers
application.add_handler(CommandHandler("inventory", inventory, block=False))
application.add_handler(CommandHandler("additem", add_inventory, block=False))
application.add_handler(CommandHandler("removeitem", remove_inventory, block=False))
application.add_handler(CallbackQueryHandler(open_shop, pattern="open_shop", block=False))
application.add_handler(CallbackQueryHandler(top_players, pattern="top_players", block=False))
