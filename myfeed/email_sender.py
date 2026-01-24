import smtplib
import traceback
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
                subject = f"Your Daily Newsletter 😎💨🥴🤖🌍🇫🇷🇺🇸 - {datetime.now().strftime('%B %d, %Y')}"
            
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
            traceback.print_exc()
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
            color: #2980b9;
            font-weight: bold;
            font-size: 28px;
            margin-top: 35px;
            margin-bottom: 30px;
            padding-bottom: 10px;
            border-bottom: 2px solid #3498db;
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
        .paper {
            border-left: 4px solid #e74c3c;
            padding-left: 15px;
            margin: 20px 0;
            background-color: #fdf2f2;
            padding: 15px;
            border-radius: 5px;
        }
        .paper-meta {
            font-size: 14px;
            color: #7f8c8d;
            margin: 5px 0;
        }
        .footer {
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #bdc3c7;
            text-align: center;
            font-size: 14px;
            color: #7f8c8d;
        }
        hr {
            border: none;
            border-top: 2px solid #bdc3c7;
            margin: 30px 0;
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
        
        # Enhanced markdown-like formatting
        import re
        formatted_content = content

        # Convert horizontal rules (--- -> <hr>)
        formatted_content = re.sub(r'^---+\s*$', r'<hr>', formatted_content, flags=re.MULTILINE)

        # Convert headers (### Title -> <h3>Title</h3>)
        formatted_content = re.sub(r'^### (.*?)$', r'<h3>\1</h3>', formatted_content, flags=re.MULTILINE)
        formatted_content = re.sub(r'^## (.*?)$', r'<h2>\1</h2>', formatted_content, flags=re.MULTILINE)
        formatted_content = re.sub(r'^# (.*?)$', r'<h1>\1</h1>', formatted_content, flags=re.MULTILINE)

        # Convert bold text (**text** -> <strong>text</strong>)
        formatted_content = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', formatted_content)

        # Convert Markdown links ([text](url) -> <a href="url">text</a>)
        formatted_content = re.sub(r'\[([^\]]+)\]\(([^\)]+)\)', r'<a href="\2">\1</a>', formatted_content)

        # Handle paper sections - wrap papers in appropriate divs
        formatted_content = re.sub(r'(## Recent Papers.*?)(?=## |\Z)', self._format_papers_section, formatted_content, flags=re.DOTALL)
        
        # Handle news sections - wrap articles in appropriate divs
        formatted_content = re.sub(r'(## Latest News.*?)(?=## Recent Papers|## |\Z)', self._format_news_section, formatted_content, flags=re.DOTALL)
        
        # Convert paragraphs (double newlines)
        formatted_content = formatted_content.replace('\n\n', '</p><p>')
        formatted_content = '<p>' + formatted_content + '</p>'
        
        # Convert single newlines to line breaks
        formatted_content = formatted_content.replace('\n', '<br>')
        
        # Clean up empty paragraphs
        formatted_content = formatted_content.replace('<p></p>', '')
        formatted_content = formatted_content.replace('<p><br>', '<p>')
        
        return html_template.render(
            content=formatted_content,
            date=datetime.now().strftime('%B %d, %Y at %I:%M %p')
        )

    def _format_papers_section(self, match):
        content = match.group(1)
        # Wrap individual papers in paper divs
        import re
        content = re.sub(r'(\d+\.\s+<strong>.*?</strong>.*?)(?=\d+\.\s+<strong>|\Z)', r'<div class="paper">\1</div>', content, flags=re.DOTALL)
        return content

    def _format_news_section(self, match):
        content = match.group(1)
        # Wrap individual articles in article divs
        import re
        content = re.sub(r'(\d+\.\s+<strong>.*?</strong>.*?)(?=\d+\.\s+<strong>|\Z)', r'<div class="article">\1</div>', content, flags=re.DOTALL)
        return content

    def test_email_connection(self) -> bool:
        try:
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.email_address, self.email_password)
                print("Email connection test successful")
                return True
        except Exception as e:
            print(f"Email connection test failed: {e}")
            traceback.print_exc()
            return False