BASE_URL = "https://engagement.swecc.org"


def verify_school_email_html(token):
    return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Email Verification</title>
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
            text-align: center;
        }}
        .header {{
            margin-bottom: 20px;
        }}
        h1 {{
            color: #6D7EE7;
            margin-top: 0;
        }}
        .content {{
            margin-bottom: 20px;
        }}
        .button {{
            display: inline-block;
            padding: 10px 20px;
            background-color: #8852F6;
            color: white !important;
            text-decoration: none;
            border-radius: 5px;
            font-size: 16px;
            margin-top: 10px;
        }}
        .footer {{
            font-size: 0.9em;
            color: #666;
            margin-top: 20px;
            border-top: 1px solid #eee;
            padding-top: 10px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Verify Your Email</h1>
        </div>
        <div class="content">
            <p>Click the button below to verify your school email:</p>
            <a href="{BASE_URL}/verify-school-email/{token.decode()}" class="button">Verify Email</a>
        </div>
        <div class="footer">
            <p>This is an automated message from SWECC</p>
            <p>&copy; 2025 Software Engineering Career Club. All rights reserved.</p>
        </div>
    </div>
</body>
</html>

"""
