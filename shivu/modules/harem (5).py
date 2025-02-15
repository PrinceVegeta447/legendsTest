from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, CallbackContext, CallbackQueryHandler
from itertools import groupby
from html import escape
import math
from shivu import collection, user_collection, application, db

DEFAULT_SORT = "rarity"  # Default sorting is now always Rarity

RARITY_ICONS = {
    "⛔ Common": "⛔",
    "🍀 Rare": "🍀",
    "🟣 Extreme": "🟣",
    "🟡 Sparking": "🟡",
    "🔮 Limited Edition": "🔮",
    "🔱 Ultimate": "🔱",
    "👑 Supreme": "👑",
    "⛩️ Celestial": "⛩️"
}

CATEGORY_ICONS = {
    "🏆 Saiyan": "🏆", "🔥 Hybrid Saiyan": "🔥", "🤖 Android": "🤖",
    "❄️ Frieza Force": "❄️", "✨ God Ki": "✨", "💪 Super Warrior": "💪",
    "🩸 Regeneration": "🩸", "🔀 Fusion Warrior": "🔀", "🤝 Duo": "🤝",
    "🔱 Super Saiyan God SS": "🔱", "🗿 Ultra Instinct Sign": "🗿",
    "⚡ Super Saiyan": "⚡", "❤️‍🔥 Dragon Ball Saga": "❤️‍🔥",
    "💫 Majin Buu Saga": "💫", "👾 Cell Saga": "👾", "📽️ Sagas From the Movies": "📽️",
    "☠️ Lineage Of Evil": "☠️", "🌏 Universe Survival Saga": "🌏"
}

SORT_OPTIONS = ["rarity", "category"]  # Sort options

async def harem(update: Update, context: CallbackContext, page=0, query=None) -> None:
    """Displays user's character collection with proper pagination."""
    user_id = update.effective_user.id
    first_name = escape(update.effective_user.first_name)
    user = await user_collection.find_one({'id': user_id})

    if not user or not user.get("characters"):
        message = "❌ <b>You don't have any characters in your collection yet!</b>"
        if query:
            await query.answer(message, show_alert=True)
        else:
            await update.message.reply_text(message, parse_mode="HTML")
        return

    harem_message, reply_markup, fav_character = await generate_harem_message(user, page, first_name)

    if query:
        if fav_character and "file_id" in fav_character:
            await query.message.edit_caption(caption=harem_message, reply_markup=reply_markup, parse_mode="HTML")
        else:
            await query.message.edit_text(harem_message, parse_mode="HTML", reply_markup=reply_markup)
    else:
        if fav_character and "file_id" in fav_character:
            await update.message.reply_photo(photo=fav_character["file_id"], caption=harem_message, reply_markup=reply_markup, parse_mode="HTML")
        else:
            await update.message.reply_text(harem_message, parse_mode="HTML", reply_markup=reply_markup)

async def generate_harem_message(user, page, first_name):
    """Generates harem message and inline keyboard for pagination."""
    user_id = user['id']
    user_pref = await db.user_sorting.find_one({'user_id': user_id}) or {"sort_by": DEFAULT_SORT}
    sort_by = user_pref["sort_by"]

    characters = sorted(user["characters"], key=lambda x: (x.get(sort_by, "Unknown"), x["id"]))
    character_counts = {k: len(list(v)) for k, v in groupby(characters, key=lambda x: x["id"])}
    unique_characters = list({character['id']: character for character in characters}.values())

    total_pages = max(1, math.ceil(len(unique_characters) / 10))
    page = max(0, min(page, total_pages - 1))

    harem_message = (
        f"📜 <b>{first_name}'s Collection</b>\n"
        f"📄 <b>Page {page+1}/{total_pages}</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
    )

    grouped_characters = {k: list(v) for k, v in groupby(unique_characters, key=lambda x: x.get(sort_by, "Unknown"))}

    for rarity, characters in sorted(grouped_characters.items(), key=lambda x: list(RARITY_ICONS.keys()).index(x[0])):
        rarity_icon = RARITY_ICONS.get(rarity, "🔹")
        total_available = await collection.count_documents({"rarity": rarity})
        harem_message += f"\n🫧 {rarity_icon} <b>{rarity}</b> ({len(characters)}/{total_available})\n\n"

        for character in characters:
            count = character_counts[character["id"]]
            harem_message += f"[{character['id']}] {character['name']}  [×{count}]\n"

    total_count = len(user['characters'])
    keyboard = [
        [InlineKeyboardButton(f"📜 See Collection ({total_count})", switch_inline_query_current_chat=f"collection.{user_id}")],
        [InlineKeyboardButton("🔄 Change Sort", callback_data="sort_menu")]
    ]

    if total_pages > 1:
        nav_buttons = []
        if page > 0:
            nav_buttons.append(InlineKeyboardButton("⬅️ Prev", callback_data=f"harem:{page-1}:{user_id}"))
        if page < total_pages - 1:
            nav_buttons.append(InlineKeyboardButton("Next ➡️", callback_data=f"harem:{page+1}:{user_id}"))
        keyboard.append(nav_buttons)

    reply_markup = InlineKeyboardMarkup(keyboard)
    fav_character = next((c for c in user["characters"] if c["id"] == user.get("favorites", [None])[0]), None)

    return harem_message, reply_markup, fav_character

async def harem_callback(update: Update, context: CallbackContext) -> None:
    """Handles pagination properly without sending a new message."""
    query = update.callback_query
    data = query.data.split(":")

    if len(data) < 3:
        await query.answer("Invalid callback data!", show_alert=True)
        return

    action, page, user_id = data[0], int(data[1]), int(data[2])

    if action != "harem":
        return

    if update.effective_user.id != int(user_id):
        await query.answer("❌ You can't view someone else's collection!", show_alert=True)
        return

    await harem(update, context, page=page, query=query)

async def sort_command(update: Update, context: CallbackContext) -> None:
    """Sends an inline keyboard for sorting selection."""
    keyboard = [
        [InlineKeyboardButton(f"{RARITY_ICONS['⛔ Common']} Sort by Rarity", callback_data="sort:rarity")],
        [InlineKeyboardButton("📂 Sort by Category", callback_data="sort:category")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("🔄 <b>Select a sorting method:</b>", reply_markup=reply_markup, parse_mode="HTML")

async def sort_callback(update: Update, context: CallbackContext) -> None:
    """Handles sorting preference and saves it in the database."""
    query = update.callback_query
    data = query.data

    if data == "sort_menu":
        await sort_command(update, context)
        return

    _, sort_by = data.split(":")
    user_id = query.from_user.id

    if sort_by not in SORT_OPTIONS:
        await query.answer("❌ Invalid sorting option!", show_alert=True)
        return

    await db.user_sorting.update_one({"user_id": user_id}, {"$set": {"sort_by": sort_by}}, upsert=True)

    await query.answer(f"✅ Collection will now be sorted by {sort_by.capitalize()}")
    await harem(update, context, query=query)

# ✅ Register Handlers
application.add_handler(CommandHandler(["harem", "collection"], harem, block=False))
application.add_handler(CommandHandler("sort", sort_command, block=False))
application.add_handler(CallbackQueryHandler(harem_callback, pattern="^harem", block=False))
application.add_handler(CallbackQueryHandler(sort_callback, pattern="^sort", block=False))
