# subs - FamilyTrees newsletter subscription service on FamilyTrees platform

## Introduction

---

The 'subs' Web App is a web service that allows you publish and subscribe/unsubscribe to your family news and events.

## How It Works

---

The 'subs' service provides a front-end for family members to keep in the loop on what's new to your family-related matters. At the backend for your family newsletter team to maintain the publication of family matters whereas the family members can subscribe/unsubscribe to the family news as needed.

### Key Features

1. **Keep in the loop with your family social circle**
   - Secure login and registration
   - Email verification
   - Password reset functionality

2. **Publication Management**
   - Manage user subscriptions
   - Track subscription status
   - Handle newsletter updates

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

### For FamilyTrees Operations Team

   ```bash
   # publish the journal to subscribers
   <your-subs-server-URL>/pub

   # manage subscribers
   # 1. from front-end browser via URL
   <your-subs-server-URL>/user
   # 2. from back-end browser via streamlit
   streamlit run ops_subMgmt.py

   # manage articles
   # from back-end browser via qt5
   python ops_artBatch.py
   # from back-end browser via streamlit
   streamlit run ops_artMgmt.py
   

   ```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

For support, please contact [Michael Kao](mailto:mkaoy2k@gmail.com).

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
