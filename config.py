# config.py
import os
import json
from dotenv import load_dotenv

# 環境変数の読み込み
load_dotenv()

# Discord Botの設定
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")

# Google Calendarの設定
GOOGLE_CALENDAR_CREDENTIALS_PATH = os.getenv("GOOGLE_CALENDAR_CREDENTIALS_PATH")
GOOGLE_CALENDAR_SCOPES = ['https://www.googleapis.com/auth/calendar']
GOOGLE_CALENDAR_ID = os.getenv("GOOGLE_CALENDAR_ID")

# config.jsonから読み込む設定
CONFIG_FILE_PATH = "config/config.json"
allowed_users_data = {}
user_pairings = {}

try:
    with open(CONFIG_FILE_PATH, "r") as f:
        config_data = json.load(f)
    allowed_users_data = {user["name"]: user["id"] for user in config_data.get("allowed_users", [])}
    user_pairings = config_data.get("pairings", {})
except FileNotFoundError:
    print(f"Error: Config file not found at {CONFIG_FILE_PATH}")
except json.JSONDecodeError:
    print(f"Error: Could not decode JSON from {CONFIG_FILE_PATH}")
except Exception as e:
    print(f"An unexpected error occurred while loading config: {e}")

# 設定値にアクセスするためのシンプルな関数や変数として公開
def get_allowed_user_ids():
    """許可されたユーザーのIDリストを返します。"""
    return [user["id"] for user in config_data.get("allowed_users", [])]

def get_user_pairings():
    """ユーザーのペアリング情報を返します。"""
    return user_pairings