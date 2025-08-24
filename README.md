# 📰 Family Tree Journal Subscription System

(FamilyTreesOps, or code name as `subs` for short)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/downloads/)

## 📖 Introduction

FamilyTreesOps Journal System is a web service designed for families, allowing family members to easily subscribe to and receive family-related news and event information. The system provides complete front-end and back-end services, including features, like subscription management, newsletter publishing, and editorial review etc.

### ✨ Current Key Features

- **Membership System**
  - Secure login and registration for editors
  - Open registration for subscribers
  - Email verification
  - Password reset and management

- **Content Management**
  - Newsletter publishing and management
  - Subscription status tracking
  - Content review system
  - User feedback collection

- **Multi-language Support**
  - Traditional Chinese (default)
  - English (US)
  - Easily extendable to other languages

## 🚀 Quick Start

### System Requirements

- Python 3.8 or newer
- SQLite 3 (built-in)
- Email service (e.g., Gmail)

### Installation Steps

1. **Clone the Repository**

   ```bash
   git clone https://github.com/mkaoy2k/subs.git
   cd subs
   ```

2. **Create Virtual Environment (Recommended)**

   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Linux/Mac
   # or
   .\.venv\Scripts\activate  # Windows
   ```

3. **Install Dependencies**

   ```bash
   pip install -r requirements.txt
   ```

4. **Configure Environment Variables**

   ```bash
   cp template.env.txt .env
   ```

   Edit the `.env` file to tailor your environment:
   - Set server paths
   - Set your language, release, and version etc.
   - Configure email service
   - Set application secret key
   - Configure server URL

   Edit `L10N.json` if your language is newly added. The default languages are Traditional Chinese (繁中) and English (US).

   Edit `L10N_<your language>.json` if your language is newly added. The default localization files included are Traditional Chinese `L10N_TW.json` and English `L10N_US.json`.

   Edit `ops_svr.py` for your production Flask server. For example, you can set `DEBUG = False` and `HOST = '0.0.0.0'`.

5. **Initialize Data Directory**

   ```bash
   mkdir -p data
   ```

6. **Initialize Admin User Database**

   ```bash
   python genesis.py
   ```

## 🛠️ Running the System

### Start Web Server

```bash
python ops_svr.py
```

### Start Admin Interface (For Admins)

```bash
streamlit run subs_ui.py
```

## ⚙️ Environment Variables

### Server Configuration

- `OPS_SVR`: Operations server URL (e.g., `http://localhost:5566`)
- `OPS_SVR_PORT`: Operations server port (e.g., `5566`)
- `RELEASE`: Application release version (e.g., `2.0`)
- `L10N_FILE`: Localization file (default: `L10N.json`)
- `L10N`: Language code (e.g., `繁中`)
- `TIMEZONE`: Server timezone (e.g., `Your Timezone`)

### Database Configuration

- `DB_SVR`: Database server type (e.g., `sqlite3`)
- `DB_NAME`: Database file path (e.g., `data/users.db`)
- `TBL_USR`: Users table name (e.g., `user`)
- `TBL_ARTICLE`: Articles table name (e.g., `article`)
- `DB_ADMIN`: Database admin email (e.g., `Your DB Admin Email`)
- `DB_ADMIN_PW`: Database admin password (e.g., `Your DB Admin Password`)

### Email Configuration

- `MAIL_USERNAME`: Gmail account (e.g., `Your Gmail Account`)
- `MAIL_PASSWORD`: Gmail app password (e.g., `Your Gmail App Password`)
- `MAIL_DEFAULT_SENDER`: Default sender email (e.g., `Your Gmail Account`)

### App Configuration

- `APP_NAME`: Application name (e.g., `Your App Name`)
- `BASE_URL`: Base URL of the application (e.g., `Your Base URL`)
- `SECRET_KEY`: Application secret key (e.g., `Your Flask Secret Key`)
- `FT_SVR`: FamilyTreesPE server URL (e.g., `Your FamilyTreesPE Server URL`)

### Optional Variables

- `ARTICLE_WINDOW`: Article display window in days (default: `7`)
- `LOGGING`: Logging level (e.g., `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`) (default: `INFO`)


## 🤝 Contributing

We welcome contributions to improve this project! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the [MIT](LICENSE) License

## 📬 Contact Us

For any questions or suggestions, please contact:

- [Michael Kao](mailto:mkaoy2k@gmail.com)
- [GitHub Issues](https://github.com/mkaoy2k/subs/issues)
