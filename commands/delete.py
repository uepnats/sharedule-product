import discord
from discord import app_commands
from dateutil import parser
import config
import google_calendar

def setup(tree: app_commands.CommandTree):
    """コマンドツリーに/deleteコマンドを登録します。"""

    @tree.command(name="delete", description="Googleカレンダーの予定を削除します")
    @app_commands.describe(date="削除したい予定の日付", schedule="削除したい予定の内容 (正確に入力)")
    async def delete_command(interaction: discord.Interaction, date: str, schedule: str):
        await interaction.response.defer(ephemeral=False) # 応答を遅延させる

        user_id = interaction.user.id
        allowed_ids = config.get_allowed_user_ids()

        # 権限チェック
        if user_id not in allowed_ids:
            await interaction.followup.send("🚫 あなたは予定を削除する権限がありません。", ephemeral=True)
            return

        try:
            # 日付の解析
            try:
                date_obj = parser.parse(date, yearfirst=True)
                formatted_date = date_obj.strftime("%Y-%m-%d")
            except parser.ParserError:
                await interaction.followup.send("日付の形式が正しくありません。yyyy/mm/dd、MM/DDまたはM/Dで入力してください。", ephemeral=True)
                return

            # 削除したい予定を検索 (タイムゾーン修正は find_calendar_event 内で行われている)
            event_info, error_message = await google_calendar.find_calendar_event(formatted_date, schedule)

            if error_message:
                await interaction.followup.send(f"❌ 予定の検索に失敗しました: {error_message}", ephemeral=True)
                return

            event_id = event_info["id"]
            actual_schedule = event_info["summary"] # 検索で見つかった実際の概要

            # 予定の削除
            success, delete_message = await google_calendar.delete_calendar_event(event_id)

            if success:
                response_message = f"✅ Googleカレンダーの {formatted_date} の予定 '{actual_schedule}' を削除しました。"
            else:
                response_message = f"❌ 予定の削除に失敗しました: {delete_message}"
                await interaction.followup.send(response_message, ephemeral=True)
                return # 削除に失敗したらここで終了

            # ペアリング相手への通知処理
            partner_notification = ""
            user_pairings = config.get_user_pairings()
            if str(user_id) in user_pairings:
                partner_id = int(user_pairings[str(user_id)])
                mention = f"<@{partner_id}>"
                partner_notification = (
                    f"{mention} さんへ: {interaction.user.display_name} さんが予定を削除しました。\n"
                    f"日付: {formatted_date}\n"
                    f"内容: {actual_schedule}"
                )
            # 結果をユーザーに送信
            await interaction.followup.send(response_message)
            # ペアリング相手に通知（通知メッセージがある場合のみ）
            if partner_notification:
                await interaction.channel.send(partner_notification)
        except Exception as e:
            print(f"[/delete] 予期しないエラー: {e}") # 予期しないエラーのログは残しておく
            await interaction.followup.send("予期しないエラーが発生しました。", ephemeral=True)