import csv
import json
from email_sender import EmailSender

class BatchEmailSender:
    def __init__(self, config_file='email_config.cfg'):
        self.email_sender = EmailSender(config_file)
    
    def send_batch_emails(self, csv_file_path):
        """Send emails to multiple recipients from a CSV file"""
        
        try:
            with open(csv_file_path, 'r', encoding='utf-8') as file:
                csv_reader = csv.DictReader(file)
                recipients = list(csv_reader)
            
            print(f"📋 Found {len(recipients)} recipients in CSV file")
            
            for i, recipient in enumerate(recipients, 1):
                print(f"\n--- Processing {i}/{len(recipients)} ---")
                
                name = recipient.get('name', '').strip()
                email = recipient.get('email', '').strip()
                message = recipient.get('message', '').strip()
                tone = recipient.get('tone', 'Formal').strip()
                
                if not all([name, email, message]):
                    print(f"❌ Skipping incomplete record: {name}")
                    continue
                
                # Generate email content
                generated_content = self.email_sender.generate_email_content(name, message, tone)
                subject, body = self.email_sender.parse_generated_content(generated_content)
                
                # Preview and send
                self.email_sender.preview_email(name, subject, body, tone)
                confirm = input(f"Send to {name}? (y/n/skip all): ").lower()
                
                if confirm == 'y':
                    self.email_sender.send_email([email], subject, body)
                elif confirm == 'skip all':
                    print("Skipping remaining emails.")
                    break
                else:
                    print(f"Skipped {name}")
            
            print("\n✅ Batch processing completed!")
            
        except Exception as e:
            print(f"❌ Error processing batch: {str(e)}")

def create_sample_csv():
    """Create a sample CSV file for batch sending"""
    sample_data = [
        ['name', 'email', 'message', 'tone'],
        ['John Smith', 'john@example.com', 'Reminder about tomorrow meeting at 2 PM', 'Formal'],
        ['Sarah Johnson', 'sarah@example.com', "Let's catch up for coffee next week", 'Casual + Friendly'],
        ['Mike Wilson', 'mike@example.com', 'Project deadline extension approved', 'Formal + Casual']
    ]
    
    with open('sample_recipients.csv', 'w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerows(sample_data)
    
    print("✅ Sample CSV created: 'sample_recipients.csv'")

if __name__ == "__main__":
    batch_sender = BatchEmailSender()
    
    print("📧 Batch Email Sender")
    print("1. Send batch emails from CSV")
    print("2. Create sample CSV template")
    
    choice = input("Choose option (1 or 2): ").strip()
    
    if choice == '1':
        csv_file = input("Enter CSV file path: ").strip()
        batch_sender.send_batch_emails(csv_file)
    elif choice == '2':
        create_sample_csv()
    else:
        print("Invalid choice")