# subs - journal subscription service on FamilyTrees platform

## Introduction

---

The 'subs' Web App is a web service that allows you to read news and to subscribe/unsubscribe to your family news.

## How It Works

---

The 'subs' service provides a front-end for family members to keep in the loop on what's new to your family-related matters. At the backend for FamilyTrees service team to maintain the publication of faamily matters whereas the family members can subscribe/unsubscribe to the family news as needed.

### Key Features

1. **Keep in the loop with your family Social Circle**
   - Secure login and registration
   - Email verification
   - Password reset functionality

2. **Publication Management**
   - Manage user subscriptions
   - Track subscription status
   - Handle subscription updates

3. **Multi-language Support**
   - Currently supports Traditional Chinese (TW) and English (US)
   - Easy to add more languages

## Dependencies and Installation

---

To install prior to running the application:

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

   ```bash
   cp template.env.txt .env
   ```

   - Update the environment variables in `.env` file accordingly.

4. Create a subdirectory, named `data` in the root directory of the project.

## Usage

### Running the subs server

   ```bash
   python ops_svr.py
   ```

### Running the ftpe server

   ```bash
   streamlit run ftpe_svr.py
   ```

### For FamilyTrees Team

   ```bash
   # publish the journal to subscribers
   <your-subs-server-URL>/pub

   # query subscribers 
   # 1. from front-end browser
   <your-subs-server-URL>/dbq
   # 2. from back-end browser
   python ops_user_query.py

   # update subscribers
   # 1. from front-end browser
   <your-subs-server-URL>/dbu
   # 2. from back-end browser
   python ops_user_update.py

   # Insert/update/delete articles
   # from back-end browser
   python ops_article.py

   ```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

For support, please contact [Michael Kao](mailto:mkaoy2k@gmail.com).

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
