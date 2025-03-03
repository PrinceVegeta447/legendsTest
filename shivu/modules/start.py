import random
from html import escape
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackContext, CallbackQueryHandler, CommandHandler
from shivu import application, PHOTO_URL, SUPPORT_CHAT, UPDATE_CHAT, BOT_USERNAME, db, GROUP_ID
from shivu import pm_users as collection  

ANIME_EMOJIS = ["🐉", "🏴‍☠️", "🍃", "⚔️", "⛩️", "🛡️", "👊", "🦸‍♂️", "🎯"]  # Random Anime Icons

async def start(update: Update, context: CallbackContext) -> None:
    """Handles the /start command with an interactive UI."""
    user_id = update.effective_user.id
    first_name = update.effective_user.first_name
    username = update.effective_user.username

    user_data = await collection.find_one({"_id": user_id})

    if user_data is None:
        await collection.insert_one({"_id": user_id, "first_name": first_name, "username": username})

        # 🏆 Announce new users in the support group
        await context.bot.send_message(
            chat_id=GROUP_ID, 
            text=f"🔥 **A New Anime Collector Has Arrived!** 🔥\n"
                 f"👤 **User:** [{escape(first_name)}](tg://user?id={user_id})\n"
                 f"💥 **Get ready to collect anime characters from multiple universes!** 🌍⚡",
            parse_mode='Markdown'
        )
    else:
        # ✅ Update user info if changed
        if user_data['first_name'] != first_name or user_data['username'] != username:
            await collection.update_one({"_id": user_id}, {"$set": {"first_name": first_name, "username": username}})

    # 🏆 **Private Chat Start Message**
    if update.effective_chat.type == "private":
        anime_icon = random.choice(ANIME_EMOJIS)
        caption = f"""
{anime_icon} **Welcome, {escape(first_name)}!** {anime_icon}

🌍 **Step into the world of anime!**  
⚡ Collect legendary characters from **One Piece, Naruto, DBZ, Jujutsu Kaisen, Bleach, and more!**  

🎮 **What You Can Do:**  
🔹 **/collect <character>** → Claim anime characters in groups.  
🔹 **/harem** → View your personal anime collection.  
🔹 **/inventory** → Check your Zeni & Crystals.  
🔹 **/summon** → Use Chrono Crystals to summon exclusive characters!  
🔹 **/shop** → Buy **Chrono Crystals & Summon Tickets**.  

🏆 **Start your anime collection now!**  
"""
        keyboard = [
            [InlineKeyboardButton("⚡ ADD ME TO GROUP ⚡", url=f'http://t.me/{BOT_USERNAME}?startgroup=true')],
            [InlineKeyboardButton("🔹 SUPPORT", url=f'https://t.me/{SUPPORT_CHAT}'),
             InlineKeyboardButton("🔸 UPDATES", url=f'https://t.me/{UPDATE_CHAT}')],
            [InlineKeyboardButton("📜 HELP", callback_data='help')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        photo_url = random.choice(PHOTO_URL)

        await context.bot.send_photo(
            chat_id=update.effective_chat.id,
            photo=photo_url,
            caption=caption,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

    else:
        # 🏆 **Group Chat Start Message**
        photo_url = random.choice(PHOTO_URL)
        keyboard = [
            [InlineKeyboardButton("⚡ ADD ME TO GROUP ⚡", url=f'http://t.me/{BOT_USERNAME}?startgroup=true')],
            [InlineKeyboardButton("🔹 SUPPORT", url=f'https://t.me/{SUPPORT_CHAT}'),
             InlineKeyboardButton("🔸 UPDATES", url=f'https://t.me/{UPDATE_CHAT}')],
            [InlineKeyboardButton("📜 HELP", callback_data='help')],
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await context.bot.send_photo(
            chat_id=update.effective_chat.id,
            photo=photo_url,
            caption="⚡ **Bot Activated!** Send me a private message for details.",
            reply_markup=reply_markup
        )


async def button(update: Update, context: CallbackContext) -> None:
    """Handles interactive buttons in the start menu."""
    query = update.callback_query
    await query.answer()

    if query.data == 'help':
        help_text = """
⚡ **Anime Character Collector - Help Menu** ⚡

🟢 **Basic Commands:**  
🔹 `/collect <character>` → Claim a dropped character  
🔹 `/collection` → View your **anime collection**  
🔹 `/inventory` → View your **Zeni & Chrono Crystals**  
🔹 `/shop` → Buy **Crystals & Summon Tickets**  
🔹 `/fav` → Set a favorite character  

🛠 **Admin Commands:**  
🔹 `/set_droptime <number>` → Set drop frequency (Admin only)  
🔹 `/droptime` → View current drop settings  
🔹 `/topgroups` → View **Top Groups**  
🔹 `/top` → View **Top Players**  
"""
        help_keyboard = [[InlineKeyboardButton("⏪ Back", callback_data='back')]]
        reply_markup = InlineKeyboardMarkup(help_keyboard)
        
        await context.bot.edit_message_caption(
            chat_id=update.effective_chat.id,
            message_id=query.message.message_id,
            caption=help_text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

    elif query.data == 'back':
        anime_icon = random.choice(ANIME_EMOJIS)
        caption = f"""
{anime_icon} **Welcome Back, Collector!** {anime_icon}

⚡ **This is the Ultimate Anime Character Collector Bot!**  
🔹 Collect characters from **One Piece, Naruto, DBZ, Jujutsu Kaisen, Bleach, and more!**  
🔹 Use **/collect <character>** to claim them.  
🔹 Check your **collection** with **/harem**.  
🔹 Earn **Zeni & Crystals** by collecting more!  
"""

        keyboard = [
            [InlineKeyboardButton("⚡ ADD ME TO GROUP ⚡", url=f'http://t.me/{BOT_USERNAME}?startgroup=true')],
            [InlineKeyboardButton("🔹 SUPPORT", url=f'https://t.me/{SUPPORT_CHAT}'),
             InlineKeyboardButton("🔸 UPDATES", url=f'https://t.me/{UPDATE_CHAT}')],
            [InlineKeyboardButton("📜 HELP", callback_data='help')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await context.bot.edit_message_caption(
            chat_id=update.effective_chat.id,
            message_id=query.message.message_id,
            caption=caption,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )


# ✅ **Handlers for Start & Interactive Buttons**
application.add_handler(CallbackQueryHandler(button, pattern='^help$|^back$', block=False))
start_handler = CommandHandler('start', start, block=False)
application.add_handler(start_handler)
