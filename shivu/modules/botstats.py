from telegram import Update
from telegram.ext import CommandHandler, CallbackContext
from shivu import application, user_collection, collection

async def bot_stats(update: Update, context: CallbackContext):
    """Displays bot statistics, including users, collections, and characters."""
    user_id = update.effective_user.id

    # ✅ **Check if user is authorized**
    if user_id not in sudo_users and user_id != OWNER_ID:
        await update.message.reply_text("🚫 You don't have permission to view bot stats!")
        return

    try:
        # ✅ **Fetch Data**
        total_users = await user_collection.count_documents({})
        total_characters = await collection.count_documents({})
        total_user_collections = await user_collection.aggregate([{"$unwind": "$characters"}, {"$count": "count"}]).to_list(length=1)
        total_collected = total_user_collections[0]["count"] if total_user_collections else 0

        # ✅ **Character Rarity Counts**
        rarity_counts = await collection.aggregate([
            {"$group": {"_id": "$rarity", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}  # Sort by highest count
        ]).to_list(length=None)

        rarity_stats = "\n".join([f"{data['_id']}: `{data['count']}`" for data in rarity_counts])

        # ✅ **Most Collected Rarity**
        most_collected = await user_collection.aggregate([
            {"$unwind": "$characters"},
            {"$group": {"_id": "$characters.rarity", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 1}
        ]).to_list(length=1)

        most_collected_rarity = most_collected[0]["_id"] if most_collected else "Unknown"

        # ✅ **Prepare Statistics Message**
        stats_message = (
            f"📊 <b>Bot Statistics</b>\n"
            f"━━━━━━━━━━━━━━━━━━━\n"
            f"👥 <b>Total Users:</b> <code>{total_users}</code>\n"
            f"🎴 <b>Total Characters:</b> <code>{total_characters}</code>\n"
            f"📦 <b>Total User Collections:</b> <code>{total_collected}</code>\n"
            f"💠 <b>Most Collected Rarity:</b> <code>{most_collected_rarity}</code>\n"
            f"━━━━━━━━━━━━━━━━━━━\n"
            f"🎭 <b>Characters by Rarity:</b>\n{rarity_stats}\n"
            f"━━━━━━━━━━━━━━━━━━━\n"
            f"📌 <i>Updated in real-time!</i>"
        )

        await update.message.reply_text(stats_message, parse_mode="HTML")

    except Exception as e:
        await update.message.reply_text(f"❌ Error fetching bot statistics: {str(e)}")

# ✅ **Register Bot Stats Command**
application.add_handler(CommandHandler("botstats", bot_stats, block=False))
