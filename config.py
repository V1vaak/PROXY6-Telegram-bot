import os
from dotenv import load_dotenv

load_dotenv()


PROXY_API_KEY = os.getenv('PROXY6_API_KEY')
BOT_TOKEN = os.getenv('BOT_TOKEN')
YOOKASSA_API_KEY = os.getenv('YOOKASSA_API_KEY')
YOOKASSA_SHOP_ID = os.getenv('YOOKASSA_SHOP_ID')