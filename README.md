# Journal - FamilyTrees Web App

> Subscription journal system for FamilyTrees service

## Introduction

---

The 'Journal' Web App is a web application that allows you to read and subscribe/unsubscribe to your journal.

## How It Works

---

The 'Journal' service helps you keep updated with what's new to your family-related matters. You can subscribe/unsubscribe to your journal as needed.

### Key Features:

1. **Keep in the loop with your family Social Circle**
   - Secure login and registration
   - Email verification
   - Password reset functionality

2. **Subscription Management**
   - Manage user subscriptions
   - Track subscription status
   - Handle subscription updates

3. **Multi-language Support**
   - Currently supports Traditional Chinese (TW) and English (US)
   - Easy to add more languages

## Dependencies and Installation

---

To install and run the application:

1. Clone the repository:
   ```bash
   git clone https://github.com/mkaoy2k/subs.git
   cd subs
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Configure environment variables in `.env`:
   ```
# --- Endpoints for Servers --- from here 

# Database Server
DB_SVR="sqlite3"

# Operations Server
OPS_SVR=your Journal server URL

# FamilyTrees Server
FT_SVR=your FamilyTrees server URL

# FamilyTrees GitHub Repository
GIT_SVR="https://github.com/mkaoy2k/ftpe.git"

# --- Configurations for DB Server --- from here

# sqlite3 configurations
DB_NAME="data/users.db"
TBL_NAME="users"

# --- Configurations for Gmail service --- from here

# The following parms are used by: funcUtils.py
MAIL_SERVER=smtp.gmail.com
MAIL_USERNAME=your email
MAIL_PASSWORD=your password
MAIL_DEFAULT_SENDER=your email

# App Configuration
APP_NAME=FamilyTrees Journal
SECRET_KEY=your-secret-key
BASE_URL=your journal URL

# --- Server Settings --- from here

# logging level
# LOGGING="DEBUG"
LOGGING="INFO"

# Language Options
L10N_FILE="L10N.json"
L10N="繁中"
# L10N="US"

# Menu Options
OPS_MENU_FILE="ops_menu.json"

   ```

## Usage

### Running the Server

```bash
python ops_svr.py
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

For support, please contact [Michael Kao](mailto:mkaoy2k@gmail.com).

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
