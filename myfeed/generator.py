import traceback
from datetime import datetime
from typing import List
from .agent import NewsAgent
from .email_sender import EmailSender

class NewsletterGenerator:
    def __init__(self, openai_api_key: str, email_sender: EmailSender, topics: List[str]):
        self.agent = NewsAgent(openai_api_key)
        self.email_sender = email_sender
        self.topics = topics

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
            traceback.print_exc()

    def run(self):
        """Generate and send newsletter once."""
        print("Running newsletter generation...")
        self.generate_and_send_newsletter()