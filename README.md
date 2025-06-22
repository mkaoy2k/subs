# 📰 家庭樹電子報訂閱系統 (FamilyTreesOps, subs in short)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/downloads/)

## 📖 專案介紹

FamilyTreesOps 電子報訂閱系統是一個專為家庭設計的網路服務，讓家庭成員能夠輕鬆訂閱和接收家庭相關新聞與活動資訊。系統提供完整的前後端服務，包括訂閱管理、內容發布和用戶驗證等功能。

### ✨ 主要功能

- **會員系統**
  - 編輯者安全登入與註冊
  - 訂閱者開放註冊
  - 電子郵件驗證
  - 密碼重設與管理

- **內容管理**
  - 電子報發布與管理
  - 訂閱狀態追蹤
  - 內容審核系統
  - 用戶反饋收集

- **多語言支援**
  - 繁體中文 (預設)
  - 英文 (美國)
  - 可輕鬆擴充其他語言

## 🚀 快速開始

### 系統需求

- Python 3.8 或更新版本
- SQLite 3 (內建)
- 電子郵件服務 (如 Gmail)

### 安裝步驟

1. **克隆儲存庫**

   ```bash
   git clone https://github.com/mkaoy2k/subs.git
   cd subs
   ```

2. **建立虛擬環境 (建議)**

   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Linux/Mac
   # 或
   .\.venv\Scripts\activate  # Windows
   ```

3. **安裝相依套件**

   ```bash
   pip install -r requirements.txt
   ```

4. **設定環境變數**

   ```bash
   cp template.env.txt .env
   ```

   編輯 `.env` 檔案，根據您的環境進行設定：
   - 設定資料庫路徑
   - 配置電子郵件服務
   - 設定應用程式金鑰
   - 配置伺服器網址

5. **初始化資料目錄**

   ```bash
   mkdir -p data
   ```

6. **初始化資料庫**

   ```bash
   python genesis.py
   ```

## 🛠️ 執行系統

### 啟動後端伺服器

```bash
python ops_svr.py
```

### 啟動管理介面 (編輯者使用)

```bash
streamlit run admin_ui.py
```

## ⚙️ 環境變數說明

| 變數名稱 | 說明 | 範例 | 必填 |
|---------|------|------|------|
| `DB_SVR` | 資料庫伺服器類型 | `sqlite3` | 是 |
| `DB_NAME` | 資料庫檔案路徑 | `data/users.db` | 是 |
| `DB_ADMIN` | 管理員電子郵件 | `admin@example.com` | 是 |
| `DB_ADMIN_PW` | 管理員密碼 | `your-secure-password` | 是 |
| `OPS_SVR` | Operations 伺服器網址 | `http://localhost:5000` | 是 |
| `FT_SVR` | FamilyTreesPE 伺服器網址 | `http://example.com` | 是 |
| `MAIL_SERVER` | 郵件伺服器 | `smtp.gmail.com` | 是 |
| `MAIL_USERNAME` | 郵件帳號 | `your-email@gmail.com` | 是 |
| `MAIL_PASSWORD` | 郵件密碼或應用程式密碼 | `your-app-password` | 是 |
| `MAIL_DEFAULT_SENDER` | 預設寄件者 | `your-email@gmail.com` | 是 |
| `APP_NAME` | 應用程式名稱 | `FamilyTreesOps` | 是 |
| `SECRET_KEY` | 應用程式密鑰 | 隨機字串 | 是 |
| `BASE_URL` | 應用程式網址 | `http://localhost:5000` | 是 |
| `ARTICLE_WINDOW` | 文章顯示天數 | `7` | 否 |
| `L10N` | 預設語言 | `繁中` 或 `US` | 否 |
| `LOGGING` | 日誌等級 | `INFO` 或 `DEBUG` | 否 |
| `OPS_MENU_FILE` | 選單設定檔 | `ops_menu.json` | 是 |

## 🤝 貢獻指南

歡迎提交 Pull Request 來改進這個專案！請遵循以下步驟：

1. Fork 儲存庫
2. 建立功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交您的修改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 開啟 Pull Request

## 📄 授權

本專案採用 [MIT](LICENSE) 授權條款

## 📬 聯絡我們

如有任何問題或建議，請聯繫：

- [Michael Kao](mailto:mkaoy2k@gmail.com)
- [GitHub Issues](https://github.com/mkaoy2k/subs/issues)
