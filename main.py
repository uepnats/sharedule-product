import discord
from discord import app_commands
import os
import glob
import importlib
import config # config.pyから設定を読み込む

# Discord Botの設定
intents = discord.Intents.default()
intents.message_content = True # 必要に応じてFalseに変更も検討

# Discord Botのクライアントとコマンドツリーの初期化
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

# コマンドを読み込む関数
def load_commands():
    """commandsディレクトリからコマンドモジュールを読み込み、セットアップします。"""
    command_files = glob.glob("commands/*.py") # commands/*.py に一致するファイルを取得
    for command_file in command_files:
        module_name = command_file.replace("\\", "/").replace("/", ".")[:-3] # ファイルパスからモジュール名に変換 (例: commands.add)
        try:
            module = importlib.import_module(module_name)
            if hasattr(module, 'setup'):
                module.setup(tree) # setup関数があれば実行してコマンドを登録
        except Exception as e:
            print(f"Error loading command module {module_name}: {e}") # エラーログは残しておく

# on_readyイベント
@client.event
async def on_ready():
    print(f'{client.user} としてログインしました') # ログインログは残しておく
    load_commands() # ボット起動時にコマンドを読み込む
    await tree.sync() # コマンドをDiscordに同期
    print('コマンドを同期しました') # 同期完了ログは残しておく
    print(f'{client.user} が起動しました') # 起動完了ログは残しておく

# ボットの起動
client.run(config.DISCORD_BOT_TOKEN)