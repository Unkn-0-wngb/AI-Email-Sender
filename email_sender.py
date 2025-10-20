import smtplib
import configparser
import os
import mimetypes
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.image import MIMEImage
from email.mime.application import MIMEApplication
from email import encoders
from groq import Groq
from contact_manager import ContactManager
import re
from datetime import datetime

class EmailSender:
    def __init__(self, config_file='email_config.cfg'):
        self.config = configparser.ConfigParser()
        self.config.read(config_file)
        
        # Initialize contact manager
        self.contact_manager = ContactManager()
        
        # Initialize Groq client
        self.groq_api_key = self.config.get('ai_settings', 'groq_api_key')
        self.model = self.config.get('ai_settings', 'model', fallback='llama-3.1-8b-instant')
        try:
            self.client = Groq(api_key=self.groq_api_key)
        except Exception as e:
            print(f"⚠️  Failed to initialize Groq client: {e}")
            self.client = None
        
        # Load personal info
        self.personal_info = {
            'name': self.config.get('personal_info', 'name'),
            'phone': self.config.get('personal_info', 'phone'),
            'address': self.config.get('personal_info', 'address'),
            'company': self.config.get('personal_info', 'company', fallback=''),
            'position': self.config.get('personal_info', 'position', fallback=''),
            'website': self.config.get('personal_info', 'website', fallback='')
        }
        
        # Load email accounts
        self.email_accounts = self._load_email_accounts()
        self.current_account = self.config.get('email_accounts', 'default_account', fallback='work')
        
        # Load signature settings
        self.signature_settings = {
            'include_phone': self.config.getboolean('signature_settings', 'include_phone', fallback=True),
            'include_address': self.config.getboolean('signature_settings', 'include_address', fallback=False),
            'include_company': self.config.getboolean('signature_settings', 'include_company', fallback=True),
            'include_position': self.config.getboolean('signature_settings', 'include_position', fallback=True),
            'include_website': self.config.getboolean('signature_settings', 'include_website', fallback=True)
        }
        
        # Load assistant settings
        self.assistant_settings = {
            'include_ai_footer': self.config.getboolean('assistant_settings', 'include_ai_footer', fallback=True),
            'ai_footer_text': self.config.get('assistant_settings', 'ai_footer_text', fallback="This email was composed and sent by Joshua's AI Assistant")
        }
        
        # Load attachment settings
        self.attachment_settings = {
            'max_attachment_size': self.config.getint('attachment_settings', 'max_attachment_size', fallback=25),
            'allowed_extensions': [ext.strip() for ext in self.config.get('attachment_settings', 'allowed_extensions', fallback='pdf,doc,docx,txt,jpg,jpeg,png,gif,zip,rar').split(',')]
        }
        
        # Available Groq models
        self.available_models = [
            "llama-3.1-8b-instant",
            "llama-3.1-70b-versatile", 
            "mixtral-8x7b-32768",
            "gemma2-9b-it"
        ]
    
    def _load_email_accounts(self):
        """Load all configured email accounts"""
        accounts = {}
        
        # Get list of account names from email_accounts section
        if self.config.has_section('email_accounts'):
            for key, value in self.config.items('email_accounts'):
                if key.endswith('_email') and key != 'default_account':
                    account_name = key.replace('_email', '')
                    if self.config.has_section(account_name + '_email'):
                        account_section = account_name + '_email'
                        accounts[account_name] = {
                            'email': value,
                            'smtp_server': self.config.get(account_section, 'smtp_server'),
                            'smtp_port': self.config.getint(account_section, 'smtp_port'),
                            'smtp_username': self.config.get(account_section, 'smtp_username'),
                            'smtp_password': self.config.get(account_section, 'smtp_password'),
                            'display_name': self.config.get(account_section, 'display_name', fallback='')
                        }
        
        # If no accounts found, create a default one
        if not accounts:
            accounts['default'] = {
                'email': 'default@example.com',
                'smtp_server': 'smtp.gmail.com',
                'smtp_port': 587,
                'smtp_username': 'default@example.com',
                'smtp_password': 'password',
                'display_name': 'Default Account'
            }
        
        return accounts
    
    def get_current_account_info(self):
        """Get information for the current email account"""
        return self.email_accounts.get(self.current_account, {})
    
    def select_email_account(self):
        """Allow user to select which email account to use"""
        if len(self.email_accounts) <= 1:
            print(f"📧 Using account: {self.current_account}")
            return self.current_account
        
        print("\n📧 SELECT EMAIL ACCOUNT")
        print("-" * 25)
        
        account_list = list(self.email_accounts.keys())
        for i, account_name in enumerate(account_list, 1):
            account_info = self.email_accounts[account_name]
            current_indicator = " (Current)" if account_name == self.current_account else ""
            print(f"{i}. {account_info['display_name']} - {account_info['email']}{current_indicator}")
        
        print(f"{len(account_list) + 1}. ⚙️  Manage email accounts")
        
        try:
            choice = input(f"\nSelect account (1-{len(account_list) + 1}): ").strip()
            
            if choice.isdigit():
                choice_num = int(choice)
                if 1 <= choice_num <= len(account_list):
                    selected_account = account_list[choice_num - 1]
                    self.current_account = selected_account
                    print(f"✅ Selected account: {self.email_accounts[selected_account]['display_name']}")
                    return selected_account
                elif choice_num == len(account_list) + 1:
                    self.manage_email_accounts()
                    return self.current_account
            else:
                print("❌ Invalid selection")
        except (ValueError, IndexError):
            print("❌ Invalid input")
        
        return self.current_account
    
    def manage_email_accounts(self):
        """Manage email accounts configuration"""
        while True:
            print("\n📧 EMAIL ACCOUNT MANAGEMENT")
            print("=" * 30)
            
            for i, (account_name, account_info) in enumerate(self.email_accounts.items(), 1):
                current_indicator = " (Current)" if account_name == self.current_account else ""
                print(f"{i}. {account_info['display_name']} - {account_info['email']}{current_indicator}")
            
            print(f"{len(self.email_accounts) + 1}. ➕ Add new email account")
            print(f"{len(self.email_accounts) + 2}. ✏️  Edit email account")
            print(f"{len(self.email_accounts) + 3}. 🗑️  Delete email account")
            print(f"{len(self.email_accounts) + 4}. ✅ Set default account")
            print(f"{len(self.email_accounts) + 5}. ↩️  Back to main menu")
            
            try:
                choice = input(f"\nSelect option (1-{len(self.email_accounts) + 5}): ").strip()
                
                if choice.isdigit():
                    choice_num = int(choice)
                    
                    if 1 <= choice_num <= len(self.email_accounts):
                        # Switch to existing account
                        account_list = list(self.email_accounts.keys())
                        self.current_account = account_list[choice_num - 1]
                        print(f"✅ Switched to account: {self.email_accounts[self.current_account]['display_name']}")
                    
                    elif choice_num == len(self.email_accounts) + 1:
                        # Add new account
                        self._add_email_account()
                    
                    elif choice_num == len(self.email_accounts) + 2:
                        # Edit account
                        self._edit_email_account()
                    
                    elif choice_num == len(self.email_accounts) + 3:
                        # Delete account
                        self._delete_email_account()
                    
                    elif choice_num == len(self.email_accounts) + 4:
                        # Set default account
                        self._set_default_account()
                    
                    elif choice_num == len(self.email_accounts) + 5:
                        break
                    
                    else:
                        print("❌ Invalid selection")
                else:
                    print("❌ Invalid input")
            
            except (ValueError, IndexError):
                print("❌ Invalid input")
    
    def _add_email_account(self):
        """Add a new email account"""
        print("\n➕ ADD NEW EMAIL ACCOUNT")
        print("-" * 25)
        
        account_name = input("Account name (e.g., 'work', 'personal'): ").strip().lower()
        if not account_name:
            print("❌ Account name is required")
            return
        
        if account_name in self.email_accounts:
            print("❌ Account name already exists")
            return
        
        email = input("Email address: ").strip()
        if not email:
            print("❌ Email address is required")
            return
        
        smtp_server = input("SMTP server (e.g., smtp.gmail.com): ").strip()
        smtp_port = input("SMTP port (e.g., 587): ").strip()
        smtp_username = input("SMTP username (usually your email): ").strip()
        smtp_password = input("SMTP password/app password: ").strip()
        display_name = input("Display name (e.g., Joshua Lavery-Jones (Work)): ").strip()
        
        # Validate required fields
        if not all([smtp_server, smtp_port, smtp_username, smtp_password]):
            print("❌ All SMTP settings are required")
            return
        
        try:
            smtp_port = int(smtp_port)
        except ValueError:
            print("❌ SMTP port must be a number")
            return
        
        # Save to config
        self.config.set('email_accounts', f'{account_name}_email', email)
        
        account_section = f'{account_name}_email'
        if not self.config.has_section(account_section):
            self.config.add_section(account_section)
        
        self.config.set(account_section, 'smtp_server', smtp_server)
        self.config.set(account_section, 'smtp_port', str(smtp_port))
        self.config.set(account_section, 'smtp_username', smtp_username)
        self.config.set(account_section, 'smtp_password', smtp_password)
        self.config.set(account_section, 'display_name', display_name)
        
        # Save config file
        with open('email_config.cfg', 'w') as configfile:
            self.config.write(configfile)
        
        # Reload accounts
        self.email_accounts = self._load_email_accounts()
        print(f"✅ Email account '{display_name}' added successfully!")
    
    def _edit_email_account(self):
        """Edit an existing email account"""
        if not self.email_accounts:
            print("❌ No email accounts to edit")
            return
        
        print("\n✏️  EDIT EMAIL ACCOUNT")
        account_list = list(self.email_accounts.keys())
        
        for i, account_name in enumerate(account_list, 1):
            account_info = self.email_accounts[account_name]
            print(f"{i}. {account_info['display_name']} - {account_info['email']}")
        
        try:
            choice = int(input(f"\nSelect account to edit (1-{len(account_list)}): ").strip()) - 1
            if 0 <= choice < len(account_list):
                account_name = account_list[choice]
                account_info = self.email_accounts[account_name]
                
                print(f"\nEditing account: {account_info['display_name']}")
                print("Leave blank to keep current value")
                
                new_email = input(f"Email address (current: {account_info['email']}): ").strip() or account_info['email']
                new_smtp_server = input(f"SMTP server (current: {account_info['smtp_server']}): ").strip() or account_info['smtp_server']
                new_smtp_port = input(f"SMTP port (current: {account_info['smtp_port']}): ").strip() or str(account_info['smtp_port'])
                new_smtp_username = input(f"SMTP username (current: {account_info['smtp_username']}): ").strip() or account_info['smtp_username']
                new_smtp_password = input("SMTP password (enter to keep current): ").strip() or account_info['smtp_password']
                new_display_name = input(f"Display name (current: {account_info['display_name']}): ").strip() or account_info['display_name']
                
                try:
                    new_smtp_port = int(new_smtp_port)
                except ValueError:
                    print("❌ SMTP port must be a number")
                    return
                
                # Update config
                self.config.set('email_accounts', f'{account_name}_email', new_email)
                
                account_section = f'{account_name}_email'
                self.config.set(account_section, 'smtp_server', new_smtp_server)
                self.config.set(account_section, 'smtp_port', str(new_smtp_port))
                self.config.set(account_section, 'smtp_username', new_smtp_username)
                self.config.set(account_section, 'smtp_password', new_smtp_password)
                self.config.set(account_section, 'display_name', new_display_name)
                
                # Save config file
                with open('email_config.cfg', 'w') as configfile:
                    self.config.write(configfile)
                
                # Reload accounts
                self.email_accounts = self._load_email_accounts()
                print(f"✅ Email account updated successfully!")
            else:
                print("❌ Invalid selection")
        except (ValueError, IndexError):
            print("❌ Invalid input")
    
    def _delete_email_account(self):
        """Delete an email account"""
        if len(self.email_accounts) <= 1:
            print("❌ Cannot delete the only email account")
            return
        
        print("\n🗑️  DELETE EMAIL ACCOUNT")
        account_list = list(self.email_accounts.keys())
        
        for i, account_name in enumerate(account_list, 1):
            account_info = self.email_accounts[account_name]
            print(f"{i}. {account_info['display_name']} - {account_info['email']}")
        
        try:
            choice = int(input(f"\nSelect account to delete (1-{len(account_list)}): ").strip()) - 1
            if 0 <= choice < len(account_list):
                account_name = account_list[choice]
                account_info = self.email_accounts[account_name]
                
                confirm = input(f"Are you sure you want to delete account '{account_info['display_name']}'? (y/n): ").lower().strip()
                if confirm == 'y':
                    # Remove from config
                    self.config.remove_option('email_accounts', f'{account_name}_email')
                    
                    account_section = f'{account_name}_email'
                    if self.config.has_section(account_section):
                        self.config.remove_section(account_section)
                    
                    # Update default account if needed
                    if self.current_account == account_name:
                        new_default = list(self.email_accounts.keys())[0]
                        if new_default != account_name:
                            self.current_account = new_default
                            self.config.set('email_accounts', 'default_account', new_default)
                    
                    # Save config file
                    with open('email_config.cfg', 'w') as configfile:
                        self.config.write(configfile)
                    
                    # Reload accounts
                    self.email_accounts = self._load_email_accounts()
                    print(f"✅ Email account deleted successfully!")
            else:
                print("❌ Invalid selection")
        except (ValueError, IndexError):
            print("❌ Invalid input")
    
    def _set_default_account(self):
        """Set the default email account"""
        if not self.email_accounts:
            print("❌ No email accounts available")
            return
        
        print("\n⭐ SET DEFAULT EMAIL ACCOUNT")
        account_list = list(self.email_accounts.keys())
        
        for i, account_name in enumerate(account_list, 1):
            account_info = self.email_accounts[account_name]
            current_indicator = " (Current Default)" if account_name == self.current_account else ""
            print(f"{i}. {account_info['display_name']} - {account_info['email']}{current_indicator}")
        
        try:
            choice = int(input(f"\nSelect default account (1-{len(account_list)}): ").strip()) - 1
            if 0 <= choice < len(account_list):
                account_name = account_list[choice]
                self.current_account = account_name
                self.config.set('email_accounts', 'default_account', account_name)
                
                # Save config file
                with open('email_config.cfg', 'w') as configfile:
                    self.config.write(configfile)
                
                print(f"✅ Default account set to: {self.email_accounts[account_name]['display_name']}")
            else:
                print("❌ Invalid selection")
        except (ValueError, IndexError):
            print("❌ Invalid input")
    
    def handle_recipient(self, recipient_name: str) -> tuple:
        """Enhanced recipient handling with contact management"""
        existing_contact = self.contact_manager.find_contact(recipient_name)
        
        if existing_contact:
            existing_emails = existing_contact.get('emails', [])
            
            print(f"\n📧 Contact '{recipient_name}' found!")
            print(f"Existing emails: {', '.join(existing_emails)}")
            
            while True:
                print("\nChoose option:")
                print("1. ✅ Use existing email(s)")
                print("2. ➕ Add new email to this contact")
                print("3. 👤 Create new contact with this name")
                print("4. ✏️  Edit this contact")
                print("5. ❌ Cancel")
                
                choice = input("Select option (1-5): ").strip()
                
                if choice == '1':
                    # Use existing emails
                    selected_emails = self.select_emails(recipient_name, existing_emails)
                    if selected_emails:
                        return recipient_name, selected_emails
                    else:
                        print("❌ No emails selected")
                
                elif choice == '2':
                    # Add new email to existing contact
                    if self.contact_manager.add_email_to_contact(recipient_name):
                        # Refresh contact data
                        updated_contact = self.contact_manager.find_contact(recipient_name)
                        updated_emails = updated_contact.get('emails', [])
                        selected_emails = self.select_emails(recipient_name, updated_emails)
                        if selected_emails:
                            return recipient_name, selected_emails
                    else:
                        print("❌ Failed to add email to contact")
                
                elif choice == '3':
                    # Create new contact with similar name
                    new_name = f"{recipient_name} ({len([c for c in self.contact_manager.list_contacts() if recipient_name in c]) + 1})"
                    if self.contact_manager.create_contact_with_name(new_name):
                        new_contact = self.contact_manager.find_contact(new_name)
                        if new_contact and new_contact.get('emails'):
                            return new_name, [new_contact['emails'][0]]
                    else:
                        print("❌ Failed to create new contact")
                
                elif choice == '4':
                    # Edit existing contact
                    self.contact_manager.edit_contact(recipient_name)
                    # After editing, show updated emails
                    updated_contact = self.contact_manager.find_contact(recipient_name)
                    existing_emails = updated_contact.get('emails', [])
                    print(f"Updated emails: {', '.join(existing_emails)}")
                
                elif choice == '5':
                    return None, []
                
                else:
                    print("❌ Invalid choice")
        else:
            # New contact - create with comprehensive information
            print(f"\n👤 '{recipient_name}' not found in contacts.")
            create_new = input("Create new contact? (y/n): ").lower().strip()
            
            if create_new == 'y':
                if self.contact_manager.create_contact_with_name(recipient_name):
                    # Get the created contact
                    new_contact = self.contact_manager.find_contact(recipient_name)
                    if new_contact and new_contact.get('emails'):
                        return recipient_name, [new_contact['emails'][0]]
                    else:
                        print("❌ Failed to create contact or no emails added")
                        return None, []
                else:
                    return None, []
            else:
                # Just use without saving to contacts
                email = input(f"Enter email for {recipient_name} (not saved to contacts): ").strip()
                if email and self.validate_email(email):
                    return recipient_name, [email]
                else:
                    print("❌ Invalid email")
                    return None, []
    
    def select_emails(self, contact_name: str, available_emails: list) -> list:
        """Let user select which emails to send to"""
        if len(available_emails) == 1:
            return available_emails
        
        print(f"\n📧 Select emails for {contact_name}:")
        for i, email in enumerate(available_emails, 1):
            print(f"{i}. {email}")
        print(f"{len(available_emails) + 1}. ✅ Send to all")
        print(f"{len(available_emails) + 2}. ❌ Cancel")
        
        while True:
            try:
                choice = input(f"\nSelect option (1-{len(available_emails) + 2}): ").strip()
                
                if choice == str(len(available_emails) + 1):
                    return available_emails
                elif choice == str(len(available_emails) + 2):
                    return []
                else:
                    selected_indices = [int(c.strip()) - 1 for c in choice.split(',') if c.strip().isdigit()]
                    selected_emails = [available_emails[i] for i in selected_indices if 0 <= i < len(available_emails)]
                    
                    if selected_emails:
                        return selected_emails
                    else:
                        print("❌ No valid emails selected")
            except (ValueError, IndexError):
                print("❌ Invalid input")
    
    def manage_attachments(self) -> list:
        """Manage file attachments for the email"""
        attachments = []
        
        print("\n📎 ATTACHMENT MANAGEMENT")
        print("-" * 25)
        
        while True:
            print(f"\nCurrent attachments: {len(attachments)} file(s)")
            for i, attachment in enumerate(attachments, 1):
                print(f"  {i}. {os.path.basename(attachment)}")
            
            print("\nOptions:")
            print("1. ➕ Add attachment")
            print("2. 🗑️  Remove attachment")
            print("3. 🔗 Add clickable link")
            print("4. ✅ Finished with attachments")
            
            choice = input("\nSelect option (1-4): ").strip()
            
            if choice == '1':
                file_path = input("Enter file path to attach: ").strip()
                if file_path:
                    if self.validate_attachment(file_path):
                        attachments.append(file_path)
                        print(f"✅ Added attachment: {os.path.basename(file_path)}")
                    else:
                        print("❌ Invalid file or file too large")
                else:
                    print("❌ No file path provided")
            
            elif choice == '2' and attachments:
                try:
                    index = int(input("Enter attachment number to remove: ").strip()) - 1
                    if 0 <= index < len(attachments):
                        removed = attachments.pop(index)
                        print(f"✅ Removed attachment: {os.path.basename(removed)}")
                    else:
                        print("❌ Invalid attachment number")
                except ValueError:
                    print("❌ Invalid input")
            
            elif choice == '3':
                link_url = input("Enter URL: ").strip()
                link_text = input("Enter link text (optional): ").strip()
                
                if link_url:
                    if not link_url.startswith(('http://', 'https://')):
                        link_url = 'https://' + link_url
                    
                    link_markdown = f"[{link_text or link_url}]({link_url})"
                    # Create a temporary file for the link
                    link_file = f"link_{len(attachments)}.txt"
                    try:
                        with open(link_file, 'w') as f:
                            f.write(f"Clickable Link: {link_text or link_url}\nURL: {link_url}")
                        attachments.append(link_file)
                        print(f"✅ Added clickable link: {link_text or link_url}")
                    except Exception as e:
                        print(f"❌ Failed to create link file: {e}")
                else:
                    print("❌ URL is required")
            
            elif choice == '4':
                break
            
            else:
                print("❌ Invalid choice")
        
        return attachments
    
    def validate_attachment(self, file_path: str) -> bool:
        """Validate if a file can be attached"""
        if not os.path.exists(file_path):
            print("❌ File does not exist")
            return False
        
        if not os.path.isfile(file_path):
            print("❌ Path is not a file")
            return False
        
        # Check file size (in MB)
        file_size = os.path.getsize(file_path) / (1024 * 1024)  # Convert to MB
        max_size = self.attachment_settings['max_attachment_size']
        
        if file_size > max_size:
            print(f"❌ File too large: {file_size:.2f}MB (max: {max_size}MB)")
            return False
        
        # Check file extension
        file_ext = os.path.splitext(file_path)[1].lower().lstrip('.')
        allowed_extensions = self.attachment_settings['allowed_extensions']
        
        if file_ext not in allowed_extensions:
            print(f"❌ File type not allowed: .{file_ext}")
            print(f"✅ Allowed types: {', '.join(allowed_extensions)}")
            return False
        
        return True
    
    def generate_email_content(self, recipient_name: str, message_request: str, tone_option: str, attachments: list = None) -> str:
        """Generate email content using Groq AI with AI footer and attachment awareness"""
        
        # If Groq client is not available, use fallback immediately
        if not self.client:
            return self._create_fallback_email(recipient_name, message_request, tone_option, attachments)
        
        tone_prompts = {
            "Formal (Full)": """Write a very formal and professional email. Use complete formal structure with detailed footer.
            Include: formal greeting, professional language, complete contact information in signature.""",
            
            "Formal": """Write a formal professional email with standard business formatting.
            Use professional language but slightly less rigid than full formal.""",
            
            "Formal + Casual": """Write an email that is professional but slightly casual, suitable for workplace colleagues.
            Balance professionalism with approachability.""",
            
            "Casual": """Write a casual email that is friendly but still somewhat professional.
            Use relaxed language but maintain clarity and purpose.""",
            
            "Casual + Friendly": """Write a very friendly and casual email, like you're writing to a friend.
            Use warm, personal language while conveying the message clearly."""
        }
        
        signature_template = self._generate_signature(tone_option)
        ai_footer = self._generate_ai_footer()
        
        # Add attachment context to prompt
        attachment_context = ""
        if attachments:
            attachment_names = [os.path.basename(att) for att in attachments if not att.startswith('link_')]
            link_files = [att for att in attachments if att.startswith('link_')]
            
            if attachment_names:
                attachment_context = f"\nATTACHMENTS INCLUDED: {', '.join(attachment_names)}"
            
            if link_files:
                links_info = []
                for link_file in link_files:
                    try:
                        with open(link_file, 'r') as f:
                            link_content = f.read()
                            # Extract URL from link file content
                            if 'URL: ' in link_content:
                                url = link_content.split('URL: ')[1].strip()
                                link_text = link_content.split('\n')[0].replace('Clickable Link: ', '')
                                links_info.append(f"{link_text} ({url})")
                    except:
                        pass
                
                if links_info:
                    attachment_context += f"\nLINKS INCLUDED: {', '.join(links_info)}"
        
        prompt = f"""
        TASK: Write a complete email to {recipient_name}.
        
        CORE MESSAGE: {message_request}
        {attachment_context}
        
        TONE: {tone_option}
        TONE GUIDELINES: {tone_prompts.get(tone_option, "Professional")}
        
        SIGNATURE TEMPLATE (use this exact format):
        {signature_template}
        
        AI FOOTER (add this at the very end, after signature):
        {ai_footer}
        
        REQUIREMENTS:
        1. Include a relevant subject line starting with "Subject:"
        2. Use appropriate greeting based on tone
        3. Write clear body content conveying the core message
        4. If there are attachments, briefly mention them in the body
        5. If there are links, mention them naturally in the body
        6. Include the provided signature template at the end
        7. Add the AI footer after the signature
        8. Return ONLY the email content, no additional commentary
        
        FORMAT:
        Subject: [Your Subject Here]
        
        [Email Body Here]
        """
        
        try:
            chat_completion = self.client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert email writer. Create professional, well-structured emails that match the requested tone and include the provided signature and AI footer. Naturally mention any attachments or links in the email body."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                model=self.model,
                temperature=0.7,
                max_tokens=1024,
                top_p=1,
                stream=False,
            )
            
            return chat_completion.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"⚠️  AI generation failed: {str(e)}")
            return self._create_fallback_email(recipient_name, message_request, tone_option, attachments)
    
    def _generate_ai_footer(self) -> str:
        """Generate the AI assistant footer"""
        if not self.assistant_settings['include_ai_footer']:
            return ""
        
        first_name = self.personal_info['name'].split()[0]
        footer_text = self.assistant_settings['ai_footer_text']
        
        # Replace placeholder with actual first name
        footer_text = footer_text.replace("{Your First Name}", first_name)
        
        return f"\n\n--\n{footer_text}"
    
    def _generate_signature(self, tone_option: str) -> str:
        """Generate signature based on tone option and settings"""
        
        name = self.personal_info['name']
        current_account_info = self.get_current_account_info()
        email = current_account_info.get('email', '')
        phone = self.personal_info['phone'] if self.signature_settings['include_phone'] else ""
        address = self.personal_info['address'] if self.signature_settings['include_address'] else ""
        company = self.personal_info['company'] if self.signature_settings['include_company'] else ""
        position = self.personal_info['position'] if self.signature_settings['include_position'] else ""
        website = self.personal_info['website'] if self.signature_settings['include_website'] and self.personal_info['website'] != 'N/A' else ""
        
        if tone_option == "Formal (Full)":
            signature = f"Sincerely,\n\n{name}"
            if position and company:
                signature += f"\n{position}, {company}"
            elif position:
                signature += f"\n{position}"
            elif company:
                signature += f"\n{company}"
            if email:
                signature += f"\nEmail: {email}"
            if phone:
                signature += f"\nPhone: {phone}"
            if address:
                signature += f"\nAddress: {address}"
            if website:
                signature += f"\nWebsite: {website}"
            return signature
        
        elif tone_option == "Formal":
            signature = f"Best regards,\n\n{name}"
            if position or company:
                signature += f"\n{position + ' | ' if position else ''}{company}"
            if email:
                signature += f"\n{email}"
            if phone:
                signature += f" | {phone}"
            return signature
        
        elif tone_option == "Formal + Casual":
            signature = f"Best,\n\n{name}"
            if position:
                signature += f"\n{position}"
            if email:
                signature += f"\n{email}"
            return signature
        
        elif tone_option == "Casual":
            return f"Cheers,\n\n{name}\n{email}"
        
        elif tone_option == "Casual + Friendly":
            return f"All the best,\n\n{name.split()[0]}"
        
        else:
            return f"Best regards,\n\n{name}\n{email}"
    
    def _create_fallback_email(self, recipient_name: str, message_request: str, tone_option: str, attachments: list = None) -> str:
        """Create fallback email template with AI footer and attachment mention"""
        subject = f"Update: {message_request[:50]}..." if len(message_request) > 50 else message_request
        
        greetings = {
            "Formal (Full)": f"Dear {recipient_name},",
            "Formal": f"Dear {recipient_name},",
            "Formal + Casual": f"Hello {recipient_name},",
            "Casual": f"Hi {recipient_name},",
            "Casual + Friendly": f"Hey {recipient_name}!"
        }
        
        # Add attachment mention
        attachment_mention = ""
        if attachments:
            file_attachments = [os.path.basename(att) for att in attachments if not att.startswith('link_')]
            link_attachments = []
            
            for att in attachments:
                if att.startswith('link_'):
                    try:
                        with open(att, 'r') as f:
                            link_content = f.read()
                            link_text = link_content.split('\n')[0].replace('Clickable Link: ', '')
                            link_attachments.append(link_text)
                    except:
                        pass
            
            if file_attachments:
                attachment_mention = f"\n\nI've attached {', '.join(file_attachments)} for your reference."
            
            if link_attachments:
                attachment_mention += f"\n\nHere are some useful links: {', '.join(link_attachments)}"
        
        body = f"""
{greetings.get(tone_option, f"Dear {recipient_name},")}

I hope this message finds you well.

{message_request}{attachment_mention}

Please let me know if you have any questions or need additional information.

{self._generate_signature(tone_option)}
{self._generate_ai_footer()}
"""
        return f"Subject: {subject}\n\n{body}"
    
    def parse_generated_content(self, content: str) -> tuple:
        """Parse AI-generated content into subject and body"""
        lines = content.split('\n')
        subject = ""
        body_lines = []
        found_subject = False
        
        for line in lines:
            stripped_line = line.strip()
            if (stripped_line.startswith('Subject:') or stripped_line.startswith('SUBJECT:')) and not found_subject:
                subject = stripped_line.split(':', 1)[1].strip()
                found_subject = True
            else:
                body_lines.append(line)
        
        if not subject:
            subject = "Important Message"
        
        body = '\n'.join(body_lines).strip()
        return subject, body
    
    def edit_email_content(self, subject: str, body: str) -> tuple:
        """Allow user to edit email content with advanced options"""
        while True:
            print("\n" + "="*60)
            print("✏️  EMAIL EDITING OPTIONS")
            print("="*60)
            print(f"Current Subject: {subject}")
            print(f"Current Body:\n{body}")
            print("="*60)
            
            print("\nEditing Options:")
            print("1. ✏️  Edit subject only")
            print("2. 📝 Edit body only")
            print("3. 🔄 Edit both subject and body")
            print("4. 🎯 Quick edit - Replace specific text")
            print("5. 🔗 Insert clickable link")
            print("6. ✅ Finalize and continue")
            
            edit_choice = input("\nSelect option (1-6): ").strip()
            
            if edit_choice == '1':
                new_subject = input("Enter new subject: ").strip()
                if new_subject:
                    subject = new_subject
                    print("✅ Subject updated!")
            
            elif edit_choice == '2':
                print("\nEnter new body (press Enter twice to finish):")
                new_body_lines = []
                empty_lines = 0
                
                while empty_lines < 2:
                    try:
                        line = input()
                        if line.strip() == "":
                            empty_lines += 1
                        else:
                            empty_lines = 0
                        new_body_lines.append(line)
                    except EOFError:
                        break
                
                new_body = '\n'.join(new_body_lines[:-1])  # Remove the two empty lines
                if new_body.strip():
                    body = new_body
                    print("✅ Body updated!")
                else:
                    print("❌ Body cannot be empty")
            
            elif edit_choice == '3':
                new_subject = input("Enter new subject: ").strip()
                print("Enter new body (press Enter twice to finish):")
                new_body_lines = []
                empty_lines = 0
                
                while empty_lines < 2:
                    try:
                        line = input()
                        if line.strip() == "":
                            empty_lines += 1
                        else:
                            empty_lines = 0
                        new_body_lines.append(line)
                    except EOFError:
                        break
                
                new_body = '\n'.join(new_body_lines[:-1])
                if new_subject and new_body.strip():
                    subject = new_subject
                    body = new_body
                    print("✅ Subject and body updated!")
                else:
                    print("❌ Subject and body cannot be empty")
            
            elif edit_choice == '4':
                # Quick text replacement
                search_text = input("Text to replace: ").strip()
                replace_text = input("Replace with: ").strip()
                
                if search_text in body:
                    body = body.replace(search_text, replace_text)
                    print("✅ Text replaced!")
                else:
                    print("❌ Text not found in body")
            
            elif edit_choice == '5':
                # Insert clickable link
                link_url = input("Enter URL: ").strip()
                link_text = input("Enter link text (optional): ").strip()
                
                if link_url:
                    if not link_url.startswith(('http://', 'https://')):
                        link_url = 'https://' + link_url
                    
                    link_markdown = f"[{link_text or link_url}]({link_url})"
                    
                    print("\nWhere would you like to insert the link?")
                    print("1. At cursor position (will be marked with {{LINK}})")
                    print("2. At the end of the email")
                    
                    pos_choice = input("Select option (1-2): ").strip()
                    
                    if pos_choice == '1':
                        body += f"\n\n[Insert link here: {link_markdown}]"
                        print("✅ Link marker added. Please position it manually in the body.")
                    else:
                        body += f"\n\nUseful link: {link_markdown}"
                        print("✅ Link added to the end of the email")
                else:
                    print("❌ URL is required")
            
            elif edit_choice == '6':
                break
            
            else:
                print("❌ Invalid choice")
        
        return subject, body
    
    def send_email(self, recipient_emails: list, subject: str, body: str, attachments: list = None) -> bool:
        """Send email to multiple recipients with attachments using current account"""
        success_count = 0
        total_emails = len(recipient_emails)
        
        # Get current account info
        account_info = self.get_current_account_info()
        if not account_info:
            print("❌ No email account configured")
            return False
        
        print(f"\n📤 Sending email from: {account_info['display_name']}")
        print(f"📧 To: {total_emails} recipient(s)...")
        if attachments:
            print(f"📎 With {len(attachments)} attachment(s)")
        
        for i, recipient_email in enumerate(recipient_emails, 1):
            try:
                # Create message container
                msg = MIMEMultipart()
                
                # Set From field with display name
                from_name = account_info['display_name'] or self.personal_info['name']
                msg['From'] = f'{from_name} <{account_info["email"]}>'
                msg['To'] = recipient_email
                msg['Subject'] = subject
                
                # Attach body text
                msg.attach(MIMEText(body, 'plain'))
                
                # Attach files
                if attachments:
                    for file_path in attachments:
                        if file_path.startswith('link_'):
                            # Skip link files (they're not real attachments)
                            continue
                        try:
                            with open(file_path, 'rb') as file:
                                # Guess the MIME type
                                mime_type, encoding = mimetypes.guess_type(file_path)
                                if mime_type is None or encoding is not None:
                                    mime_type = 'application/octet-stream'
                                
                                main_type, sub_type = mime_type.split('/', 1)
                                
                                if main_type == 'text':
                                    attachment = MIMEText(file.read().decode('utf-8'), _subtype=sub_type)
                                elif main_type == 'image':
                                    attachment = MIMEImage(file.read(), _subtype=sub_type)
                                elif main_type == 'application':
                                    attachment = MIMEApplication(file.read(), _subtype=sub_type)
                                else:
                                    attachment = MIMEBase(main_type, sub_type)
                                    attachment.set_payload(file.read())
                                    encoders.encode_base64(attachment)
                                
                                # Add header
                                filename = os.path.basename(file_path)
                                attachment.add_header('Content-Disposition', f'attachment; filename="{filename}"')
                                msg.attach(attachment)
                                
                        except Exception as e:
                            print(f"⚠️  Failed to attach {file_path}: {str(e)}")
                
                # Send email
                with smtplib.SMTP(account_info['smtp_server'], account_info['smtp_port']) as server:
                    server.starttls()
                    server.login(account_info['smtp_username'], account_info['smtp_password'])
                    server.send_message(msg)
                
                print(f"✅ [{i}/{total_emails}] Email sent to {recipient_email}")
                success_count += 1
                
            except Exception as e:
                print(f"❌ [{i}/{total_emails}] Failed to send to {recipient_email}: {str(e)}")
        
        # Clean up temporary link files
        if attachments:
            for file_path in attachments:
                if file_path.startswith('link_') and os.path.exists(file_path):
                    try:
                        os.remove(file_path)
                    except:
                        pass
        
        print(f"\n📊 Sent {success_count} out of {total_emails} emails successfully")
        return success_count > 0
    
    def preview_email(self, recipient_name: str, subject: str, body: str, tone_option: str, attachments: list = None):
        """Preview email content with attachments"""
        account_info = self.get_current_account_info()
        from_display = account_info.get('display_name', '') if account_info else ''
        
        print("\n" + "="*70)
        print("📧 EMAIL PREVIEW")
        print("="*70)
        print(f"From: {from_display}")
        print(f"To: {recipient_name}")
        print(f"Subject: {subject}")
        print(f"Tone: {tone_option}")
        
        if attachments:
            file_attachments = [os.path.basename(att) for att in attachments if not att.startswith('link_')]
            link_attachments = []
            
            for att in attachments:
                if att.startswith('link_'):
                    try:
                        with open(att, 'r') as f:
                            link_content = f.read()
                            link_text = link_content.split('\n')[0].replace('Clickable Link: ', '')
                            link_attachments.append(link_text)
                    except:
                        pass
            
            if file_attachments:
                print(f"📎 Attachments: {', '.join(file_attachments)}")
            if link_attachments:
                print(f"🔗 Links: {', '.join(link_attachments)}")
        
        print("-" * 70)
        print(body)
        print("="*70)
    
    def manage_signature_settings(self):
        """Allow user to customize signature settings"""
        print("\n📝 SIGNATURE SETTINGS")
        print("=" * 30)
        
        for setting, current_value in self.signature_settings.items():
            friendly_name = setting.replace('_', ' ').title()
            new_value = input(f"Include {friendly_name}? (current: {'Yes' if current_value else 'No'}) (y/n): ").lower().strip()
            if new_value in ['y', 'yes']:
                self.signature_settings[setting] = True
            elif new_value in ['n', 'no']:
                self.signature_settings[setting] = False
        
        # Save to config file
        for setting, value in self.signature_settings.items():
            self.config.set('signature_settings', setting, 'yes' if value else 'no')
        
        with open('email_config.cfg', 'w') as configfile:
            self.config.write(configfile)
        
        print("✅ Signature settings updated!")
    
    def manage_assistant_settings(self):
        """Allow user to customize AI assistant settings"""
        print("\n🤖 AI ASSISTANT SETTINGS")
        print("=" * 30)
        
        # AI Footer setting
        current_footer = self.assistant_settings['include_ai_footer']
        footer_choice = input(f"Include AI assistant footer? (current: {'Yes' if current_footer else 'No'}) (y/n): ").lower().strip()
        self.assistant_settings['include_ai_footer'] = footer_choice in ['y', 'yes']
        
        # Custom footer text
        if self.assistant_settings['include_ai_footer']:
            current_text = self.assistant_settings['ai_footer_text']
            new_text = input(f"Footer text (current: {current_text}): ").strip()
            if new_text:
                self.assistant_settings['ai_footer_text'] = new_text
        
        # Save to config file
        self.config.set('assistant_settings', 'include_ai_footer', 
                       'yes' if self.assistant_settings['include_ai_footer'] else 'no')
        self.config.set('assistant_settings', 'ai_footer_text', 
                       self.assistant_settings['ai_footer_text'])
        
        with open('email_config.cfg', 'w') as configfile:
            self.config.write(configfile)
        
        print("✅ AI assistant settings updated!")
    
    def manage_attachment_settings(self):
        """Allow user to customize attachment settings"""
        print("\n📎 ATTACHMENT SETTINGS")
        print("=" * 30)
        
        # Max attachment size
        current_size = self.attachment_settings['max_attachment_size']
        new_size = input(f"Maximum attachment size in MB (current: {current_size}): ").strip()
        if new_size and new_size.isdigit():
            self.attachment_settings['max_attachment_size'] = int(new_size)
        
        # Allowed extensions
        current_extensions = ', '.join(self.attachment_settings['allowed_extensions'])
        new_extensions = input(f"Allowed file extensions (comma-separated, current: {current_extensions}): ").strip()
        if new_extensions:
            self.attachment_settings['allowed_extensions'] = [ext.strip() for ext in new_extensions.split(',')]
        
        # Save to config file
        self.config.set('attachment_settings', 'max_attachment_size', 
                       str(self.attachment_settings['max_attachment_size']))
        self.config.set('attachment_settings', 'allowed_extensions', 
                       ', '.join(self.attachment_settings['allowed_extensions']))
        
        with open('email_config.cfg', 'w') as configfile:
            self.config.write(configfile)
        
        print("✅ Attachment settings updated!")
    
    def validate_email(self, email: str) -> bool:
        """Validate email format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None