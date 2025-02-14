from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, CallbackQueryHandler, CallbackContext
from itertools import groupby
import math
import random
from html import escape

from shivu import collection, user_collection, application

# Rarity Symbols
RARITY_SYMBOLS = {
    "Common": "⚪",
    "Uncommon": "🟢",
    "Rare": "🔵",
    "Extreme": "🟣",
    "Sparking": "🟡",
    "Ultra": "🔱",
}

# Category Symbols (example, customize as needed)
CATEGORY_SYMBOLS = {
    "Saiyan": "🦾",
    "Android": "🤖",
    "Frieza Force": "👑",
    "Hybrid Saiyan": "🧒",
    "God Ki": "✨",
}

async def harem(update: Update, context: CallbackContext, page=0) -> None:
    user_id = update.effective_user.id

    # Fetch user data
    user = await user_collection.find_one({'id': user_id})
    if not user or 'characters' not in user or not user['characters']:
        message = "🚫 You haven't collected any characters yet!"
        if update.message:
            await update.message.reply_text(message)
        else:
            await update.callback_query.edit_message_text(message)
        return

    characters = sorted(user['characters'], key=lambda x: (x['category'], x['id']))

    # Count character occurrences
    character_counts = {k: len(list(v)) for k, v in groupby(characters, key=lambda x: x['id'])}

    # Unique characters
    unique_characters = list({char['id']: char for char in characters}.values())

    # Pagination calculations
    total_pages = math.ceil(len(unique_characters) / 15)
    page = max(0, min(page, total_pages - 1))  

    # Header Message
    harem_message = f"<b>🏆 {escape(update.effective_user.first_name)}'s Harem - Page {page+1}/{total_pages}</b>\n"

    # Fetch characters for the current page
    current_characters = unique_characters[page * 15:(page + 1) * 15]

    # Group characters by anime
    grouped_characters = {}
    for char in current_characters:
        grouped_characters.setdefault(char['category'], []).append(char)

    for category, char_list in grouped_characters.items():
        category_total = await collection.count_documents({'category': category})  
        harem_message += f"\n<b>🫧 {category} ({len(char_list)}/{category_total})</b>\n"
        
        for char in char_list:
            rarity_icon = RARITY_SYMBOLS.get(char['rarity'], "❓")  
            category_icon = CATEGORY_SYMBOLS.get(char.get('category', ""), "")  
            count = character_counts[char['id']]
            harem_message += f"{rarity_icon} {char['name']} {category_icon} ×{count}\n"

    # Inline buttons
    total_count = len(user['characters'])
    keyboard = [[InlineKeyboardButton(f"📜 See Collection ({total_count})", switch_inline_query_current_chat=f"collection.{user_id}")]]
    
    if total_pages > 1:
        nav_buttons = []
        if page > 0:
            nav_buttons.append(InlineKeyboardButton("⬅️", callback_data=f"harem:{page-1}:{user_id}"))
        if page < total_pages - 1:
            nav_buttons.append(InlineKeyboardButton("➡️", callback_data=f"harem:{page+1}:{user_id}"))
        keyboard.append(nav_buttons)

    reply_markup = InlineKeyboardMarkup(keyboard)

    # Handle favorite or random character image using `file_id`
    character_file_id = None
    if 'favorites' in user and user['favorites']:
        fav_character_id = user['favorites'][0]
        fav_character = next((c for c in user['characters'] if c['id'] == fav_character_id), None)
        character_file_id = fav_character['file_id'] if fav_character and 'file_id' in fav_character else None
    else:
        random_character = random.choice(user['characters'])
        character_file_id = random_character['file_id'] if 'file_id' in random_character else None

    # Send response
    if update.message:
        if character_file_id:
            await update.message.reply_photo(photo=character_file_id, caption=harem_message, parse_mode="HTML", reply_markup=reply_markup)
        else:
            await update.message.reply_text(harem_message, parse_mode="HTML", reply_markup=reply_markup)
    else:
        try:
            if character_file_id:
                await update.callback_query.edit_message_media(
                    media=InputMediaPhoto(media=character_file_id, caption=harem_message, parse_mode="HTML"),
                    reply_markup=reply_markup
                )
            else:
                await update.callback_query.edit_message_text(harem_message, parse_mode="HTML", reply_markup=reply_markup)
        except Exception:
            pass  # Prevents unnecessary errors if Telegram API blocks repeated edits

async def harem_callback(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    _, page, user_id = query.data.split(":")
    page, user_id = int(page), int(user_id)

    if query.from_user.id != user_id:
        await query.answer("🚫 This is not your Harem!", show_alert=True)
        return

    await harem(update, context, page)

# Register Handlers
application.add_handler(CommandHandler(["harem", "collection"], harem, block=False))
application.add_handler(CallbackQueryHandler(harem_callback, pattern="^harem", block=False))
