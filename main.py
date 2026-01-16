#!/usr/bin/env python3
import argparse
import sys
import os

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from myfeed.generator import NewsletterGenerator
from myfeed.email_sender import EmailSender

def main():
    parser = argparse.ArgumentParser(description='AI-Powered Newsletter System')
    parser.add_argument('command', choices=['test', 'run-once', 'config'], 
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
    
    args = parser.parse_args()
    
    # Convert topics string to list
    topics_list = [topic.strip() for topic in args.topics.split(",") if topic.strip()]
    
    if args.command == 'config':
        print("Current Configuration:")
        print(f"Topics: {', '.join(topics_list)}")
        print(f"Email: {args.to_email}")
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
            generator = NewsletterGenerator(
                openai_api_key=args.openai_api_key,
                email_sender=email_sender,
                topics=topics_list
            )
            generator.run()
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
        generator = NewsletterGenerator(
            openai_api_key=args.openai_api_key,
            email_sender=email_sender,
            topics=topics_list
        )
        generator.run()
        return

if __name__ == "__main__":
    main()