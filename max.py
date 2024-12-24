import speech_recognition as sr
import openai
import datetime
import re
import os
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import pyttsx3
import keyboard


# 設置 OpenAI API 金鑰
# openai.api_key = ""

# Google Calendar API 需要的權限
SCOPES = [
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/calendar"
]


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

def create_event(service, summary, location, description, start_time, end_time):
    """在 Google Calendar 上建立一個新事件"""
    event = {
        "summary": summary,
        "location": location,
        "description": description,
        "start": {
            "dateTime": start_time.isoformat(),
            "timeZone": "Asia/Taipei",
        },
        "end": {
            "dateTime": end_time.isoformat(),
            "timeZone": "Asia/Taipei",
        },
    }

    event_result = service.events().insert(calendarId="primary", body=event).execute()
    print(f"Event created: {event_result.get('htmlLink')}")

def voice_to_text():
    """將語音轉換為文字"""
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("請開始說話...")
        try:
            audio = recognizer.listen(source, timeout=15, phrase_time_limit=50)
            print("正在儲存語音檔案作除錯...")
            with open("audio_test.wav", "wb") as f:
                f.write(audio.get_wav_data())
            print("語音檔案已儲存為 audio_test.wav，請檢查錄音內容。")

            print("正在轉換語音為文字...")
            text = recognizer.recognize_google(audio, language="zh-TW")
            print(f"轉換結果: {text}")
            return text
        except sr.UnknownValueError:
            print("無法辨識語音內容。")
        except sr.RequestError as e:
            print(f"語音服務錯誤: {e}")
        except Exception as ex:
            print(f"發生錯誤: {ex}")


def send_to_chatgpt(text):
    """將文字發送到 ChatGPT 並提取關鍵字"""
    try:
        print("正在將文字發送到 ChatGPT...")
        # 使用新版 OpenAI Chat API
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "system", "content": "你是我的隨身助理秘書,要幫我記錄提醒事項"},
                      {"role": "user", "content": f"幫我從以下內容提取關鍵字：{text}"}]
        )

        # 修正：解析 ChatGPT 回應
        keywords = response.choices[0].message.content
        print(f"{keywords}")
        return keywords
    except Exception as e:
        print(f"與 ChatGPT 通信時發生錯誤: {e}")


def determine_time_period(now):
    """根據當前時間判斷是早上、下午、晚上或凌晨"""
    if 6 <= now.hour < 12:
        return "早上"
    elif 12 <= now.hour < 18:
        return "下午"
    elif 18 <= now.hour < 24:
        return "晚上"
    else:
        return "凌晨"
def parse_keywords(keywords):
    """自動解析關鍵字並提取 summary, location, description, start_time, end_time"""
    summary = ""
    location = ""
    description = ""
    start_time = None
    end_time = None

    # 取得今天的日期
    today = datetime.datetime.now()

    # 日期處理
    if "明早" in keywords or "明天" in keywords:
        event_date = today + datetime.timedelta(days=1)
    elif "後天" in keywords:
        event_date = today + datetime.timedelta(days=2)
    elif "今天" in keywords or "待會" in keywords or "等等" in keywords:
        event_date = today
    else:
        # 預設日期從語音提取（例如「12月25號」）
        date_pattern = r'(\d{1,2})月(\d{1,2})號?'
        date_matches = re.search(date_pattern, keywords)
        if date_matches:
            month, day = map(int, date_matches.groups())
            event_date = datetime.datetime(today.year, month, day)
            
            # 如果日期小於今天，推到下一年
            if event_date < today:
                event_date = event_date.replace(year=today.year + 1)
        else:
            event_date = today

    # 提取時間與分鐘
    default_hour = 9  # 預設早上9點
    default_minute = 0
    hour_pattern = r'(\d{1,2})點(?:半|(\d{1,2})分)?'
    hour_matches = re.search(hour_pattern, keywords)

    time_matched = False
    if hour_matches:
        hour = int(hour_matches.group(1))  # 提取小時
        minute = 0

        # 處理分鐘
        if "半" in keywords:
            minute = 30
        elif hour_matches.group(2):  # 如果有具體的分鐘數
            minute = int(hour_matches.group(2))

        # 判斷時段並轉換到24小時制
        if "下午" in keywords or "晚上" in keywords:
            if hour < 12:  # 下午/晚上需轉換到24小時制
                hour += 12
        elif "中午" in keywords:
            hour = 12  # 中午固定為12點

        # 設定開始時間
        start_time = event_date.replace(hour=hour, minute=minute, second=0, microsecond=0)
        time_matched = True

    # 如果沒有指定時間，使用預設值 9:00
    if not time_matched:
        start_time = event_date.replace(hour=default_hour, minute=default_minute, second=0, microsecond=0)

    # 設置結束時間為 1 小時後
    end_time = start_time + datetime.timedelta(hours=1)

    # 提取動詞和名詞作為 Summary
    task_pattern = r'(吃|刷|買|洗|開|提醒|做)\s*([\u4e00-\u9fff]+)'
    task_match = re.search(task_pattern, keywords)
    if task_match:
        summary = f"{task_match.group(1)} {task_match.group(2)}"
    else:
        # 如果沒有匹配到，取最後一個具體詞作為 Summary
        fallback_match = re.findall(r'[\u4e00-\u9fff]+', keywords)
        if fallback_match:
            summary = fallback_match[-1]

    # 判斷地點
    location_keywords = ['台北市', '新北市', '高雄市']
    for loc in location_keywords:
        if loc in keywords:
            location = loc
            break

    # 設置描述
    description = keywords

    return summary, location, description, start_time, end_time

def speak_event(event_message):
    """將事件訊息轉換為語音並播放"""
    engine = pyttsx3.init()  # 初始化語音引擎
    engine.setProperty('rate', 150)  # 設定語速
    engine.setProperty('volume', 1)  # 設定音量（範圍：0.0至1.0）
    engine.say(event_message)  # 將事件訊息傳入語音引擎
    engine.runAndWait()  # 播放語音
def get_upcoming_events(service):
    """獲取即將發生的事件並播放語音提示"""
    now = datetime.datetime.utcnow().isoformat() + "Z"  # 當前時間
    events_result = service.events().list(calendarId="primary", timeMin=now,
                                         maxResults=10, singleEvents=True,
                                         orderBy="startTime").execute()
    events = events_result.get("items", [])

    # 添加調試輸出
    print(f"取得的事件數量: {len(events)}")

    if not events:
        print("沒有即將到來的事件。")
        speak_event("沒有即將到來的事件")
    else:
        for event in events:
            start = event["start"].get("dateTime", event["start"].get("date"))
            event_message = f"事件: {event['summary']}，開始時間: {start}"
            print(event_message)
            speak_event(event_message)



if __name__ == "__main__":
    while True :
        keyboard.wait("enter")
        print("start detect")

        result = voice_to_text()
        if result:
            keywords = send_to_chatgpt(result)
            if keywords:
                summary, location, description, start_time, end_time = parse_keywords(keywords)
                print(f"Summary: {summary}")
                print(f"Location: {location}")
                print(f"Description: {description}")
                print(f"Start Time: {start_time}")
                print(f"End Time: {end_time}")

                # 將事件加入 Google Calendar
                service = authenticate_google_calendar()
                create_event(service, summary, location, description, start_time, end_time)
        keyboard.wait("enter")
        print("end")
