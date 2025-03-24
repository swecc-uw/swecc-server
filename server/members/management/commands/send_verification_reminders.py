from members.models import User
from django.core.management.base import BaseCommand
import time
from email_util.send_email import send_email

SENDER_EMAIL = "swecc@uw.edu"
COOL_DOWN = 1

email_template = (
    lambda user: f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Verify Your SWECC Account</title>
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
        .verification-info {{
            background-color: #f0f0f0;
            padding: 15px;
            border-radius: 5px;
            margin-bottom: 20px;
        }}
        .command {{
            background-color: #eaecf6;
            padding: 12px;
            border-radius: 4px;
            font-family: monospace;
            font-weight: bold;
            color: #5548c2;
            display: inline-block;
            margin: 10px 0;
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
        .important {{
            font-weight: bold;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <img src="https://bbaxszapshozxdvglcjg.supabase.co/storage/v1/object/public/assets/brand/swecc-logo.png" alt="SWECC Logo" class="logo">
            <h1>Verify Your SWECC Account</h1>
        </div>
        <div class="content">
            <p>Hello {user.first_name},</p>
            <p>We noticed that you haven't verified your SWECC account yet. To get the most out of your membership in SWECC, it's important that you finish the verification process. Most noteably, referral program eligibility hinges on us being able to connect your Discord account to your profile.</p>
            <p>Follow the instructions below to verify your account:</p>

            <div class="verification-info">
                <h2>Verification Instructions</h2>
                <p>In the Discord server, use this command to verify your account:</p>
                <div class="command">/verify {user.username}</div>

                <p> If you've forgotten your password, you can reset it using another command:</p>
                <div class="command">/reset_password</div>

                <p class="important">For verification and password reset to work, your Discord username <strong>must</strong> match the username you entered: <strong>{user.discord_username}</strong></p>

                <p>If your Discord username doesn't match, please contact us at <a href="mailto:swecc@uw.edu">swecc@uw.edu</a> to update your information.</p>
            </div>
        </div>
        <div class="footer">
            <p>This is an automated message from SWECC</p>
        </div>
    </div>
</body>
</html>
"""
)


class Command(BaseCommand):
    help = "Command to send a reminder email to all unverified users"

    def add_arguments(self, parser):
        parser.add_argument(
            "--all", action="store_true", help="Send reminder to all users"
        )
        parser.add_argument(
            "--username", type=str, help="SWECC Interview Website Username"
        )
        parser.add_argument(
            "--dry-run", action="store_true", help="Dry run, do not send emails"
        )
        parser.add_argument(
            "--preview", action="store_true", help="Preview email content"
        )

    def is_verified(self, user):
        return user.groups.filter(name="is_verified").exists()

    def get_target_users(self, options):
        if options["username"]:
            users = User.objects.filter(username=options["username"])
            if not users.exists():
                return None, f"User with username {options['username']} not found"
            return list(users), None

        if options["all"]:
            users = [user for user in User.objects.all() if not self.is_verified(user)]
            if not users:
                return None, "No unverified users found"
            return users, None

        return None, "Either --all or --username must be specified"

    def send_reminder_email(self, user):
        html_content = email_template(user)
        subject = "SWECC Account Verification Required"

        if not user.email:
            return False, f"⚠ User {user.username} has no email address"

        try:
            send_email(
                from_email=SENDER_EMAIL,
                to_email=user.email,
                subject=subject,
                html_content=html_content,
            )
            return True, f"✓ Sent reminder to {user.email}"
        except Exception as e:
            return False, f"✗ Failed to send reminder to {user.email}: {str(e)}"

    def preview_email(self, user):
        html_content = email_template(user)
        self.stdout.write(
            self.style.SUCCESS(f"\nPreview of email for {user.username}:\n")
        )
        self.stdout.write(html_content)
        self.stdout.write("\n")

    def handle(self, *args, **options):
        pp = (
            lambda user: f"Username: {user.username}, Email: {user.email}, Discord ID: {user.discord_id}"
        )

        users, error = self.get_target_users(options)
        if error is not None:
            self.stdout.write(self.style.ERROR(error))
            return

        self.stdout.write(
            self.style.SUCCESS(
                f"Found {len(users)} {'user' if len(users) == 1 else 'users'} to send reminders to"
            )
        )

        for user in users:
            self.stdout.write(
                self.style.SUCCESS(pp(user) + f", Verified: {self.is_verified(user)}")
            )

        if options["preview"]:
            self.preview_email(users[0])
            return

        if options["dry_run"]:
            self.stdout.write(
                self.style.SUCCESS("Dry run completed. No emails were sent.")
            )
            return

        sent_count, error_count = 0, 0
        for user in users:
            success, message = self.send_reminder_email(user)
            self.stdout.write(
                self.style.SUCCESS(message) if success else self.style.ERROR(message)
            )

            if success:
                sent_count += 1
            else:
                error_count += 1

            time.sleep(COOL_DOWN)

        self.stdout.write(
            self.style.SUCCESS(
                f"Completed sending reminders: {sent_count} sent, {error_count} failed"
            )
        )
