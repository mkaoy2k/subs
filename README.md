# 📰 Family Tree Journal Subscription System

(FamilyTreesOps, or code name as `subs` for short)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.13+](https://img.shields.io/badge/Python-3.13+-blue.svg)](https://www.python.org/downloads/)

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

- Python 3.13 or newer (`uv.lock` sets `requires-python = ">=3.13"`)
- [uv](https://docs.astral.sh/uv/) (this is how the server is run locally)
- SQLite 3 (built-in)
- Email service (e.g., Gmail)

### Installation Steps

1. **Clone the Repository**

   ```bash
   git clone https://github.com/mkaoy2k/subs.git
   cd subs
   ```

2. **Install Dependencies**

   `pyproject.toml` and `uv.lock` are the dependency set `uv run` uses. `requirements.txt` is an older full-environment freeze: it includes macOS-only packages such as `pyobjc`, and Flask itself is absent from that file.

   ```bash
   uv sync
   ```

   `uv sync` creates `.venv`. `uv run` uses it on macOS, Linux, and Windows.

   On Linux, if you want the optional gunicorn extra (see below):

   ```bash
   uv sync --extra gunicorn
   ```

3. **Configure Environment Variables**

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

   Leave debug and the listen address to environment variables (`OPS_SVR_HOST`, `OPS_SVR_PORT`, `OPS_DEV`). `python ops_svr.py` serves the app with waitress and leaves Flask debug off. Pass `--dev` when you want the debugger.

4. **Initialize Data Directory**

   ```bash
   mkdir -p data
   ```

5. **Initialize Admin User Database**

   ```bash
   uv run python genesis.py
   ```

## 🛠️ Running the System

This repo has no systemd unit, Dockerfile, or cloud-host config. `requirements.txt` includes macOS frameworks (`pyobjc`), and sample pages link out through ngrok tunnels. The default server is **waitress**, which runs on macOS, Linux, and Windows. gunicorn is the Unix alternative (it imports `fcntl`, so the Windows path stays on waitress).

### Production web server (default)

```bash
uv run python ops_svr.py
```

That process loads `ops_svr:app` and serves it with waitress. Flask debug and the reloader stay off, and Werkzeug's development-server warning stays silent.

Equivalent, if you would rather invoke the WSGI server directly (expand the port yourself; this form does not read `OPS_SVR_PORT`):

```bash
uv run waitress-serve --listen=127.0.0.1:5566 --threads=1 ops_svr:app
```

Listen address:

- `OPS_SVR_HOST` (default `127.0.0.1`, same as the old `app.run` default)
- `OPS_SVR_PORT` (default `5566`)
- `OPS_SVR_THREADS` (default `1`)

Leave the thread count at 1. `before_request` writes the active language into module globals, so overlapping requests can serve the wrong language. Set `OPS_SVR_HOST=0.0.0.0` only when this process should accept connections on every interface.

### Linux: gunicorn

gunicorn is a Unix WSGI server and an optional extra. A plain `uv sync` leaves it out. Locked gunicorn 26 imports `fcntl`, so on Windows use the waitress command above.

```bash
uv sync --extra gunicorn
uv run gunicorn --bind 127.0.0.1:5566 --workers 1 --threads 1 ops_svr:app
```

Keep `--threads 1` (the sync worker). `--threads` greater than 1 switches gunicorn to a threaded worker and hits the same module-global language state. More than one sync worker is a separate process per worker; that avoids the threaded race, but concurrent SQLite access has not been validated here.

### Development server

Use this only when you want the debugger and auto-reloader. It **will** print Flask's development-server warning. That is expected.

```bash
uv run python ops_svr.py --dev
```

or:

```bash
OPS_DEV=1 uv run python ops_svr.py
```

`flask --app ops_svr run` is the development server as well. Production stays `uv run python ops_svr.py`.

### Start Admin Interface (For Admins)

```bash
uv run streamlit run subs_ui.py
```

## ⚙️ Environment Variables

### Server Configuration

- `OPS_SVR`: Operations server URL (e.g., `http://localhost:5566`)
- `OPS_SVR_HOST`: Interface the WSGI server binds (default `127.0.0.1`)
- `OPS_SVR_PORT`: Operations server port (e.g., `5566`)
- `OPS_SVR_THREADS`: waitress thread count (default `1`; see the warning above)
- `OPS_DEV`: set to `1` to run Flask's development server instead of waitress
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
