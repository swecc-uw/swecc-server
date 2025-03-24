import os
import logging

logger = logging.getLogger(__name__)


def interview_paired_notification_html(
    name,
    partner_name,
    partner_email,
    partner_discord_id,
    partner_discord_username,
    interview_date,
):
    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>SWECC Interview Pairing Notification</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                line-height: 1.6;
                color: #282A2E;
                margin: 0;
                padding: 0;
                background-color: #f4f4f4;
            }}
            .container {{
                max-width: 600px;
                margin: 20px auto;
                background-color: #ffffff;
                padding: 20px;
                border-radius: 5px;
                box-shadow: 0 0 10px rgba(0,0,0,0.1);
            }}
            .header {{
                text-align: center;
                margin-bottom: 20px;
            }}
            .logo {{
                max-width: 200px;
                height: auto;
            }}
            h1 {{
                color: #6D7EE7;
                margin-top: 0;
            }}
            .content {{
                margin-bottom: 20px;
            }}
            .partner-info {{
                background-color: #f0f0f0;
                padding: 15px;
                border-radius: 5px;
                margin-bottom: 20px;
            }}
            .footer {{
                text-align: center;
                font-size: 0.9em;
                color: #666;
                margin-top: 20px;
                border-top: 1px solid #eee;
                padding-top: 10px;
            }}
            .button {{
                display: inline-block;
                padding: 10px 20px;
                background-color: #8852F6;
                color: white;
                text-decoration: none;
                border-radius: 5px;
                margin-top: 10px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <img src="https://bbaxszapshozxdvglcjg.supabase.co/storage/v1/object/public/assets/brand/swecc-logo.png" alt="SWECC Logo" class="logo">
                <h1>New Interview Pair!</h1>
            </div>
            <div class="content">
                <p>Hello {name},</p>
                <p>Great news! You've been paired for an upcoming mock interview, effective for the week of {interview_date}</p>

                <div class="partner-info">
                    <h2>Your Interview Partner</h2>
                    <p><strong>Name:</strong> {partner_name}</p>
                    <p><strong>Email:</strong> {partner_email}</p>
                    <p><strong>Discord Username:</strong> {partner_discord_username}</p>
                </div>

                <p>Please reach out to your partner to coordinate the details of your interview sessions. Remember to review the technical question you'll be interviewing them on and to come prepared!</p>

                <a href="https://interview.swecc.org" class="button">View Pairing</a>
                <a href="https://discordapp.com/users/{partner_discord_id}" class="button">Message Partner</a>
            </div>
            <div class="footer">
                <p>This is an automated message from SWECC</p>
                <p>&copy; 2024 Software Engineering Career Club. All rights reserved.</p>
            </div>
        </div>
    </body>
    </html>
    """


def interview_unpaired_notification_html(name, interview_date):
    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>SWECC Interview Pairing Notification</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                line-height: 1.6;
                color: #282A2E;
                margin: 0;
                padding: 0;
                background-color: #f4f4f4;
            }}
            .container {{
                max-width: 600px;
                margin: 20px auto;
                background-color: #ffffff;
                padding: 20px;
                border-radius: 5px;
                box-shadow: 0 0 10px rgba(0,0,0,0.1);
            }}
            .header {{
                text-align: center;
                margin-bottom: 20px;
            }}
            .logo {{
                max-width: 200px;
                height: auto;
            }}
            h1 {{
                color: #6D7EE7;
                margin-top: 0;
            }}
            .content {{
                margin-bottom: 20px;
            }}
            .footer {{
                text-align: center;
                font-size: 0.9em;
                color: #666;
                margin-top: 20px;
                border-top: 1px solid #eee;
                padding-top: 10px;
            }}
            .button {{
                display: inline-block;
                padding: 10px 20px;
                background-color: #8852F6;
                color: white;
                text-decoration: none;
                border-radius: 5px;
                margin-top: 10px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <img src="https://bbaxszapshozxdvglcjg.supabase.co/storage/v1/object/public/assets/brand/swecc-logo.png" alt="SWECC Logo" class="logo">
                <h1>Interview Pairing</h1>
            </div>
            <div class="content">
                <p>Hello {name},</p>
                <p>We're sorry to inform you that we weren't able to find you a mock interview partner for the week of {interview_date}.</p>
                <p>Please feel free to sign up again next week.</p>
            </div>
            <div class="footer">
                <p>This is an automated message from SWECC</p>
                <p>&copy; 2024 Software Engineering Career Club. All rights reserved.</p>
            </div>
        </div>
    </body>
    </html>
    """
