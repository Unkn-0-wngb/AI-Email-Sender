import json
import os
import re
from typing import Dict, List, Optional
from datetime import datetime

class ContactManager:
    def __init__(self, contacts_file='contacts.json'):
        self.contacts_file = contacts_file
        self.contacts = self.load_contacts()
    
    def load_contacts(self) -> Dict:
        """Load contacts from JSON file"""
        if os.path.exists(self.contacts_file):
            try:
                with open(self.contacts_file, 'r', encoding='utf-8') as file:
                    return json.load(file)
            except (json.JSONDecodeError, Exception) as e:
                print(f"⚠️  Error loading contacts: {e}")
                return {}
        return {}
    
    def save_contacts(self):
        """Save contacts to JSON file"""
        try:
            with open(self.contacts_file, 'w', encoding='utf-8') as file:
                json.dump(self.contacts, file, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"❌ Error saving contacts: {e}")
            return False
    
    def find_contact(self, name: str) -> Optional[Dict]:
        """Find contact by name (case-insensitive)"""
        name_lower = name.lower()
        for contact_name, contact_data in self.contacts.items():
            if contact_name.lower() == name_lower:
                return contact_data
        return None
    
    def get_contact_details(self, name: str) -> Optional[Dict]:
        """Get complete contact details - FIXED METHOD"""
        return self.find_contact(name)
    
    def find_contacts_by_email(self, email: str) -> List[str]:
        """Find all contacts with matching email"""
        matching_contacts = []
        email_lower = email.lower()
        
        for contact_name, contact_data in self.contacts.items():
            emails = contact_data.get('emails', [])
            if any(e.lower() == email_lower for e in emails):
                matching_contacts.append(contact_name)
        
        return matching_contacts
    
    def create_contact(self) -> bool:
        """Create a new contact with comprehensive information"""
        print("\n👥 CREATE NEW CONTACT")
        print("-" * 20)
        
        name = input("Full Name: ").strip()
        if not name:
            print("❌ Name is required")
            return False
        
        # Check if contact already exists
        existing_contact = self.find_contact(name)
        if existing_contact:
            print(f"⚠️  Contact '{name}' already exists!")
            view = input("View existing contact? (y/n): ").lower().strip()
            if view == 'y':
                self.display_contact_details(name, existing_contact)
            return False
        
        # Collect contact information
        contact_data = {
            'emails': [],
            'phones': [],
            'created_at': self._get_current_timestamp(),
            'last_contact': self._get_current_timestamp()
        }
        
        # Email collection
        print("\n📧 EMAIL ADDRESSES")
        while True:
            email = input("Email address (or 'done' to finish): ").strip()
            if email.lower() == 'done':
                if not contact_data['emails']:
                    print("❌ At least one email is required")
                    continue
                break
            
            if self.validate_email(email):
                if email not in contact_data['emails']:
                    contact_data['emails'].append(email)
                    print(f"✅ Added email: {email}")
                else:
                    print("⚠️  Email already added")
            else:
                print("❌ Invalid email format")
        
        # Phone numbers
        print("\n📞 PHONE NUMBERS")
        while True:
            phone = input("Phone number (or 'done' to finish): ").strip()
            if phone.lower() == 'done':
                break
            if phone and phone not in contact_data['phones']:
                contact_data['phones'].append(phone)
                print(f"✅ Added phone: {phone}")
        
        # Additional information
        print("\n📝 ADDITIONAL INFORMATION")
        company = input("Company: ").strip()
        position = input("Position: ").strip()
        address = input("Address: ").strip()
        notes = input("Notes: ").strip()
        category = input("Category (e.g., Work, Personal, Family): ").strip()
        
        if company:
            contact_data['company'] = company
        if position:
            contact_data['position'] = position
        if address:
            contact_data['address'] = address
        if notes:
            contact_data['notes'] = notes
        if category:
            contact_data['category'] = category
        
        # Save contact
        self.contacts[name] = contact_data
        if self.save_contacts():
            print(f"✅ Contact '{name}' created successfully!")
            self.display_contact_details(name, contact_data)
            return True
        else:
            print("❌ Failed to save contact")
            return False

    def create_contact_with_name(self, name: str) -> bool:
        """Create a contact with a predefined name"""
        print(f"\n👥 CREATING CONTACT: {name}")
        
        # Check if contact already exists
        existing_contact = self.find_contact(name)
        if existing_contact:
            print(f"⚠️  Contact '{name}' already exists!")
            return False
        
        contact_data = {
            'emails': [],
            'phones': [],
            'created_at': self._get_current_timestamp(),
            'last_contact': self._get_current_timestamp()
        }
        
        # Email collection
        print("\n📧 EMAIL ADDRESSES")
        while True:
            email = input("Email address (or 'done' to finish): ").strip()
            if email.lower() == 'done':
                if not contact_data['emails']:
                    print("❌ At least one email is required")
                    continue
                break
            
            if self.validate_email(email):
                if email not in contact_data['emails']:
                    contact_data['emails'].append(email)
                    print(f"✅ Added email: {email}")
                else:
                    print("⚠️  Email already added")
            else:
                print("❌ Invalid email format")
        
        # Additional information
        print("\n📝 ADDITIONAL INFORMATION (optional)")
        phone = input("Phone: ").strip()
        company = input("Company: ").strip()
        position = input("Position: ").strip()
        address = input("Address: ").strip()
        notes = input("Notes: ").strip()
        category = input("Category: ").strip()
        
        if phone:
            contact_data['phones'] = [phone]
        if company:
            contact_data['company'] = company
        if position:
            contact_data['position'] = position
        if address:
            contact_data['address'] = address
        if notes:
            contact_data['notes'] = notes
        if category:
            contact_data['category'] = category
        
        # Save contact
        self.contacts[name] = contact_data
        if self.save_contacts():
            print(f"✅ Contact '{name}' created successfully!")
            return True
        else:
            print("❌ Failed to save contact")
            return False
    
    def add_email_to_contact(self, name: str) -> bool:
        """Add additional email to existing contact"""
        contact = self.find_contact(name)
        if not contact:
            print(f"❌ Contact '{name}' not found")
            return False
        
        print(f"\n📧 ADD EMAIL TO '{name}'")
        print(f"Current emails: {', '.join(contact.get('emails', []))}")
        
        while True:
            new_email = input("New email address: ").strip()
            if not new_email:
                break
            
            if self.validate_email(new_email):
                if new_email in contact.get('emails', []):
                    print("⚠️  Email already exists for this contact")
                else:
                    contact['emails'].append(new_email)
                    contact['updated_at'] = self._get_current_timestamp()
                    self.contacts[name] = contact
                    if self.save_contacts():
                        print(f"✅ Email '{new_email}' added to '{name}'")
                        return True
                    else:
                        print("❌ Failed to save contact")
                        return False
            else:
                print("❌ Invalid email format")
        
        return False
    
    def edit_contact(self, name: str) -> bool:
        """Comprehensively edit a contact"""
        contact = self.find_contact(name)
        if not contact:
            print(f"❌ Contact '{name}' not found")
            return False
        
        print(f"\n✏️  EDITING CONTACT: {name}")
        self.display_contact_details(name, contact)
        
        while True:
            print("\n📝 EDIT OPTIONS:")
            print("1. ✏️  Change name")
            print("2. 📧 Manage emails")
            print("3. 📞 Manage phones")
            print("4. 🏢 Edit company/position")
            print("5. 📍 Edit address")
            print("6. 📋 Edit notes")
            print("7. 🏷️  Edit category")
            print("8. ✅ Finish editing")
            
            choice = input("\nSelect option (1-8): ").strip()
            
            if choice == '1':
                new_name = input("New name: ").strip()
                if new_name and new_name != name:
                    if not self.find_contact(new_name):
                        self.contacts[new_name] = self.contacts.pop(name)
                        name = new_name
                        print(f"✅ Name changed to '{new_name}'")
                    else:
                        print("❌ Contact with that name already exists")
            
            elif choice == '2':
                self.manage_contact_emails(name, contact)
            
            elif choice == '3':
                self.manage_contact_phones(name, contact)
            
            elif choice == '4':
                company = input(f"Company (current: {contact.get('company', '')}): ").strip()
                position = input(f"Position (current: {contact.get('position', '')}): ").strip()
                if company:
                    contact['company'] = company
                if position:
                    contact['position'] = position
            
            elif choice == '5':
                address = input(f"Address (current: {contact.get('address', '')}): ").strip()
                if address:
                    contact['address'] = address
            
            elif choice == '6':
                notes = input(f"Notes (current: {contact.get('notes', '')}): ").strip()
                if notes:
                    contact['notes'] = notes
            
            elif choice == '7':
                category = input(f"Category (current: {contact.get('category', '')}): ").strip()
                if category:
                    contact['category'] = category
            
            elif choice == '8':
                contact['updated_at'] = self._get_current_timestamp()
                self.contacts[name] = contact
                if self.save_contacts():
                    print("✅ Contact updated successfully!")
                    return True
                else:
                    print("❌ Failed to save contact")
                    return False
            
            else:
                print("❌ Invalid option")
    
    def manage_contact_emails(self, name: str, contact: Dict):
        """Manage email addresses for a contact"""
        while True:
            print(f"\n📧 MANAGING EMAILS FOR '{name}'")
            emails = contact.get('emails', [])
            for i, email in enumerate(emails, 1):
                print(f"{i}. {email}")
            
            print("\nOptions: [a]dd, [r]emove, [d]one")
            action = input("Choose action: ").lower().strip()
            
            if action == 'a':
                new_email = input("New email: ").strip()
                if self.validate_email(new_email):
                    if new_email not in emails:
                        emails.append(new_email)
                        contact['emails'] = emails
                        print(f"✅ Email added: {new_email}")
                    else:
                        print("⚠️  Email already exists")
                else:
                    print("❌ Invalid email format")
            
            elif action == 'r' and emails:
                try:
                    index = int(input("Email number to remove: ").strip()) - 1
                    if 0 <= index < len(emails):
                        removed = emails.pop(index)
                        contact['emails'] = emails
                        print(f"✅ Email removed: {removed}")
                    else:
                        print("❌ Invalid number")
                except ValueError:
                    print("❌ Invalid input")
            
            elif action == 'd':
                break
            
            else:
                print("❌ Invalid action")
    
    def manage_contact_phones(self, name: str, contact: Dict):
        """Manage phone numbers for a contact"""
        while True:
            print(f"\n📞 MANAGING PHONES FOR '{name}'")
            phones = contact.get('phones', [])
            for i, phone in enumerate(phones, 1):
                print(f"{i}. {phone}")
            
            print("\nOptions: [a]dd, [r]emove, [d]one")
            action = input("Choose action: ").lower().strip()
            
            if action == 'a':
                new_phone = input("New phone: ").strip()
                if new_phone and new_phone not in phones:
                    phones.append(new_phone)
                    contact['phones'] = phones
                    print(f"✅ Phone added: {new_phone}")
                else:
                    print("⚠️  Phone already exists or is empty")
            
            elif action == 'r' and phones:
                try:
                    index = int(input("Phone number to remove: ").strip()) - 1
                    if 0 <= index < len(phones):
                        removed = phones.pop(index)
                        contact['phones'] = phones
                        print(f"✅ Phone removed: {removed}")
                    else:
                        print("❌ Invalid number")
                except ValueError:
                    print("❌ Invalid input")
            
            elif action == 'd':
                break
            
            else:
                print("❌ Invalid action")
    
    def display_contact_details(self, name: str, contact: Dict):
        """Display comprehensive contact details"""
        print(f"\n👤 CONTACT DETAILS: {name}")
        print("-" * 40)
        print(f"📧 Emails: {', '.join(contact.get('emails', []))}")
        print(f"📞 Phones: {', '.join(contact.get('phones', []))}")
        if contact.get('company'):
            print(f"🏢 Company: {contact.get('company')}")
        if contact.get('position'):
            print(f"💼 Position: {contact.get('position')}")
        if contact.get('address'):
            print(f"📍 Address: {contact.get('address')}")
        if contact.get('category'):
            print(f"🏷️  Category: {contact.get('category')}")
        if contact.get('notes'):
            print(f"📋 Notes: {contact.get('notes')}")
        print(f"📅 Created: {contact.get('created_at', 'Unknown')}")
        if contact.get('updated_at'):
            print(f"✏️  Updated: {contact.get('updated_at')}")
        print("-" * 40)
    
    def get_contact_emails(self, name: str) -> List[str]:
        """Get all emails for a contact"""
        contact = self.find_contact(name)
        if contact:
            return contact.get('emails', [])
        return []
    
    def delete_contact(self, name: str) -> bool:
        """Delete a contact"""
        contact = self.find_contact(name)
        if contact:
            confirm = input(f"Are you sure you want to delete '{name}'? (y/n): ").lower().strip()
            if confirm == 'y':
                del self.contacts[name]
                return self.save_contacts()
        return False
    
    def list_contacts(self, category: str = None) -> List[str]:
        """Get list of all contact names, optionally filtered by category"""
        if category:
            return [name for name, data in self.contacts.items() 
                   if data.get('category', '').lower() == category.lower()]
        return list(self.contacts.keys())
    
    def get_contact_categories(self) -> List[str]:
        """Get all unique contact categories"""
        categories = set()
        for contact_data in self.contacts.values():
            if 'category' in contact_data and contact_data['category']:
                categories.add(contact_data['category'])
        return sorted(list(categories))
    
    def search_contacts(self, query: str) -> List[str]:
        """Search contacts by name, email, company, or notes"""
        query = query.lower()
        results = []
        
        for name, data in self.contacts.items():
            # Search in name
            if query in name.lower():
                results.append(name)
                continue
            
            # Search in emails
            if any(query in email.lower() for email in data.get('emails', [])):
                results.append(name)
                continue
            
            # Search in company
            if query in data.get('company', '').lower():
                results.append(name)
                continue
            
            # Search in notes
            if query in data.get('notes', '').lower():
                results.append(name)
                continue
        
        return results
    
    def validate_email(self, email: str) -> bool:
        """Validate email format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    def _get_current_timestamp(self):
        """Get current timestamp"""
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    def export_contacts(self, filename: str) -> bool:
        """Export contacts to JSON file"""
        try:
            with open(filename, 'w', encoding='utf-8') as file:
                json.dump(self.contacts, file, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"❌ Error exporting contacts: {e}")
            return False
    
    def import_contacts(self, filename: str) -> bool:
        """Import contacts from JSON file"""
        try:
            with open(filename, 'r', encoding='utf-8') as file:
                imported_contacts = json.load(file)
            
            # Merge with existing contacts
            for name, data in imported_contacts.items():
                if name in self.contacts:
                    # Merge data
                    existing = self.contacts[name]
                    # Merge emails
                    existing_emails = set(existing.get('emails', []))
                    new_emails = set(data.get('emails', []))
                    existing['emails'] = list(existing_emails.union(new_emails))
                    # Merge other fields, preferring existing data
                    for key, value in data.items():
                        if key not in existing or not existing[key]:
                            existing[key] = value
                else:
                    self.contacts[name] = data
            
            return self.save_contacts()
        except Exception as e:
            print(f"❌ Error importing contacts: {e}")
            return False