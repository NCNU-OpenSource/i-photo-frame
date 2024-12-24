import datetime
import os
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
import pyttsx3
import time

# Google Calendar API 權限範圍
SCOPES = [
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/calendar"
]


# 已通知事件的記錄文件
NOTIFIED_EVENTS_FILE = "notified_events.txt"


def authenticate_google_calendar():
    """驗證 Google Calendar API，僅在必要時重新授權"""
    creds = None
    token_path = "token.json"

    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=8080, prompt="select_account")

        with open(token_path, "w") as token_file:
            token_file.write(creds.to_json())

    return build("calendar", "v3", credentials=creds)

def get_next_event(service):
    """獲取當前時間之後的最接近事件，並根據提醒時間執行提醒"""
    now = datetime.datetime.now(datetime.timezone.utc)  # 使用 UTC 時間
    now_iso = now.isoformat()

    # 抓取最近的 10 個事件
    events_result = service.events().list(
        calendarId="primary", timeMin=now_iso, maxResults=10, singleEvents=True, orderBy="startTime"
    ).execute()
    events = events_result.get("items", [])

    if not events:
        return None

    for event in events:
        # 取得事件開始時間（考慮時區）
        event_start = event["start"].get("dateTime", event["start"].get("date"))
        event_time = datetime.datetime.fromisoformat(event_start)

        # 默認提前 10 分鐘提醒
        reminder_minutes = 10

        # 獲取自定義提醒（如果有）
        reminders = event.get("reminders", {})
        overrides = reminders.get("overrides", [])
        if overrides:
            # 使用最早的自定義提醒時間
            reminder_minutes = min(override["minutes"] for override in overrides)

        # 計算提醒的觸發時間
        reminder_time = event_time - datetime.timedelta(minutes=reminder_minutes)

        # 如果提醒時間已經到，且事件未被通知
        if now >= reminder_time and event_time > now:
            return event["id"], event["summary"], reminder_time

    return None



def is_event_notified(event_id):
    """檢查事件是否已通知"""
    if not os.path.exists(NOTIFIED_EVENTS_FILE):
        return False
    with open(NOTIFIED_EVENTS_FILE, "r") as file:
        notified_events = file.read().splitlines()
    return event_id in notified_events

def mark_event_as_notified(event_id):
    """標記事件為已通知"""
    with open(NOTIFIED_EVENTS_FILE, "a") as file:
        file.write(f"{event_id}\n")

def speak_event(event_message):
    """播放語音通知"""
    engine = pyttsx3.init(debug=True)
    engine.setProperty("rate", 150)  # 語速
    engine.setProperty("volume", 1)  # 音量
    engine.say(event_message)
    engine.runAndWait()

# def main():
#     # 驗證並連接 Google Calendar 服務
#     service = authenticate_google_calendar()
#     event = get_next_event(service)
#     if event:
#         event_id, summary, event_time = event

#         # 如果事件尚未通知並且在未來
#         now = datetime.datetime.now(datetime.timezone.utc)
#         if not is_event_notified(event_id) and event_time > now:
#             event_message = f"提醒您，事件：{summary}，將於 {event_time.strftime('%Y年%m月%d日 %H:%M')} 開始。"
#             speak_event(event_message)
#             mark_event_as_notified(event_id)


def main():
    service = authenticate_google_calendar()

    while True:
        event = get_next_event(service)
        if event:
            event_id, summary, reminder_time = event
            reminder_time += datetime.timedelta(minutes=10)

            # 確保事件未被通知
            if not is_event_notified(event_id):
                event_message = f"提醒您，事件：{summary}，將於 {reminder_time.strftime('%Y年%m月%d日 %H:%M')} 開始。"
                speak_event(event_message)
                mark_event_as_notified(event_id)

        # 每隔 1 分鐘檢查一次
        time.sleep(60)


main()

