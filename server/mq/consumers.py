import json
import logging

import mq
from asgiref.sync import sync_to_async
from pika import BasicProperties
from resume_review.models import Resume

logger = logging.getLogger(__name__)


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


@mq.consumer(queue="server.reviewed-resume", exchange="ai", routing_key="reviewed")
async def reviewed_feedback(
    body: bytes,
    properties: BasicProperties,
):
    body = body.decode("utf-8")
    logger.info(f"Received reviewed resume message: {body}")
    try:
        body = json.loads(body)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to decode JSON: {e}")
        return
    feedback = body.get("feedback", None)
    key = body.get("key", None)

    if feedback is None or key is None:
        logger.error("Feedback or key not found in message")
        return

    user_id, resume_id, file_name = key.split("-")

    @sync_to_async
    def perform_database_operations():
        resume_object = Resume.objects.filter(id=int(resume_id)).first()
        if not resume_object:
            logger.error(f"Resume with ID {resume_id} not found")
            return False

        if resume_object.member.id != int(user_id):
            logger.error(
                f"Resume with ID {resume_id} does not belong to user {user_id}"
            )
            return False

        if resume_object.file_name != file_name:
            logger.error(
                f"Resume with ID {resume_id} does not have file name {file_name}"
            )
            return False

        resume_object.feedback = feedback
        resume_object.save()

    successful = await perform_database_operations()
    if successful:
        logger.info(f"Feedback for resume {resume_id} updated with value {feedback}")
