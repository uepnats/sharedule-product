import discord
from discord import app_commands
from datetime import datetime, timedelta
from dateutil import parser
import config
import google_calendar

def setup(tree: app_commands.CommandTree):
    """コマンドツリーに/list_dayコマンドを登録"""
    @tree.command(name="list_day", description="指定した日付の予定一覧を表示します")
    @app_commands.describe(date="予定を表示したい日付 (例:yyyy/mm/dd, mm/dd, 今日, 明日)")
    async def list_day_command(interaction: discord.Interaction, date: str):
        await interaction.response.defer(ephemeral=False) # 応答を遅延

        user_id = interaction.user.id
        allowed_ids = config.get_allowed_user_ids()

        try:
            # 日付の解析
            try:
                # dateutil.parser は "today", "tomorrow" なども解析できます
                date_obj = parser.parse(date, yearfirst=True, fuzzy=True) # fuzzy=True で曖昧な解析も試みる
                formatted_date = date_obj.strftime("%Y-%m-%d")
            except parser.ParserError:
                await interaction.followup.send("日付の形式が正しくありません。yyyy/mm/dd、MM/DD、M/D、「今日」「明日」などで入力してください。", ephemeral=True)
                return

            # 検索期間の設定 (指定日の 00:00 JST から翌日の 00:00 JST まで)
            time_min = f"{formatted_date}T00:00:00+09:00"
            next_day_obj = date_obj + timedelta(days=1)
            time_max = f"{next_day_obj.strftime('%Y-%m-%d')}T00:00:00+09:00"
            # Googleカレンダーからイベントリストを取得
            events, error_message = await google_calendar.list_events_in_range(time_min, time_max)

            if error_message:
                await interaction.followup.send(f"❌ 予定の取得に失敗しました: {error_message}", ephemeral=True)
                return

            # 応答メッセージの生成
            if not events:
                response_message = f"{formatted_date} の予定はありません。"
            else:
                response_message = f"🗓️ **{formatted_date} の予定:**\n"
                for event in events:
                    summary = event.get('summary', 'タイトルなし')
                    # 終日イベントかどうかを判定して表示を調整
                    start = event.get('start', {})
                    end = event.get('end', {})

                    if 'date' in start: # 終日イベントの場合
                        # 終日イベントは開始日と終了日が同じ date キーで示される
                        # 厳密には終了日はイベントの最後の日の翌日になるが、表示上は日付だけで良いことが多い
                        response_message += f"・ {summary} (終日)\n"
                    else: # 時間指定イベントの場合
                        # dateTime キーで示される
                        start_time_str = datetime.fromisoformat(start.get('dateTime')).strftime('%H:%M')
                        end_time_str = datetime.fromisoformat(end.get('dateTime')).strftime('%H:%M')
                        response_message += f"・ {summary} ({start_time_str} - {end_time_str})\n" # 必要に応じてタイムゾーン考慮も

            # 結果をユーザーに送信
            await interaction.followup.send(response_message)

        except Exception as e:
            print(f"[/list_day] 予期しないエラー: {e}")
            await interaction.followup.send("予期しないエラーが発生しました。", ephemeral=True)