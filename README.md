# 框住每一刻
## 動機:
當夜晚關燈準備入睡時，突然想起明天有一個新的行程需要記錄，但因疲憊或不便，不想再拿起手機操作。如果有一個更直覺、更便利的方式，能立即透過語音將行程記錄下來，那將極大地提升生活的便利性與效率。
## 功能:
- 自動輪播：<br>
智慧相框自動從雲端儲存的相簿中抓取照片，並以輪播形式在顯示器上播放，讓您隨時回味生活中的美好瞬間。
- 語音記錄：<br>
只需輕按相框旁Enter鍵，便可直接口述明天的行程。智慧相框將即時記錄您的語音，並同步至行事曆，讓行程管理更加簡單高效。
## 硬體設備:
- Raspberry Pi
- 顯示器
- 麥克風
- 巨型Enter鍵
## 第三方服務
- Google Drive
- Google Calendar
- Open AI
## 軟體需求及程式語言
- Python
- HTML
- Nginx
## 憑證準備
### How to get OpenAI API key
1. 到 [OpenAI 官網](https://openai.com/)
2. 選擇 Products > API > API Login

![image](https://hackmd.io/_uploads/SJtxLMlUyg.png)

3. 登入後選擇 Dashboard

![image](https://hackmd.io/_uploads/HkdO8zgIkg.png)

4. 選擇 API Keys

![image](https://hackmd.io/_uploads/B1L0LMe8yl.png)

5. 點選 Create new secret key

![image](https://hackmd.io/_uploads/rJmlDzeLye.png)

6. 建立完後貼到 [`max.py` 的 15 行](https://github.com/zxcvcindy/Raspberry-Pi-Calendar/blob/main/max.py#L15) 並取消註解

### How to get Google API credentials

1. 到 [Google Cloud Console](https://console.cloud.google.com/welcome)
2. 選擇 API 和服務

![image](https://hackmd.io/_uploads/B1ltwMlIyx.png)

3. 點選啟用 API 和服務

![image](https://hackmd.io/_uploads/SkgjDfgIkx.png)

4. 找到 Google Drive 跟 Google Calendar 按啟用

![image](https://hackmd.io/_uploads/rJ80vGxIye.png)

5. 回到 API 和服務選擇憑證

![image](https://hackmd.io/_uploads/S1qguMg8Jg.png)

6. 選擇建立憑證 > OAuth 用戶端 ID

![image](https://hackmd.io/_uploads/S1O7_Me8ke.png)

![image](https://hackmd.io/_uploads/B1NrdGeUyx.png)

7. 建立完後就能下載 `credentials.json` 放到專案資料夾底下就可以使用了
## 執行過程
### 下載雲端照片
1. 切換進專案資料夾

  `cd Raspberry-Pi-Calendar`

2. 啟動 python 專案的虛擬環境

  `source venv/bin/activate`

3. 執行get_file2.py下在圖片至指定路徑
   (/var/www/html/ , 與index.html放在同一層)

  `sudo ../../venv/bin/python get_file2.py`

### 開啟照片輪轉
1. 啟動Nginx

   `sudo systemctl start nginx`

2. 查看樹梅派ip

   `ip addr`

3. 在瀏覽器搜尋

   `http://[ip]/

### 執行語音輸入
1. 切換進專案資料夾

   `cd Raspberry-Pi-Calendar`

2. 啟動 `tmux` 來使 `audio.py` 以及 `max.py` 能夠以背景執行

  `tmux`

3. 啟動 python 專案的虛擬環境

  `source venv/bin/activate`

4. 啟動 `max.py`

  `sudo venv/bin/python max.py`

5. `ctrl + b` 後按 `c` 在 `tmux` 新增一個 tab

6. 啟動 python 專案的虛擬環境

  `source venv/bin/activate`

7. 啟動 `audio.py`

  `python audio.py`

## 心得回饋及遇到的困難
1. raspberry pi環境：一開始在設定網路就把樹梅派搞壞，重裝一次，在環境上也花了不少時間。
2. 顯示器:因為想實現照片輪播，裝了GUI發現樹梅派會超燙，還變超當，但還好沒有燒壞。所以後來才決定用網站方式呈現照片輪播。
3. 憑證問題:因為使用Google服務，憑證每隔一段時間就必須刷新一次，而我們的程式碼無法自行更新憑證，需要一直重新取得，最後在josh的幫助下，才修改出可以自動更新憑證的code。
## 工作分配
- 111213028 張嘉心:圖片輪轉功能、PPT總整理
- 111213065 何俞鋒:圖片輪轉功能、上台報搞
- 111213023 謝逸驊:語音輸入辨識及語音提醒功能
- 111213033 朱邑旋:語音輸入辨識及語音提醒功能
- 111213077 林冠伶:github初稿、ppt初稿
- 感謝Josh的超強後援
## 參考資料
- w3school:https://www.w3schools.com/
- 課程共筆:https://hackmd.io/@ncnu-opensource/book/%2FF40AXYr2QMOrUD8HO12zTg
- 名言佳句:http://library.yuda-cloudstudy.com.tw/submenu/index/well-known
- KeyCode Event:https://stackoverflow.com/questions/51267273/how-can-i-use-a-keydown-event-listener-on-a-div
