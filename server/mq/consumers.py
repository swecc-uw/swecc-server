import json
import logging

import mq
from pika import BasicProperties
from resume_review.models import Resume

logger = logging.getLogger(__name__)


@mq.consumer(
    queue="reviewed-feedback",
    routing_key="reviewed-feedback",
    exchange="swecc-server-exchange",
)
async def reviewed_feedback_callback(
    body,
    properties: BasicProperties,
):
    expected_fields = ["user_id", "resume_id", "feedback", "error"]

    # Validate body
    try:
        data = json.loads(body)
        for field in expected_fields:
            if field not in data:
                raise ValueError(f"Field {field} not found in message")
    except json.JSONDecodeError as e:
        logger.error(f"Error decoding JSON: {e}")
        return
    except ValueError as e:
        logger.error(f"Error validating message: {e}")
        return

    if data["error"]:
        logger.info(f"Received error message: {data['error']}")
        return

    resume_object = Resume.objects.filter(id=data["resume_id"]).first()

    if not resume_object:
        logger.error(
            f"Resume with ID {data['resume_id']} not found"
        )  # Technically unreachable, though can't hurt to check for
        return

    resume_object.feedback = data["feedback"]
    resume_object.save()

    logger.info(
        f"Feedback for resume {data['resume_id']} updated with value {data['feedback']}"
    )


@mq.consumer(
    queue="server.verified-email",
    routing_key="server.verified-email",
    exchange="swecc-server-exchange",
)
async def verified_email_callback(
    body,
    properties: BasicProperties,
):
    logger.info(f"Received verified email message: {body}")
