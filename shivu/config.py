class Config(object):
    LOGGER = True

    # Get this value from my.telegram.org/apps
    OWNER_ID = "6523029979"
    sudo_users = [6523029979]
    GROUP_ID = -1002455955347
    TOKEN = "7775101187:AAEctjmSG-xhVYR8jmQjT_RX4G6R3dPbkLA"
    mongo_url = "mongodb+srv://vegetakun447:TK1WRYfAESFT5vTe@cluster0.hcngy.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
    PHOTO_URL = ["http://ibb.co/WvZ6gLTr"]
    SUPPORT_CHAT = "TBD"
    UPDATE_CHAT = "TBD"
    BOT_USERNAME = "test532267bot"
    CHARA_CHANNEL_ID = "-1002455955347"
    api_id = 26626068
    api_hash = "bf423698bcbe33cfd58b11c78c42caa2"
    
class Production(Config):
    LOGGER = True


class Development(Config):
    LOGGER = True
