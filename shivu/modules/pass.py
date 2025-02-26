import time
import random
from telegram import Update
from telegram.ext import CommandHandler, CallbackContext
from shivu import application, user_collection, collection
from datetime import datetime, timedelta

# 📌 Pass Details
WEEKLY_PASS_PRICE = 8000  # Price in Diamonds
WEEKLY_PASS_DURATION = 7 * 86400  # 7 Days in seconds
WEEKLY_PASS_REWARDS = {
    0: {"tokens": 20000, "diamonds": 120, "rarity": "🍀 Rare"},
    1: {"tokens": 15000, "diamonds": 100, "rarity": "🍀 Rare"},
    2: {"tokens": 25000, "diamonds": 180, "rarity": "🟡 Sparking"},
    3: {"tokens": 15000, "diamonds": 120, "rarity": "🟡 Sparking"},
    4: {"tokens": 20000, "diamonds": 150, "rarity": "🟡 Sparking"},
    5: {"tokens": 25000, "diamonds": 250, "rarity": "🟡 Sparking"},
    6: {"tokens": 50000, "diamonds": 400, "rarity": "🔮 Limited Edition"},
}

async def buypass(update: Update, context: CallbackContext) -> None:
    """Allows users to purchase a Weekly Pass."""
    user_id = update.effective_user.id
    user = await user_collection.find_one({'id': user_id}) or {}

    if "pass" in user:
        await update.message.reply_text("❌ **You already have an active Weekly Pass!**", parse_mode="Markdown")
        return

    # ✅ Check if user has enough Diamonds
    if user.get("diamonds", 0) < WEEKLY_PASS_PRICE:
        await update.message.reply_text("❌ **Not enough Diamonds!**\nYou need `8,000 Diamonds`.", parse_mode="Markdown")
        return

    # ✅ Deduct Diamonds and Activate Pass
    expiry = int(time.time()) + WEEKLY_PASS_DURATION
    await user_collection.update_one({'id': user_id}, {
        '$set': {'pass': {"expiry": expiry, "type": "weekly"}},
        '$inc': {'diamonds': -WEEKLY_PASS_PRICE}
    })

    # ✅ Show Pass Benefits
    rewards_text = "\n".join(
        f"🗓 **{['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday'][day]}** → "
        f"{data['tokens']} Tokens, {data['diamonds']} Diamonds, {data['rarity']} Character"
        for day, data in WEEKLY_PASS_REWARDS.items()
    )

    await update.message.reply_text(
        f"✅ **Weekly Pass Purchased!** 🎟️\n\n"
        f"📅 **Valid for 7 Days**\n"
        f"💎 **Daily Rewards:**\n{rewards_text}\n\n"
        f"🎁 **Your rewards will be given automatically every day at 12 AM!**",
        parse_mode="Markdown"
    )

# ✅ Register Command
application.add_handler(CommandHandler("buypass", buypass, block=False))

async def check_pass(update: Update, context: CallbackContext) -> None:
    """Shows the user's active pass and remaining days."""
    user_id = update.effective_user.id
    user = await user_collection.find_one({'id': user_id})

    if not user or "pass" not in user:
        await update.message.reply_text("❌ **You don't have an active Weekly Pass!**\nUse `/buypass` to buy one.", parse_mode="Markdown")
        return

    pass_info = user["pass"]
    remaining_days = max(0, (pass_info["expiry"] - int(time.time())) // 86400)

    if remaining_days == 0:
        await update.message.reply_text("❌ **Your Weekly Pass has expired!** Buy a new one using `/buypass`.", parse_mode="Markdown")
        await user_collection.update_one({'id': user_id}, {'$unset': {'pass': ""}})
        return

    await update.message.reply_text(f"🎟️ **Active Weekly Pass**\n"
                                    f"📅 **Days Left:** `{remaining_days}`\n"
                                    f"🎁 **Daily Auto-Rewards Enabled!**", parse_mode="Markdown")

# ✅ Register Command
application.add_handler(CommandHandler("pass", check_pass, block=False))

async def distribute_pass_rewards(context: CallbackContext):
    """Gives daily rewards to users with an active Weekly Pass."""
    users = await user_collection.find({"pass.type": "weekly"}).to_list(length=None)

    for user in users:
        pass_info = user["pass"]
        if int(time.time()) >= pass_info["expiry"]:
            # ✅ Pass Expired, Remove It
            await user_collection.update_one({'id': user["id"]}, {'$unset': {'pass': ""}})
            continue

        # ✅ Get today's reward
        day_index = datetime.utcnow().weekday()
        reward = WEEKLY_PASS_REWARDS.get(day_index, {"tokens": 0, "diamonds": 0, "rarity": "🍀 Rare"})

        # ✅ Get a random character of the day's rarity
        character = await collection.aggregate([
            {"$match": {"rarity": reward["rarity"]}},
            {"$sample": {"size": 1}}
        ]).to_list(length=1)

        if character:
            character = character[0]
            await user_collection.update_one({'id': user["id"]}, {
                '$inc': {'tokens': reward["tokens"], 'diamonds': reward["diamonds"]},
                '$push': {'characters': character}
            })
            character_msg = f"🎴 **New Character:** {character['name']} ({character['rarity']})"
        else:
            character_msg = "❌ No character found for today's rarity."

        # ✅ Send User a Notification
        try:
            await context.bot.send_message(
                chat_id=user["id"],
                text=(
                    f"🎟️ **Weekly Pass Daily Reward** 🎟️\n\n"
                    f"🗓 **Day:** {['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday'][day_index]}\n"
                    f"💎 **Diamonds Earned:** `{reward['diamonds']}`\n"
                    f"🪙 **Tokens Earned:** `{reward['tokens']}`\n"
                    f"{character_msg}\n\n"
                    f"🎁 Rewards given automatically!"
                ),
                parse_mode="Markdown"
            )
        except:
            pass  # Ignore message sending failures

    print(f"✅ Daily pass rewards distributed to {len(users)} users!")

# ✅ Schedule Daily Pass Rewards at 12 AM UTC
application.job_queue.run_daily(distribute_pass_rewards, time=datetime.utcnow().replace(hour=0, minute=0, second=0))
