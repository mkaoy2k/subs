# 📰 Family Tree Newsletter Subscription System (FamilyTreesOps, or subs for short)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/downloads/)

## 📖 Project Introduction

FamilyTreesOps Journal System is a web service designed for families, allowing family members to easily subscribe to and receive family-related news and event information. The system provides complete front-end and back-end services, including subscription management, newsletter publishing, and editorial verification features.

### ✨ Key Features

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

### Start Backend Server

```bash
python ops_svr.py
```

### Start Admin Interface (For Editors)

```bash
streamlit run admin_ui.py
```

## ⚙️ Environment Variables

| Variable Name | Description | Example | Required |
|--------------|-------------|---------|----------|
| `DB_SVR` | Database server type | `sqlite3` | Yes |
| `DB_NAME` | Database file path | `data/users.db` | Yes |
| `DB_ADMIN` | Admin email | `admin@example.com` | Yes |
| `DB_ADMIN_PW` | Admin password | `your-secure-password` | Yes |
| `OPS_SVR` | Operations server URL | `http://localhost:5000` | Yes |
| `FT_SVR` | FamilyTreesPE server URL | `http://example.com` | Yes |
| `MAIL_SERVER` | Mail server | `smtp.gmail.com` | Yes |
| `MAIL_USERNAME` | Email account | `your-email@gmail.com` | Yes |
| `MAIL_PASSWORD` | Email password or app password | `your-app-password` | Yes |
| `MAIL_DEFAULT_SENDER` | Default sender | `your-email@gmail.com` | Yes |
| `APP_NAME` | Application name | `FamilyTreesOps` | Yes |
| `SECRET_KEY` | Application secret key | Random string | Yes |
| `BASE_URL` | Application URL | `http://localhost:5000` | Yes |
| `ARTICLE_WINDOW` | Article display window (days) | `7` | No |
| `L10N` | Default language | `zh_TW` or `en_US` | No |
| `LOGGING` | Logging level | `INFO` or `DEBUG` | No |
| `OPS_MENU_FILE` | Menu configuration file | `ops_menu.json` | Yes |

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
