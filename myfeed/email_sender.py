import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from jinja2 import Template
from datetime import datetime

class EmailSender:
    def __init__(self, smtp_server: str, smtp_port: int, email_address: str, email_password: str, to_email: str):
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.email_address = email_address
        self.email_password = email_password
        self.to_email = to_email

    def send_newsletter(self, content: str, subject: str = None) -> bool:
        try:
            if not subject:
                subject = f"Your Daily Newsletter - {datetime.now().strftime('%B %d, %Y')}"
            
            # Create HTML version of the newsletter
            html_content = self._convert_to_html(content)
            
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.email_address
            msg['To'] = self.to_email

            # Add both plain text and HTML parts
            text_part = MIMEText(content, 'plain', 'utf-8')
            html_part = MIMEText(html_content, 'html', 'utf-8')
            
            msg.attach(text_part)
            msg.attach(html_part)

            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.email_address, self.email_password)
                server.send_message(msg)
                
            print(f"Newsletter sent successfully to {self.to_email}")
            return True
            
        except Exception as e:
            print(f"Failed to send newsletter: {e}")
            return False

    def _convert_to_html(self, content: str) -> str:
        html_template = Template("""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Your Daily Newsletter</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f4f4f4;
        }
        .container {
            background-color: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 0 10px rgba(0,0,0,0.1);
        }
        h1 {
            color: #2c3e50;
            border-bottom: 2px solid #3498db;
            padding-bottom: 10px;
        }
        h2 {
            color: #34495e;
            margin-top: 30px;
        }
        h3 {
            color: #2980b9;
        }
        a {
            color: #3498db;
            text-decoration: none;
        }
        a:hover {
            text-decoration: underline;
        }
        .article {
            border-left: 4px solid #3498db;
            padding-left: 15px;
            margin: 20px 0;
            background-color: #f8f9fa;
            padding: 15px;
            border-radius: 5px;
        }
        .footer {
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #bdc3c7;
            text-align: center;
            font-size: 14px;
            color: #7f8c8d;
        }
    </style>
</head>
<body>
    <div class="container">
        {{ content | replace('\n', '<br>') | replace('**', '<strong>') | replace('**', '</strong>') }}
        <div class="footer">
            <p>This newsletter was generated automatically by your AI agent.</p>
            <p>Generated on {{ date }}</p>
        </div>
    </div>
</body>
</html>
        """)
        
        # Simple markdown-like formatting
        formatted_content = content
        formatted_content = formatted_content.replace('\n\n', '</p><p>')
        formatted_content = formatted_content.replace('\n', '<br>')
        formatted_content = formatted_content.replace('**', '<strong>', 1)
        formatted_content = formatted_content.replace('**', '</strong>', 1)
        
        return html_template.render(
            content=formatted_content,
            date=datetime.now().strftime('%B %d, %Y at %I:%M %p')
        )

    def test_email_connection(self) -> bool:
        try:
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.email_address, self.email_password)
                print("Email connection test successful")
                return True
        except Exception as e:
            print(f"Email connection test failed: {e}")
            return False