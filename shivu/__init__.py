import logging  
import os
from pyrogram import Client 
from telegram.ext import Application
from motor.motor_asyncio import AsyncIOMotorClient

logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    handlers=[logging.FileHandler("log.txt"), logging.StreamHandler()],
    level=logging.INFO,
)

logging.getLogger("apscheduler").setLevel(logging.ERROR)
logging.getLogger('httpx').setLevel(logging.WARNING)
logging.getLogger("pyrate_limiter").setLevel(logging.ERROR)
LOGGER = logging.getLogger(__name__)

from shivu.config import Development as Config


api_id = Config.api_id
api_hash = Config.api_hash
TOKEN = Config.TOKEN
GROUP_ID = Config.GROUP_ID
CHARA_CHANNEL_ID = Config.CHARA_CHANNEL_ID 
mongo_url = Config.mongo_url 
PHOTO_URL = Config.PHOTO_URL 
SUPPORT_CHAT = Config.SUPPORT_CHAT 
UPDATE_CHAT = Config.UPDATE_CHAT
BOT_USERNAME = Config.BOT_USERNAME 
sudo_users = Config.sudo_users
OWNER_ID = Config.OWNER_ID 

application = Application.builder().token(TOKEN).build()
shivuu = Client("Shivu", api_id, api_hash, bot_token=TOKEN)
lol = AsyncIOMotorClient(mongo_url, tls=True, tlsAllowInvalidCertificates=True)
db = lol['Character_catcher']
collection = db['anime_characters_lol']
user_totals_collection = db['user_totals_lmaoooo']
user_collection = db["user_collection_lmaoooo"]
group_user_totals_collection = db['group_user_totalsssssss']
top_global_groups_collection = db['top_global_groups']
pm_users = db['total_pm_users']
banners_collection = db['banners']
market_collection = db['market']
store_collection = db["store"]
auction_collection = db["auction"]
adventure_collection = db["adventures"]
battle_collection = db["battles"]
investment_collection = db["investment"]
redeem_codes_collection = db["redeem_codes"]
expired_codes_collection = db["expired_codes"]
db.redeem_codes.create_index("code", unique=True)  # Prevent duplicate codes
db.expired_codes.create_index("code", unique=True)  # Track used codes
boss_collection = db["boss"]
raid_collection = db["raid"]
leaderboard_collection = db["leaderboard"]
