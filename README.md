# subs - FamilyTrees Web App

> Subscription management system for FamilyTrees service

## Introduction

---

The 'FamilyTrees' Web App is a Python application that allows you to record your family tree.

## How It Works

---

The 'Family Trees' service helps you build your family tree as your family grows. You can add, update, or share family information as needed.

### Key Features:

1. **User Management**
   - Secure login and registration
   - Email verification
   - Password reset functionality

2. **Subscription System**
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
   # Database configuration
   DB_SVR=sqlite3
   DB_NAME=users.db
   TBL_NAME=users
   
   # Server settings
   LOGGING=DEBUG
   L10N=TW
   ```

## Usage

### Running the Server

```bash
python ops_svr.py
```

### Managing Subscriptions

To update a user's subscription:
```bash
python ops_activate.py user@example.com PREMIUM
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

For support, please contact [Michael Kao](mailto:mkaoy2k@gmail.com).

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
