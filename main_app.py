from email_sender import EmailSender
from contact_manager import ContactManager
import os
import json
from datetime import datetime

def clear_screen():
    """Clear terminal screen"""
    os.system('cls' if os.name == 'nt' else 'clear')

def test_groq_connection(api_key, model='llama-3.1-8b-instant'):
    """Test Groq API connection"""
    from groq import Groq
    try:
        client = Groq(api_key=api_key)
        chat_completion = client.chat.completions.create(
            messages=[{"role": "user", "content": "Say 'Hello' in a short message."}],
            model=model,
            max_tokens=10,
        )
        print(f"✅ Groq API connection successful with model: {model}")
        return True
    except Exception as e:
        print(f"❌ Groq API connection failed: {str(e)}")
        return False

def save_draft(draft_data):
    """Save email draft to JSON file"""
    try:
        drafts_file = 'email_drafts.json'
        drafts = []
        
        # Load existing drafts
        if os.path.exists(drafts_file):
            with open(drafts_file, 'r', encoding='utf-8') as file:
                drafts = json.load(file)
        
        # Add new draft
        draft_data['created_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        draft_data['id'] = len(drafts) + 1
        drafts.append(draft_data)
        
        # Save back to file
        with open(drafts_file, 'w', encoding='utf-8') as file:
            json.dump(drafts, file, indent=2, ensure_ascii=False)
        
        return True
    except Exception as e:
        print(f"❌ Error saving draft: {e}")
        return False

def load_drafts():
    """Load all saved drafts"""
    try:
        drafts_file = 'email_drafts.json'
        if os.path.exists(drafts_file):
            with open(drafts_file, 'r', encoding='utf-8') as file:
                return json.load(file)
        return []
    except Exception as e:
        print(f"❌ Error loading drafts: {e}")
        return []

def delete_draft(draft_id):
    """Delete a draft by ID"""
    try:
        drafts_file = 'email_drafts.json'
        drafts = load_drafts()
        
        # Remove draft with matching ID
        drafts = [draft for draft in drafts if draft.get('id') != draft_id]
        
        # Save updated list
        with open(drafts_file, 'w', encoding='utf-8') as file:
            json.dump(drafts, file, indent=2, ensure_ascii=False)
        
        return True
    except Exception as e:
        print(f"❌ Error deleting draft: {e}")
        return False

def manage_drafts_flow(email_sender):
    """Manage saved email drafts"""
    while True:
        drafts = load_drafts()
        
        print("\n💾 MANAGING DRAFTS")
        print("=" * 30)
        
        if not drafts:
            print("📭 No saved drafts found")
            print("\n1. ↩️ Back to main menu")
            choice = input("Select option: ").strip()
            if choice == '1':
                break
            continue
        
        print(f"Found {len(drafts)} draft(s):")
        for i, draft in enumerate(drafts, 1):
            print(f"{i}. {draft.get('name', 'Unnamed Draft')} - {draft.get('created_at', 'Unknown date')}")
        
        print(f"\nOptions:")
        print(f"{len(drafts) + 1}. 👀 View and edit draft")
        print(f"{len(drafts) + 2}. 🗑️ Delete draft")
        print(f"{len(drafts) + 3}. ↩️ Back to main menu")
        
        try:
            choice = input(f"\nSelect option (1-{len(drafts) + 3}): ").strip()
            
            if choice.isdigit():
                choice_num = int(choice)
                
                if 1 <= choice_num <= len(drafts):
                    # Load and send draft
                    draft = drafts[choice_num - 1]
                    if load_and_send_draft(email_sender, draft):
                        print("✅ Draft processed successfully!")
                
                elif choice_num == len(drafts) + 1:
                    # View and edit specific draft
                    draft_choice = input(f"Enter draft number to view (1-{len(drafts)}): ").strip()
                    if draft_choice.isdigit():
                        draft_num = int(draft_choice) - 1
                        if 0 <= draft_num < len(drafts):
                            view_and_edit_draft(email_sender, drafts[draft_num])
                        else:
                            print("❌ Invalid draft number")
                    else:
                        print("❌ Invalid input")
                
                elif choice_num == len(drafts) + 2:
                    # Delete draft
                    draft_choice = input(f"Enter draft number to delete (1-{len(drafts)}): ").strip()
                    if draft_choice.isdigit():
                        draft_num = int(draft_choice) - 1
                        if 0 <= draft_num < len(drafts):
                            draft_id = drafts[draft_num].get('id')
                            if delete_draft(draft_id):
                                print("✅ Draft deleted successfully!")
                            else:
                                print("❌ Failed to delete draft")
                        else:
                            print("❌ Invalid draft number")
                    else:
                        print("❌ Invalid input")
                
                elif choice_num == len(drafts) + 3:
                    break
                
                else:
                    print("❌ Invalid selection")
            else:
                print("❌ Invalid input")
        
        except (ValueError, IndexError):
            print("❌ Invalid input")

def view_and_edit_draft(email_sender, draft):
    """View and edit a specific draft"""
    print(f"\n📝 EDITING DRAFT: {draft.get('name', 'Unnamed Draft')}")
    print("=" * 50)
    
    print(f"Recipient: {draft.get('recipient_name', 'Unknown')}")
    print(f"Subject: {draft.get('subject', 'No subject')}")
    print(f"Tone: {draft.get('tone', 'Formal')}")
    print(f"Created: {draft.get('created_at', 'Unknown')}")
    print(f"\nBody:\n{draft.get('body', 'No content')}")
    print("=" * 50)
    
    while True:
        print("\nEdit Options:")
        print("1. ✏️ Edit draft content")
        print("2. 📤 Send this draft")
        print("3. 🗑️ Delete this draft")
        print("4. ↩️ Back to draft list")
        
        choice = input("Select option (1-4): ").strip()
        
        if choice == '1':
            # Edit draft content
            new_subject = input(f"New subject (current: {draft.get('subject', '')}): ").strip() or draft.get('subject', '')
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
            if new_body.strip():
                draft['subject'] = new_subject
                draft['body'] = new_body
                draft['updated_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                # Save updated draft
                if update_draft(draft):
                    print("✅ Draft updated successfully!")
                else:
                    print("❌ Failed to update draft")
            else:
                print("❌ Body cannot be empty")
        
        elif choice == '2':
            # Send draft
            if load_and_send_draft(email_sender, draft):
                # Delete draft after sending
                delete_draft(draft.get('id'))
                break
        
        elif choice == '3':
            # Delete draft
            if delete_draft(draft.get('id')):
                print("✅ Draft deleted successfully!")
                break
            else:
                print("❌ Failed to delete draft")
        
        elif choice == '4':
            break
        
        else:
            print("❌ Invalid choice")

def update_draft(updated_draft):
    """Update an existing draft"""
    try:
        drafts_file = 'email_drafts.json'
        drafts = load_drafts()
        
        # Find and update the draft
        for i, draft in enumerate(drafts):
            if draft.get('id') == updated_draft.get('id'):
                drafts[i] = updated_draft
                break
        
        # Save back to file
        with open(drafts_file, 'w', encoding='utf-8') as file:
            json.dump(drafts, file, indent=2, ensure_ascii=False)
        
        return True
    except Exception as e:
        print(f"❌ Error updating draft: {e}")
        return False

def load_and_send_draft(email_sender, draft):
    """Load a draft and proceed to send it"""
    recipient_name = draft.get('recipient_name')
    recipient_emails = draft.get('recipient_emails', [])
    subject = draft.get('subject')
    body = draft.get('body')
    tone = draft.get('tone', 'Formal')
    
    if not recipient_emails:
        print("❌ No recipient emails found in draft")
        return False
    
    # Preview and send
    email_sender.preview_email(recipient_name, subject, body, tone)
    
    confirm = input("\nSend this draft? (y/n): ").lower().strip()
    if confirm == 'y':
        success = email_sender.send_email(recipient_emails, subject, body)
        if success:
            print(f"🎉 Draft sent successfully to {recipient_name}!")
            return True
        else:
            print("❌ Failed to send draft")
            return False
    else:
        print("❌ Draft sending cancelled")
        return False

def main():
    clear_screen()
    print("🚀 ENHANCED AI EMAIL SENDER")
    print("=" * 40)
    
    # Initialize email sender
    email_sender = EmailSender()
    
    # Test AI connection
    if not test_groq_connection(email_sender.groq_api_key, email_sender.model):
        print("❌ Please check your Groq API key in the config file.")
        return
    
    while True:
        # Show current email account
        current_account = email_sender.get_current_account_info()
        account_display = f"{current_account.get('display_name', 'Unknown')} - {current_account.get('email', 'No email')}"
        print(f"\n📧 Current Account: {account_display}")
        print("=" * 50)
        
        print("\n📋 MAIN MENU")
        print("1. ✉️  Send Email")
        print("2. 👥 Manage Contacts")
        print("3. 📧 Manage Email Accounts")
        print("4. ⚙️  Signature Settings")
        print("5. 🤖 AI Assistant Settings")
        print("6. 📎 Attachment Settings")
        print("7. 📊 View Statistics")
        print("8. 💾 Manage Drafts")
        print("9. 🚪 Exit")
        
        choice = input("\nSelect option (1-9): ").strip()
        
        if choice == '1':
            send_email_flow(email_sender)
        elif choice == '2':
            manage_contacts_flow(email_sender.contact_manager)
        elif choice == '3':
            email_sender.manage_email_accounts()
        elif choice == '4':
            email_sender.manage_signature_settings()
        elif choice == '5':
            email_sender.manage_assistant_settings()
        elif choice == '6':
            email_sender.manage_attachment_settings()
        elif choice == '7':
            view_statistics(email_sender.contact_manager)
        elif choice == '8':
            manage_drafts_flow(email_sender)
        elif choice == '9':
            print("👋 Goodbye!")
            break
        else:
            print("❌ Invalid choice")

def send_email_flow(email_sender):
    """Handle the enhanced email sending process with attachments"""
    print("\n✉️  SEND EMAIL")
    print("-" * 20)
    
    # Let user select email account for this operation
    print("\n📧 Select sending account:")
    email_sender.select_email_account()
    
    recipient_name = input("Recipient's Name: ").strip()
    if not recipient_name:
        print("❌ Recipient name is required")
        return
    
    # Enhanced contact handling
    contact_result = email_sender.handle_recipient(recipient_name)
    if not contact_result:
        return
    
    contact_name, selected_emails = contact_result
    
    if not selected_emails:
        print("❌ No emails selected")
        return
    
    message_request = input("What should the email say? ").strip()
    if not message_request:
        print("❌ Message is required")
        return
    
    # Tone options
    tone_options = [
        "Formal (Full)",
        "Formal", 
        "Formal + Casual",
        "Casual",
        "Casual + Friendly"
    ]
    
    print("\n📝 Select tone option:")
    for i, option in enumerate(tone_options, 1):
        print(f"   {i}. {option}")
    
    try:
        tone_choice = int(input("\nEnter choice (1-5): ")) - 1
        if 0 <= tone_choice < len(tone_options):
            selected_tone = tone_options[tone_choice]
        else:
            selected_tone = "Formal"
    except (ValueError, IndexError):
        print("Invalid choice, using 'Formal' as default.")
        selected_tone = "Formal"
    
    # Manage attachments
    attachments = email_sender.manage_attachments()
    
    # Generate email
    print("\n🤖 Generating email with AI...")
    generated_content = email_sender.generate_email_content(contact_name, message_request, selected_tone, attachments)
    subject, body = email_sender.parse_generated_content(generated_content)
    
    # Preview and edit loop
    while True:
        email_sender.preview_email(contact_name, subject, body, selected_tone, attachments)
        
        print("\nChoose action:")
        print("1. ✅ Send email now")
        print("2. ✏️  Edit email content")
        print("3. 🔄 Regenerate with AI")
        print("4. 📎 Manage attachments")
        print("5. 📧 Change sending account")
        print("6. 💾 Save as draft")
        print("7. ❌ Cancel")
        
        action = input("Select option (1-7): ").strip()
        
        if action == '1':
            # Send email
            success = email_sender.send_email(selected_emails, subject, body, attachments)
            if success:
                print(f"🎉 Email sent successfully to {len(selected_emails)} recipient(s)!")
                
                # Update last contact time
                contact = email_sender.contact_manager.find_contact(contact_name)
                if contact:
                    contact['last_contact'] = email_sender.contact_manager._get_current_timestamp()
                    email_sender.contact_manager.contacts[contact_name] = contact
                    email_sender.contact_manager.save_contacts()
            break
        
        elif action == '2':
            # Enhanced editing
            subject, body = email_sender.edit_email_content(subject, body)
        
        elif action == '3':
            # Regenerate with AI
            print("🤖 Regenerating email with AI...")
            generated_content = email_sender.generate_email_content(contact_name, message_request, selected_tone, attachments)
            subject, body = email_sender.parse_generated_content(generated_content)
        
        elif action == '4':
            # Manage attachments
            attachments = email_sender.manage_attachments()
            # Regenerate email to include new attachment mentions
            if attachments:
                print("🤖 Updating email to include new attachments...")
                generated_content = email_sender.generate_email_content(contact_name, message_request, selected_tone, attachments)
                subject, body = email_sender.parse_generated_content(generated_content)
        
        elif action == '5':
            # Change sending account
            print("\n📧 Changing sending account...")
            email_sender.select_email_account()
            # Regenerate signature with new email
            print("🤖 Updating signature with new email...")
            generated_content = email_sender.generate_email_content(contact_name, message_request, selected_tone, attachments)
            subject, body = email_sender.parse_generated_content(generated_content)
        
        elif action == '6':
            # Save draft (fully implemented)
            draft_name = input("Enter draft name: ").strip()
            if draft_name:
                draft_data = {
                    'name': draft_name,
                    'recipient_name': contact_name,
                    'recipient_emails': selected_emails,
                    'subject': subject,
                    'body': body,
                    'tone': selected_tone,
                    'message_request': message_request
                }
                
                if save_draft(draft_data):
                    print(f"💾 Draft '{draft_name}' saved successfully!")
                else:
                    print("❌ Failed to save draft")
            else:
                print("❌ Draft name required")
        
        elif action == '7':
            # Clean up temporary link files
            if attachments:
                for file_path in attachments:
                    if file_path.startswith('link_') and os.path.exists(file_path):
                        try:
                            os.remove(file_path)
                        except:
                            pass
            print("❌ Email cancelled.")
            break
        
        else:
            print("❌ Invalid choice")

def manage_contacts_flow(contact_manager):
    """Enhanced contact management with full CRUD operations"""
    while True:
        print("\n👥 CONTACT MANAGEMENT")
        print("1. ➕ Create New Contact")
        print("2. 📋 List All Contacts")
        print("3. 🔍 Search Contacts")
        print("4. ✏️  Edit Contact")
        print("5. 🗑️  Delete Contact")
        print("6. 🏷️  View by Category")
        print("7. 📤 Export Contacts")
        print("8. 📥 Import Contacts")
        print("9. ↩️  Back to Main Menu")
        
        choice = input("\nSelect option (1-9): ").strip()
        
        if choice == '1':
            contact_manager.create_contact()
        
        elif choice == '2':
            contacts = contact_manager.list_contacts()
            if contacts:
                print("\n📋 ALL CONTACTS:")
                for i, contact in enumerate(contacts, 1):
                    details = contact_manager.get_contact_details(contact)
                    if details:
                        emails = details.get('emails', [])
                        category = details.get('category', 'Uncategorized')
                        print(f"{i}. {contact} - {', '.join(emails)} [{category}]")
                    else:
                        print(f"{i}. {contact} - [Error: Contact details not found]")
            else:
                print("📭 No contacts found")
        
        elif choice == '3':
            query = input("Enter search term: ").strip()
            if query:
                results = contact_manager.search_contacts(query)
                if results:
                    print(f"\n🔍 SEARCH RESULTS for '{query}':")
                    for i, contact in enumerate(results, 1):
                        details = contact_manager.get_contact_details(contact)
                        if details:
                            emails = details.get('emails', [])
                            print(f"{i}. {contact} - {', '.join(emails)}")
                        else:
                            print(f"{i}. {contact} - [Error: Contact details not found]")
                else:
                    print("❌ No contacts found")
            else:
                print("❌ Search term required")
        
        elif choice == '4':
            name = input("Enter contact name to edit: ").strip()
            if name:
                contact_manager.edit_contact(name)
            else:
                print("❌ Contact name required")
        
        elif choice == '5':
            name = input("Enter contact name to delete: ").strip()
            if name:
                if contact_manager.delete_contact(name):
                    print("✅ Contact deleted!")
                else:
                    print("❌ Contact not found or deletion failed")
            else:
                print("❌ Contact name required")
        
        elif choice == '6':
            categories = contact_manager.get_contact_categories()
            if categories:
                print("\n🏷️  CATEGORIES:")
                for i, category in enumerate(categories, 1):
                    contacts_in_category = contact_manager.list_contacts(category)
                    print(f"{i}. {category} ({len(contacts_in_category)} contacts)")
                
                try:
                    cat_choice = int(input("\nSelect category: ").strip()) - 1
                    if 0 <= cat_choice < len(categories):
                        selected_category = categories[cat_choice]
                        contacts = contact_manager.list_contacts(selected_category)
                        print(f"\n👥 CONTACTS IN '{selected_category}':")
                        for contact in contacts:
                            details = contact_manager.get_contact_details(contact)
                            if details:
                                emails = details.get('emails', [])
                                print(f"  • {contact} - {', '.join(emails)}")
                            else:
                                print(f"  • {contact} - [Error: Contact details not found]")
                    else:
                        print("❌ Invalid selection")
                except ValueError:
                    print("❌ Invalid input")
            else:
                print("📭 No categories found")
        
        elif choice == '7':
            filename = input("Enter export filename (default: contacts_export.json): ").strip() or "contacts_export.json"
            if contact_manager.export_contacts(filename):
                print(f"✅ Contacts exported to {filename}")
            else:
                print("❌ Export failed")
        
        elif choice == '8':
            filename = input("Enter import filename: ").strip()
            if filename and os.path.exists(filename):
                if contact_manager.import_contacts(filename):
                    print("✅ Contacts imported successfully!")
                else:
                    print("❌ Import failed")
            else:
                print("❌ File not found")
        
        elif choice == '9':
            break
        
        else:
            print("❌ Invalid choice")

def view_statistics(contact_manager):
    """Display comprehensive statistics"""
    contacts = contact_manager.list_contacts()
    total_contacts = len(contacts)
    
    if total_contacts == 0:
        print("\n📊 No contacts available for statistics")
        return
    
    total_emails = 0
    total_phones = 0
    
    for contact in contacts:
        details = contact_manager.get_contact_details(contact)
        if details:
            total_emails += len(details.get('emails', []))
            total_phones += len(details.get('phones', []))
    
    categories = contact_manager.get_contact_categories()
    
    print("\n📊 CONTACT STATISTICS")
    print("=" * 25)
    print(f"Total Contacts: {total_contacts}")
    print(f"Total Email Addresses: {total_emails}")
    print(f"Total Phone Numbers: {total_phones}")
    if total_contacts > 0:
        print(f"Average Emails per Contact: {total_emails/total_contacts:.1f}")
    else:
        print("Average Emails per Contact: 0")
    
    if categories:
        print(f"\n🏷️  CATEGORY BREAKDOWN:")
        for category in categories:
            contacts_in_category = contact_manager.list_contacts(category)
            if total_contacts > 0:
                percentage = (len(contacts_in_category) / total_contacts) * 100
                print(f"  {category}: {len(contacts_in_category)} contacts ({percentage:.1f}%)")
            else:
                print(f"  {category}: {len(contacts_in_category)} contacts (0%)")
    
    # Recent contacts
    print(f"\n📈 RECENT CONTACTS (last 5):")
    for contact in contacts[-5:]:
        details = contact_manager.get_contact_details(contact)
        if details:
            created = details.get('created_at', 'Unknown')
            print(f"  • {contact} - {created}")
        else:
            print(f"  • {contact} - [Unknown creation date]")

if __name__ == "__main__":
    main()