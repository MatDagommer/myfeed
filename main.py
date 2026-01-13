#!/usr/bin/env python3
import argparse
import sys
import os

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from myfeed.scheduler import NewsletterScheduler
from myfeed.email_sender import EmailSender

def main():
    parser = argparse.ArgumentParser(description='AI-Powered Newsletter System')
    parser.add_argument('command', choices=['start', 'test', 'run-once', 'config'], 
                       help='Command to execute')
    parser.add_argument('--openai-api-key', required=True,
                       help='OpenAI API key')
    parser.add_argument('--smtp-server', default="smtp.gmail.com",
                       help='SMTP server (default: smtp.gmail.com)')
    parser.add_argument('--smtp-port', type=int, default=587,
                       help='SMTP port (default: 587)')
    parser.add_argument('--email-address', required=True,
                       help='Email address for sending')
    parser.add_argument('--email-password', required=True,
                       help='Email password')
    parser.add_argument('--to-email', required=True,
                       help='Recipient email address')
    parser.add_argument('--topics', default="",
                       help='Comma-separated list of topics')
    parser.add_argument('--newsletter-time', default="08:00",
                       help='Newsletter time (default: 08:00)')
    parser.add_argument('--timezone', default="UTC",
                       help='Timezone (default: UTC)')
    
    args = parser.parse_args()
    
    # Convert topics string to list
    topics_list = [topic.strip() for topic in args.topics.split(",") if topic.strip()]
    
    if args.command == 'config':
        print("Current Configuration:")
        print(f"Topics: {', '.join(topics_list)}")
        print(f"Email: {args.to_email}")
        print(f"Schedule: {args.newsletter_time} ({args.timezone})")
        print(f"SMTP Server: {args.smtp_server}:{args.smtp_port}")
        return
    
    if args.command == 'test':
        print("Testing email connection...")
        email_sender = EmailSender(
            smtp_server=args.smtp_server,
            smtp_port=args.smtp_port,
            email_address=args.email_address,
            email_password=args.email_password,
            to_email=args.to_email
        )
        if email_sender.test_email_connection():
            print("✓ Email connection successful")
            
            # Test newsletter generation and sending
            print("Generating test newsletter...")
            scheduler = NewsletterScheduler(
                openai_api_key=args.openai_api_key,
                email_sender=email_sender,
                topics=topics_list,
                newsletter_time=args.newsletter_time,
                timezone=args.timezone
            )
            scheduler.run_once()
        else:
            print("✗ Email connection failed")
            print("Please check your email configuration")
        return
    
    if args.command == 'run-once':
        print("Generating and sending newsletter...")
        email_sender = EmailSender(
            smtp_server=args.smtp_server,
            smtp_port=args.smtp_port,
            email_address=args.email_address,
            email_password=args.email_password,
            to_email=args.to_email
        )
        scheduler = NewsletterScheduler(
            openai_api_key=args.openai_api_key,
            email_sender=email_sender,
            topics=topics_list,
            newsletter_time=args.newsletter_time,
            timezone=args.timezone
        )
        scheduler.run_once()
        return
    
    if args.command == 'start':
        print("Starting newsletter scheduler...")
        print(f"Topics: {', '.join(topics_list)}")
        print(f"Scheduled for: {args.newsletter_time} ({args.timezone})")
        
        email_sender = EmailSender(
            smtp_server=args.smtp_server,
            smtp_port=args.smtp_port,
            email_address=args.email_address,
            email_password=args.email_password,
            to_email=args.to_email
        )
        scheduler = NewsletterScheduler(
            openai_api_key=args.openai_api_key,
            email_sender=email_sender,
            topics=topics_list,
            newsletter_time=args.newsletter_time,
            timezone=args.timezone
        )
        
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