
# AI-Powered Email Assistant 📧✨
A sophisticated Python-based email management system with AI-powered content generation, contact management, and multi-account support.

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![License](https://img.shields.io/badge/License-Proprietary-orange.svg)
![Status](https://img.shields.io/badge/Status-Active-brightgreen.svg)

---

## 🌟 Features

### 🤖 AI-Powered Email Generation
- **Smart Content Creation:** Generates professional email drafts using Groq’s AI models.  
- **Tone Customization:** Choose from multiple tones — formal, casual, persuasive, and more.  
- **Attachment Awareness:** AI naturally references attachments and links.  
- **Dynamic Signatures:** Automatically adjusts signatures to match tone and context.  

### 👥 Advanced Contact Management
- **Full CRUD Operations:** Create, read, update, and delete contacts.  
- **Multiple Emails per Contact:** Store multiple addresses for each person.  
- **Categorization:** Group contacts by work, personal, or family.  
- **Search & Filter:** Search by name, email, company, or notes.  
- **Import/Export:** JSON-based backup and restore.  

### 📧 Multi-Account Email Support
- **Multiple Accounts:** Add work, personal, or other email accounts.  
- **Quick Switching:** Seamlessly switch between accounts.  
- **Account Management:** Add, edit, delete, and set default accounts.  
- **SMTP Support:** Works with Gmail, Outlook, and most major email services.  

### 🛠️ Advanced Features
- **Attachment Management:** Supports multiple file types and configurable size limits.  
- **Clickable Links:** Add interactive URLs to your emails.  
- **Draft Management:** Save and edit email drafts.  
- **Batch Sending:** Send personalized emails via CSV.  
- **Custom Settings:** Control AI behavior, signatures, and attachments.  

---

## 📁 Project Structure
```text
AI-Email-Assistant/
├── main_app.py              # Main application entry point
├── email_sender.py          # Core email sending functionality
├── contact_manager.py       # Contact management system
├── batch_email_sender.py    # Batch email sending via CSV
├── email_config.cfg         # Configuration file (create from template)
├── requirements.txt         # Python dependencies
├── Start.bat                # Windows launcher
└── contacts.json            # Contact database (auto-generated)
```

---

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Groq API account (API key required)
- Email account with SMTP access

### Installation
```bash
git clone https://github.com/Unkn-0-wngb/AI-Email-Assistant.git
cd AI-Email-Assistant
pip install -r requirements.txt
```

### Configuration
Copy `email_config.cfg` and fill in:
- Personal information (name, phone, etc.)
- SMTP email credentials
- Groq API key
- Signature preferences

Run the app:
```bash
python main_app.py
```
Or, on Windows:
```bash
Start.bat
```

---

## ⚙️ Configuration Details

### Email Account Setup
```ini
[personal_info]
name = Your Full Name
phone = Your Phone Number
company = Your Company
position = Your Job Title

[email_accounts]
default_account = work
work_email = your.email@company.com

[work_email]
smtp_server = smtp.gmail.com
smtp_port = 587
smtp_username = your.email@company.com
smtp_password = your_app_password
display_name = Your Display Name
```

### Groq AI Setup
Sign up at [Groq Console](https://console.groq.com) → Get your API key → Add it to:
```ini
[ai_settings]
groq_api_key = your_groq_api_key_here
model = llama-3.1-8b-instant
```

---

## 🎯 Usage Examples

### Sending a Single Email
1. Select **“Send Email”** in the menu.  
2. Choose or create a recipient.  
3. Describe your message purpose.  
4. Pick tone (Formal, Casual, etc.).  
5. Add attachments if needed.  
6. Review AI-generated content.  
7. Send or save as draft.

### Batch Email Sending
- Prepare a CSV file:
  ```
  name,email,message,tone
  John Doe,john@example.com,Meeting follow-up,Formal
  ```
- Run `batch_email_sender.py` to send to all recipients.

### Contact Management
- Add, edit, delete, search, and categorize contacts.  
- Import/export JSON for backup.  

---

## 🔧 Advanced Configuration

### Signature Settings
```ini
[signature_settings]
include_phone = yes
include_address = no
include_company = yes
include_position = yes
include_website = no
```

### Attachment Settings
- **Max size:** 25 MB (configurable)  
- **Supported:** PDF, DOC, DOCX, TXT, JPG, JPEG, PNG, GIF, ZIP, RAR  

### AI Model Selection
- `llama-3.1-8b-instant` (default, fast)
- `llama-3.1-70b-versatile` (high quality)
- `mixtral-8x7b-32768` (balanced)
- `gemma2-9b-it` (efficient)

---

## 🛠️ Development

### Adding New Features
Modular design allows easy extension:
- `email_sender.py` → Email logic  
- `contact_manager.py` → CRUD operations  
- `main_app.py` → Core workflow  

### Testing
```bash
# Check email configuration
python -c "from email_sender import EmailSender; es = EmailSender(); print('Configuration OK')"

# Test AI connection
python -c "from main_app import test_groq_connection; test_groq_connection('your_api_key')"
```

---

## 🤝 Contributing
Contributions are always welcome!  
Please open a **pull request** or create an **issue** for:
- 🐞 Bug fixes  
- ✨ New features  
- 📚 Documentation updates  
- ⚡ Performance improvements  

**How to contribute:**
1. Fork the repo  
2. Create a feature branch  
3. Make changes  
4. Test thoroughly  
5. Submit PR 🚀  

---

## 📝 License
This project is licensed under the **Unkn0wngb License 1.0** — proprietary software.  
- Private modification is allowed.  
- Redistribution, resale, or public sharing is **strictly prohibited**.  

See the full license in [LICENSE](LICENSE).  

---

## 🐛 Troubleshooting

### SMTP Issues
- Verify SMTP server and port  
- Use App Passwords for Gmail accounts with 2FA  
- Check “Less Secure Apps” settings (if applicable)

### Groq API Issues
- Verify your API key  
- Ensure stable internet connection  
- Check your account for remaining API credits

### Attachment Errors
- Confirm file size < limit  
- Check extension support  
- Ensure files aren’t open elsewhere  

---

## 📞 Support
- Check [Issues](https://github.com/Unkn-0-wngb/AI-Email-Assistant/issues)  
- Create a detailed report with error messages and steps to reproduce  

---

## 🙏 Acknowledgments
- **Groq** for AI inference APIs  
- **Python Community** for open-source libraries  
- **Contributors** who make this project better  

**Developed by [Unkn0wngb](https://github.com/Unkn-0-wngb)**  
> Streamlining professional communication with AI assistance 🚀
