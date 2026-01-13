#!/usr/bin/env python3
import argparse
import sys
import os
from dotenv import load_dotenv

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.scheduler import NewsletterScheduler
from src.email_sender import EmailSender
from src.config import settings

def main():
    # Load environment variables
    load_dotenv()
    
    parser = argparse.ArgumentParser(description='AI-Powered Newsletter System')
    parser.add_argument('command', choices=['start', 'test', 'run-once', 'config'], 
                       help='Command to execute')
    
    args = parser.parse_args()
    
    if args.command == 'config':
        print("Current Configuration:")
        print(f"Topics: {', '.join(settings.topics)}")
        print(f"Email: {settings.to_email}")
        print(f"Schedule: {settings.newsletter_time} ({settings.timezone})")
        print(f"SMTP Server: {settings.smtp_server}:{settings.smtp_port}")
        return
    
    if args.command == 'test':
        print("Testing email connection...")
        email_sender = EmailSender()
        if email_sender.test_email_connection():
            print("✓ Email connection successful")
            
            # Test newsletter generation and sending
            print("Generating test newsletter...")
            scheduler = NewsletterScheduler()
            scheduler.run_once()
        else:
            print("✗ Email connection failed")
            print("Please check your email configuration in .env file")
        return
    
    if args.command == 'run-once':
        print("Generating and sending newsletter...")
        scheduler = NewsletterScheduler()
        scheduler.run_once()
        return
    
    if args.command == 'start':
        print("Starting newsletter scheduler...")
        print(f"Topics: {', '.join(settings.topics)}")
        print(f"Scheduled for: {settings.newsletter_time} ({settings.timezone})")
        
        scheduler = NewsletterScheduler()
        
        try:
            scheduler.start_scheduler()
            print("Scheduler started. Press Ctrl+C to stop.")
            
            # Keep the main thread alive
            import time
            while True:
                time.sleep(1)
                
        except KeyboardInterrupt:
            print("\nStopping scheduler...")
            scheduler.stop_scheduler()
            print("Scheduler stopped.")

if __name__ == "__main__":
    main()