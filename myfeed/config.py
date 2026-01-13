import os
from typing import List
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    openai_api_key: str
    smtp_server: str = "smtp.gmail.com"
    smtp_port: int = 587
    email_address: str
    email_password: str
    to_email: str
    topics: List[str] = []
    newsletter_time: str = "08:00"
    timezone: str = "UTC"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if isinstance(self.topics, str):
            self.topics = [topic.strip() for topic in self.topics.split(",")]

settings = Settings()