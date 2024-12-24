import os
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

# 設定 Google Drive API 權限
SCOPES = [
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/calendar"
]

def authenticate_google_drive():
    """驗證 Google Drive API，需要登入授權"""
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

    return build("drive", "v3", credentials=creds)

def list_files_in_folder(service, folder_id):
    """列出資料夾中的檔案"""
    query = f"'{folder_id}' in parents and mimeType contains 'image/'"
    results = service.files().list(
        q=query, spaces='drive', fields="files(id, name)", pageSize=100
    ).execute()
    return results.get('files', [])

def download_file(service, file_id, file_name, download_path):
    """下:載檔案到本地目錄"""
    request = service.files().get_media(fileId=file_id)
    file_path = os.path.join(download_path, file_name)
    with open(file_path, "wb") as f:
        downloader = MediaIoBaseDownload(f, request)
        done = False
        while not done:
            status, done = downloader.next_chunk()
            print(f"Downloading {file_name}: {int(status.progress() * 100)}% complete.")
    print(f"File {file_name} downloaded to {file_path}")
    return file_path

if __name__ == "__main__":
    # 驗證並建立 Google Drive API 服務
    service = authenticate_google_drive()

    # 設定 Google Drive 資料夾 ID 和本地下載路徑
    FOLDER_ID = "15nq-oZG39LjLXWCmtZGc47dOGaL18k3p"
    DOWNLOAD_PATH = "/var/www/html/images"
    os.makedirs(DOWNLOAD_PATH, exist_ok=True)

    # 列出資料夾內的圖片檔案
    print("Fetching image list from Google Drive...")
    files = list_files_in_folder(service, FOLDER_ID)

    # 篩選僅限 .jpg 和 .png 的檔案
    filtered_files = [file for file in files if file['name'].lower().endswith(('.jpg', '.png', '.jpeg'))]

    if not filtered_files:
        print(f"No .jpg or .png images found in the folder with ID: {FOLDER_ID}")
    else:
        print(f"Found {len(filtered_files)} images. Starting download...")
        image_files = []
        for file in filtered_files:
            file_id = file['id']
            file_name = file['name']
            image_files.append(download_file(service, file_id, file_name, DOWNLOAD_PATH))

        print("All images downloaded successfully. Starting slideshow...")
