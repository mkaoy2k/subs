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

   `pyproject.toml` and `uv.lock` are what `uv sync` / `uv run` use. `requirements.txt` is that same default set, pinned for pip (Flask, waitress, and the rest of the lock). It does not include the optional gunicorn extra or macOS-only packages.

   ```bash
   uv sync
   ```

   `uv sync` creates `.venv`. `uv run` uses it on macOS, Linux, and Windows.

   The pip equivalent of that default set, on Python 3.13 or newer:

   ```bash
   pip install -r requirements.txt
   ```

   On Linux, if you want the optional gunicorn extra (see below):

   ```bash
   uv sync --extra gunicorn
   ```

   gunicorn is not listed in `requirements.txt`.

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

This repo has no systemd unit, Dockerfile, or cloud-host config. Sample pages link out through ngrok tunnels. The default server is **waitress**, which runs on macOS, Linux, and Windows. gunicorn is the Unix alternative (it imports `fcntl`, so the Windows path stays on waitress).

### Production web server (default)

```bash
uv run python ops_svr.py --family_id <family_id>
```

`<family_id>` is required. It is the family this process serves. Only a person whose `user.family_id` equals that value may subscribe or submit feedback. The same value can be set with `FAMILY_ID` in `.env`; `--family_id` overrides it.

If both are missing or blank, the process exits before it listens. The error names `--family_id` and `FAMILY_ID`. `python ops_svr.py` with neither set does not start.

That process loads `ops_svr:app` and serves it with waitress. Flask debug and the reloader stay off, and Werkzeug's development-server warning stays silent.

`waitress-serve ops_svr:app` and `gunicorn ops_svr:app` do not parse `--family_id`. They import `ops_svr:app`, and that import exits the same way when `FAMILY_ID` is blank. Set `FAMILY_ID` in the environment for those processes.

Equivalent, if you would rather invoke the WSGI server directly (expand the port yourself; this form does not read `OPS_SVR_PORT`):

```bash
uv run waitress-serve --listen=127.0.0.1:5566 --threads=4 ops_svr:app
```

Listen address:

- `OPS_SVR_HOST` (default `127.0.0.1`, same as the old `app.run` default)
- `OPS_SVR_PORT` (default `5566`)
- `OPS_SVR_THREADS` (default `1`)

The active language, menu, and page strings are stored on Flask's `g` for the current request, so overlapping requests do not mix languages. The browser choice is a `current_lang` cookie (the session cookie stays `Secure`, so a browser on plain HTTP would otherwise drop it). `OPS_SVR_THREADS=4` is a reasonable small-site setting (waitress's own default). The process default stays `1` until you set the variable. The `waitress-serve` line above does not read `OPS_SVR_PORT` or `OPS_SVR_THREADS`; `--threads=4` is the recommended explicit value. Set `OPS_SVR_HOST=0.0.0.0` only when this process should accept connections on every interface.

### Linux: gunicorn

gunicorn is a Unix WSGI server and an optional extra. A plain `uv sync` leaves it out. Locked gunicorn 26 imports `fcntl`, so on Windows use the waitress command above.

```bash
uv sync --extra gunicorn
uv run gunicorn --bind 127.0.0.1:5566 --workers 1 --threads 4 ops_svr:app
```

`--workers 1 --threads 4` keeps one process (one in-memory catalog) and serves overlapping requests. Each request binds its own language, so threads above 1 do not mix languages. Extra workers are separate processes and also do not share request language; concurrent SQLite writes across those workers have not been load-tested. gunicorn stays an optional extra. On Windows, use waitress.

### Development server

Use this only when you want the debugger and auto-reloader. It **will** print Flask's development-server warning. That is expected.

```bash
uv run python ops_svr.py --dev --family_id <family_id>
```

or:

```bash
OPS_DEV=1 uv run python ops_svr.py --family_id <family_id>
```

The development server exits too when no family id is set.

`flask --app ops_svr run` is the development server as well. It imports `ops_svr:app`, so it also exits when no family id is set. Production stays `uv run python ops_svr.py --family_id <family_id>`, or the same command with `FAMILY_ID` set.

### Start Admin Interface (For Admins)

```bash
uv run streamlit run subs_ui.py
```

