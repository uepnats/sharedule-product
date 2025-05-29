from datetime import datetime, timedelta
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import config

# 認証情報の取得とサービスの構築
def _build_service():
    """Google Calendar Serviceオブジェクトを構築します。"""
    if not config.GOOGLE_CALENDAR_CREDENTIALS_PATH:
        print("Google Calendarの認証情報ファイルのパスが設定されていません。")
        return None
    try:
        creds = Credentials.from_service_account_file(config.GOOGLE_CALENDAR_CREDENTIALS_PATH, scopes=config.GOOGLE_CALENDAR_SCOPES)
        service = build('calendar', 'v3', credentials=creds)
        return service
    except Exception as e:
        print(f'Google Calendar Serviceの構築中にエラーが発生しました: {e}')
        return None

async def add_calendar_event(date_str, schedule):
    """Googleカレンダーにイベントを追加します。"""
    service = _build_service()
    if not service:
        return False, "カレンダーサービスに接続できませんでした。"

    try:
        event = {
            'summary': schedule,
            'start': {'date': date_str},
            'end': {'date': date_str},
            'transparency': 'transparent', # 終日イベントとして登録する場合に推奨
        }
        calendar_id = config.GOOGLE_CALENDAR_ID
        if not calendar_id:
            return False, "Google Calendar IDが設定されていません。"

        created_event = service.events().insert(calendarId=calendar_id, body=event).execute()
        print(f'Event created: {created_event.get("htmlLink")}')
        # 成功時は created_event オブジェクト全体を返す
        return True, created_event

    except HttpError as error:
        print(f'Googleカレンダーへの追加中にAPIエラーが発生しました: {error}')
        return False, f"Googleカレンダーへの追加中にAPIエラーが発生しました: {error}"
    except Exception as e:
        print(f'Googleカレンダーへの追加中に予期しないエラーが発生しました: {e}')
        return False, f"Googleカレンダーへの追加中に予期しないエラーが発生しました: {e}"


