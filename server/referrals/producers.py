import dataclasses
import logging

logger = logging.getLogger(__name__)


@dataclasses.dataclass
class ReferralStatusChangedEvent:
    referral_id: int
    member_id: int
    notes: str
    previous_status: str
    new_status: str


# used for testing for now
def publish_status_changed_event(
    referral_id, member_id, notes, previous_status, new_status
):
    event = ReferralStatusChangedEvent(
        referral_id=referral_id,
        member_id=member_id,
        notes=notes,
        previous_status=previous_status,
        new_status=new_status,
    )
    logger.info("Publishing status changed event: %s", event)
