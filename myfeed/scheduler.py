import schedule
import time
import threading
from datetime import datetime
import pytz
from typing import List
from .agent import NewsAgent
from .email_sender import EmailSender

class NewsletterScheduler:
    def __init__(self, openai_api_key: str, email_sender: EmailSender, topics: List[str], newsletter_time: str, timezone: str):
        self.agent = NewsAgent(openai_api_key)
        self.email_sender = email_sender
        self.topics = topics
        self.newsletter_time = newsletter_time
        self.timezone = timezone
        self.running = False
        self.thread = None

    def generate_and_send_newsletter(self):
        try:
            print(f"Starting newsletter generation at {datetime.now()}")
            
            # Generate newsletter content
            content = self.agent.generate_newsletter(self.topics)
            
            if content:
                # Send newsletter
                success = self.email_sender.send_newsletter(content)
                if success:
                    print("Newsletter generated and sent successfully!")
                else:
                    print("Failed to send newsletter")
            else:
                print("Failed to generate newsletter content")
                
        except Exception as e:
            print(f"Error in newsletter generation/sending: {e}")

    def schedule_daily_newsletter(self):
        # Clear any existing scheduled jobs
        schedule.clear()
        
        # Convert time to user's timezone
        try:
            user_tz = pytz.timezone(self.timezone)
            schedule.every().day.at(self.newsletter_time).do(self.generate_and_send_newsletter)
            print(f"Newsletter scheduled daily at {self.newsletter_time} ({self.timezone})")
        except Exception as e:
            print(f"Error setting up schedule: {e}")
            # Fallback to UTC
            schedule.every().day.at(self.newsletter_time).do(self.generate_and_send_newsletter)
            print(f"Newsletter scheduled daily at {self.newsletter_time} (UTC)")

    def start_scheduler(self):
        if self.running:
            print("Scheduler is already running")
            return
            
        self.schedule_daily_newsletter()
        self.running = True
        
        def run_scheduler():
            print("Newsletter scheduler started")
            while self.running:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
        
        self.thread = threading.Thread(target=run_scheduler, daemon=True)
        self.thread.start()
        
        print(f"Next newsletter scheduled for: {schedule.next_run()}")

    def stop_scheduler(self):
        if not self.running:
            print("Scheduler is not running")
            return
            
        self.running = False
        schedule.clear()
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=1)
        print("Newsletter scheduler stopped")

    def run_once(self):
        print("Running newsletter generation once...")
        self.generate_and_send_newsletter()

    def get_next_run_time(self):
        if schedule.jobs:
            return schedule.next_run()
        return None