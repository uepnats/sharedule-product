import discord
from discord import app_commands
from dateutil import parser
import config
import google_calendar

def setup(tree: app_commands.CommandTree):
    """コマンドツリーに/addコマンドを登録"""
    @tree.command(name="add", description="Googleカレンダーに予定を追加します")
    @app_commands.describe(date="予定の日付 (例:yyyy/mm/dd, mm/dd)", schedule="予定の内容")
    async def add_command(interaction: discord.Interaction, date: str, schedule: str):
        await interaction.response.defer(ephemeral=False) # 応答を遅延させる
        try:
            try:
                # dateutilライブラリで柔軟に解析を試みる (年が最初に来る形式を優先)
                date_obj = parser.parse(date, yearfirst=True)
                formatted_date = date_obj.strftime("%Y-%m-%d")
            except parser.ParserError:
                await interaction.followup.send("日付の形式が正しくありません。yyyy/mm/dd、MM/DDまたはM/Dで入力してください。", ephemeral=True)
                return

            user_id = interaction.user.id
            allowed_ids = config.get_allowed_user_ids()

            # Googleカレンダーへの追加処理（権限がある場合）
            added_to_gcal = False
            gcal_message = ""

            if user_id in allowed_ids:
                # add_calendar_event が成功時にイベントオブジェクトを返すことを想定
                success, result = await google_calendar.add_calendar_event(formatted_date, schedule) # 成功時 result は created_event オブジェクト
                if success:
                    created_event = result # result は作成されたイベントオブジェクト
                    gcal_message = f"✅ Googleカレンダーに {formatted_date} の予定 '{schedule}' を追加しました。\n"
                    gcal_message += f'リンク: {created_event.get("htmlLink")}' # リンクを追加
                    added_to_gcal = True
                else: # 追加に失敗した場合
                    gcal_message = f"❌ Googleカレンダーへの予定追加に失敗しました: {result}" # result はエラーメッセージ
            else: # 権限がない場合
                gcal_message = "🚫 あなたはGoogleカレンダーに予定を追加する権限がありません。"

            # ペアリング相手への通知処理
            partner_notification = ""
            user_pairings = config.get_user_pairings()
            if str(user_id) in user_pairings:
                partner_id = int(user_pairings[str(user_id)])
                mention = f"<@{partner_id}>"
                partner_notification = (
                    f"{mention} さんへ: {interaction.user.display_name} さんが {formatted_date} に **{schedule}** を予定に追加しました。"
                )
            # 結果をユーザーに送信
            await interaction.followup.send(gcal_message)
            # ペアリング相手に通知（通知メッセージがある場合のみ）
            if partner_notification:
                await interaction.channel.send(partner_notification)


        except Exception as e:
            print(f"[/add] 予期しないエラー: {e}")
            await interaction.followup.send("予期しないエラーが発生しました。", ephemeral=True)