async def find_calendar_event(date_str, schedule_summary):
    """
    指定された日付と概要に一致するGoogleカレンダーイベントを検索します。
    最初に見つかったイベントのIDと概要を返します。
    """
    service = _build_service()
    if not service:
        return None, "カレンダーサービスに接続できませんでした。"

    try:
        calendar_id = config.GOOGLE_CALENDAR_ID
        if not calendar_id:
            return None, "Google Calendar IDが設定されていません。"

        # 指定日の00:00:00から翌日の00:00:00までのイベントをJST (+09:00) で検索
        time_min = f"{date_str}T00:00:00+09:00"
        # date_strを日付オブジェクトに変換して翌日を計算
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        next_day_obj = date_obj + timedelta(days=1)
        time_max = f"{next_day_obj.strftime('%Y-%m-%d')}T00:00:00+09:00"

        events_result = service.events().list(
            calendarId=calendar_id,
            timeMin=time_min,
            timeMax=time_max,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        events = events_result.get('items', [])

        if not events:
            return None, "指定された日付にイベントは見つかりませんでした。"

        # 概要が一致するイベントを検索
        for event in events:
            event_summary = event.get('summary')
            event_id = event.get('id')

            # 入力されたタイトルとイベントのタイトルを比較
            if event_summary == schedule_summary: # 完全一致のチェック
                # 見つかったイベントのIDと実際の概要を返す
                return {"id": event_id, "summary": event_summary}, None # エラーメッセージはNone

        # ループが終わっても見つからなかった場合
        return None, f"指定された日付 ({date_str}) に '{schedule_summary}' というタイトルのイベントは見つかりませんでした。"

    except HttpError as error:
        print(f'Googleカレンダーの検索中にAPIエラーが発生しました: {error}')
        return None, f"Googleカレンダーの検索中にAPIエラーが発生しました: {error}"
    except Exception as e:
        print(f'Googleカレンダーの検索中に予期しないエラーが発生しました: {e}')
        return None, f"Googleカレンダーの検索中に予期しないエラーが発生しました: {e}"


# 期間内のイベントをリストアップする関数
async def list_events_in_range(time_min_str, time_max_str):
    """
    指定された時間範囲 (RFC3339形式文字列) のGoogleカレンダーイベントをリストアップします。
    成功した場合はイベントのリストを、失敗した場合は None とエラーメッセージを返します。
    """
    service = _build_service()
    if not service:
        return None, "カレンダーサービスに接続できませんでした。"

    try:
        calendar_id = config.GOOGLE_CALENDAR_ID
        if not calendar_id:
            return None, "Google Calendar IDが設定されていません。"

        # APIでイベントをリストアップ
        # singleEvents=True で繰り返しイベントを展開
        # orderBy='startTime' で開始時間順にソート
        events_result = service.events().list(
            calendarId=calendar_id,
            timeMin=time_min_str, # RFC3339形式の開始時刻
            timeMax=time_max_str, # RFC3339形式の終了時刻
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        events = events_result.get('items', [])

        # 成功時はイベントのリストを返す
        return events, None # エラーメッセージはNone

    except HttpError as error:
        print(f'Googleカレンダーからのイベントリスト取得中にAPIエラーが発生しました: {error}')
        return None, f"イベントリストの取得中にAPIエラーが発生しました: {error}"
    except Exception as e:
        print(f'Googleカレンダーからのイベントリスト取得中に予期しないエラーが発生しました: {e}')
        return None, f"イベントリストの取得中に予期しないエラーが発生しました: {e}"

async def update_calendar_event(event_id, new_date_str, new_schedule):
    """Googleカレンダーのイベントを更新します。"""
    service = _build_service()
    if not service:
        return False, "カレンダーサービスに接続できませんでした。"

    try:
        calendar_id = config.GOOGLE_CALENDAR_ID
        if not calendar_id:
            return False, "Google Calendar IDが設定されていません。"

        # 更新対象のイベントを取得
        # 更新には元のイベント情報が必要
        event = service.events().get(calendarId=calendar_id, eventId=event_id).execute()

        # 情報を更新
        event['summary'] = new_schedule
        # 開始・終了日時も新しい日付で更新（終日イベントとして）
        event['start'] = {'date': new_date_str}
        event['end'] = {'date': new_date_str}

        # イベントを更新
        updated_event = service.events().update(
            calendarId=calendar_id,
            eventId=event_id,
            body=event
        ).execute()
        print(f'Event updated: {updated_event.get("htmlLink")}')
        return True, updated_event.get("htmlLink")

    except HttpError as error:
        print(f'Googleカレンダーの更新中にAPIエラーが発生しました: {error}')
        return False, f"Googleカレンダーの更新中にAPIエラーが発生しました: {error}"
    except Exception as e:
        print(f'Googleカレンダーの更新中に予期しないエラーが発生しました: {e}')
        return False, f"Googleカレンダーの更新中に予期しないエラーが発生しました: {e}"


async def delete_calendar_event(event_id):
    """Googleカレンダーのイベントを削除します。"""
    service = _build_service()
    if not service:
        return False, "カレンダーサービスに接続できませんでした。"

    try:
        calendar_id = config.GOOGLE_CALENDAR_ID
        if not calendar_id:
            return False, "Google Calendar IDが設定されていません。"

        service.events().delete(calendarId=calendar_id, eventId=event_id).execute()
        print(f'Event deleted: {event_id}')
        return True, None # 成功時はエラーメッセージはNone

    except HttpError as error:
        print(f'Googleカレンダーの削除中にAPIエラーが発生しました: {error}')
        return False, f"Googleカレンダーの削除中にAPIエラーが発生しました: {error}"
    except Exception as e:
        print(f'Googleカレンダーの削除中に予期しないエラーが発生しました: {e}')
        return False, f"Googleカレンダーの削除中に予期しないエラーが発生しました: {e}"