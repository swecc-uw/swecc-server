import logging
import os

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

from server.settings import DJANGO_DEBUG, SENDGRID_API_KEY

logger = logging.getLogger(__name__)


def send_email(from_email, to_email, subject, html_content, force_send=False):
    """
    plz catch exceptions in the caller
    """
    if DJANGO_DEBUG and not force_send:
        logger.info(f"Email sent to {to_email} with subject: {subject}")
        return

    sg = SendGridAPIClient(SENDGRID_API_KEY)

    return sg.send(
        Mail(
            from_email=from_email,
            to_emails=to_email,
            subject=subject,
            html_content=html_content,
        )
    )