## Family membership

Member records are rows in the `user` table (`DB_NAME`, default `data/users.db`). There is no separate members table in this app. Lookup is by email (`get_subscriber`). A person is a member of the family this server was started with when `user.family_id` equals that id. The family-id comparison trims surrounding whitespace and then matches exactly, including case. `"12"` matches a value stored as the integer 12.

Addresses in subscribe, confirm, unsubscribe, and feedback are stripped and compared in lowercase. `Member@Example.com` matches a row stored as `member@example.com`. When this flow updates that row, it rewrites the stored address to the lowercase form unless another row already uses that exact spelling. SQLite's unique index on `email` is case-sensitive, so two rows that differ only by case can already exist. Lookup then prefers the row whose spelling is already lowercase, otherwise the lowest id. The extra row is not deleted. SQLite `LOWER()` folds ASCII letters; that covers ordinary email addresses. Password-reset lookups are unchanged and still match the stored spelling exactly. `get_subscriber` is shared with the contact form, so that lookup is case-insensitive too; the contact form does not rewrite the stored address.

`user.family_id` is added on startup for databases created before this column existed. New rows leave it empty until an admin sets it. In the admin UI (User Management), the Family ID field writes that column. A family Admin registers the person's email and personal information there first.

On `POST /subscribe` the address is checked with the existing email-format check.

- A member receives the existing verification email. Confirming it activates the subscription. The update does not change `family_id`.
- Anyone else receives one instruction email, in Traditional Chinese and English, telling them to contact the family Admin (`DB_ADMIN`) and register their email and personal information before subscribing. No user row is created, and an existing row for a different family is left unchanged.
- Unsubscribe still sends a verification email and does not require membership. The address match is case-insensitive.

The feedback form uses the same membership rule. Someone who is not a member does not get a pending user row. They receive the same instruction email, and the page shows the same check-your-email line as subscribe (`SUB_CHECK_EMAIL` in `L10N_TW.json` and `L10N_US.json`). A member who is not an active subscriber sees that same line and receives the verification email; no article is stored. An active member's article is accepted, and only that completed submission shows the success message.

The browser is shown the same check-your-email message for a member and for anyone else when the request does not finish an article or a confirmed subscription. The letter itself is what differs. That is the privacy tradeoff: the mailbox owner learns whether this family has them registered, which the product requires, and the form response does not. Invalid email format is still rejected on the page, before any lookup. The two mail paths do different database work, so response time can still differ.

Confirming a verification link re-checks membership. If the address is not a member of the configured family, the link does not activate the subscription and does not clear the token. A missing family id also refuses activation. The process exits at startup when no family id is configured, so it does not serve that request.

```bash
uv run python tests/family_subscribe_smoke.py
uv run python tests/request_locale_smoke.py
```

## ⚙️ Environment Variables

### Server Configuration

- `OPS_SVR`: Operations server URL (e.g., `http://localhost:5566`)
- `OPS_SVR_HOST`: Interface the WSGI server binds (default `127.0.0.1`)
- `OPS_SVR_PORT`: Operations server port (e.g., `5566`)
- `OPS_SVR_THREADS`: waitress thread count (default `1`). Language is request-local; `4` is a reasonable setting once you want concurrent requests.
- `OPS_DEV`: set to `1` to run Flask's development server instead of waitress
- `FAMILY_ID`: family id this server accepts subscriptions and feedback for. `--family_id` overrides it. The process exits when both are blank. See [Family membership](#family-membership).
- `RELEASE`: Application release version (e.g., `2.0`)
- `L10N_FILE`: Localization file (default: `L10N.json`)
- `L10N`: Language code (e.g., `繁中`)
- `TIMEZONE`: Server timezone (e.g., `Your Timezone`)

### Database Configuration

- `DB_SVR`: Database server type (e.g., `sqlite3`)
- `DB_NAME`: Database file path (e.g., `data/users.db`)
- `TBL_USR`: Users table name (e.g., `user`)
- `TBL_ARTICLE`: Articles table name (e.g., `article`)
- `DB_ADMIN`: Database admin email (e.g., `Your DB Admin Email`). This address is the family Admin named in the non-member instruction email.
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
