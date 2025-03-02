import re
import time
from html import escape
from cachetools import TTLCache
from pymongo import ASCENDING
from telegram import Update, InlineQueryResultPhoto
from telegram.ext import InlineQueryHandler, CallbackContext
from shivu import user_collection, collection, application, db

# ✅ Database Indexes
db.characters.create_index([('id', ASCENDING)])
db.characters.create_index([('anime', ASCENDING)])
db.characters.create_index([('file_id', ASCENDING)])

db.user_collection.create_index([('characters.id', ASCENDING)])
db.user_collection.create_index([('characters.name', ASCENDING)])
db.user_collection.create_index([('characters.file_id', ASCENDING)])

# ✅ Caching for Optimization
all_characters_cache = TTLCache(maxsize=10000, ttl=36000)
user_collection_cache = TTLCache(maxsize=10000, ttl=60)

async def inlinequery(update: Update, context: CallbackContext) -> None:
    query = update.inline_query.query
    offset = int(update.inline_query.offset) if update.inline_query.offset else 0  # Get current offset
    limit = 50  # Max results per query

    # ✅ Prevent Timeout by Answering Early
    await update.inline_query.answer([], cache_time=1)

    if query.startswith('collection.'):
        user_id, *search_terms = query.split(' ')[0].split('.')[1], ' '.join(query.split(' ')[1:])
        if user_id.isdigit():
            if user_id in user_collection_cache:
                user = user_collection_cache[user_id]
            else:
                user = await user_collection.find_one({'id': int(user_id)})
                user_collection_cache[user_id] = user

            if user:
                all_characters = list({v['id']: v for v in user['characters']}.values())
                if search_terms:
                    regex = re.compile(' '.join(search_terms), re.IGNORECASE)
                    all_characters = [char for char in all_characters if regex.search(char['name']) or regex.search(char['anime'])]
            else:
                all_characters = []
        else:
            all_characters = []
    else:
        if query:
            regex = re.compile(query, re.IGNORECASE)
            all_characters = await collection.find(
                {"$or": [{"name": regex}, {"anime": regex}]}
            ).skip(offset).limit(limit).to_list(length=limit)  # ✅ Skip & limit for pagination
        else:
            if 'all_characters' in all_characters_cache:
                all_characters = all_characters_cache['all_characters']
            else:
                all_characters = await collection.find({}).skip(offset).limit(limit).to_list(length=limit)
                all_characters_cache['all_characters'] = all_characters

    if not all_characters:
        return  # Prevents sending empty results

    results = []
    for character in all_characters:
        global_count = await user_collection.count_documents({'characters.id': character['id']})
        anime_characters = await collection.count_documents({'anime': character['anime']})

        if query.startswith('collection.'):
            user_character_count = sum(c['id'] == character['id'] for c in user['characters'])
            user_anime_characters = sum(c['anime'] == character['anime'] for c in user['characters'])
            caption = (
                f"<b> Look At <a href='tg://user?id={user['id']}'>{escape(user.get('first_name', user['id']))}</a>'s Character</b>\n\n"
                f"⚡: <b>{character['name']} (x{user_character_count})</b>\n"
                f"🫧: <b>{character['anime']} ({user_anime_characters}/{anime_characters})</b>\n"
                f"<b>{character['rarity']}</b>\n\n"
                f"<b>🆔️:</b> {character['id']}"
            )
        else:
            caption = (
                f"<b>Look At This Character !!</b>\n\n"
                f"⚡:<b> {character['name']}</b>\n"
                f"🫧: <b>{character['anime']}</b>\n"
                f"<b>{character['rarity']}</b>\n"
                f"🆔️: <b>{character['id']}</b>\n\n"
                f"<b>Globally Guessed {global_count} Times...</b>"
            )

        results.append(
            InlineQueryResultPhoto(
                thumbnail_url=character['file_id'],
                id=f"{character['id']}_{time.time()}",
                photo_url=character['file_id'],
                caption=caption,
                parse_mode="HTML"
            )
        )

    # ✅ Implement Pagination
    next_offset = str(offset + limit) if len(all_characters) == limit else ""  # Send next offset only if more results exist

    # ✅ Send Final Results with Pagination
    await update.inline_query.answer(results, cache_time=5, next_offset=next_offset)

# ✅ Register the Inline Query Handler
application.add_handler(InlineQueryHandler(inlinequery, block=False))
