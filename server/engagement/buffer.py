import threading
import time
import logging
from collections import defaultdict
from typing import Dict
from pydantic import BaseModel
from django.db import transaction
from django.db.models import F
from members.models import User
from engagement.models import DiscordMessageStats

logger = logging.getLogger(__name__)


class Message(BaseModel):
    discord_id: int
    channel_id: int


class MessageBuffer:
    def __init__(self, batch_size=200, max_size=1000, flush_interval=120):
        self._buffer = []
        self._lock = threading.Lock()
        self._last_flush = time.time()

        self._batch_size = batch_size
        self._max_size = max_size
        self._flush_interval = flush_interval

    def add_message(self, message: Message) -> None:
        with self._lock:
            if len(self._buffer) >= self._max_size:
                logger.error("buffer full, dropping message")
                return

            self._buffer.append(message)
            should_flush = (
                len(self._buffer) >= self._batch_size
                or time.time() - self._last_flush >= self._flush_interval
            )

        if should_flush:
            self.flush_to_db()

    def _aggregate(self, messages) -> Dict[int, Dict[int, int]]:
        result = defaultdict(lambda: defaultdict(int))
        for msg in messages:
            result[msg.channel_id][msg.discord_id] += 1
        return result

    def flush_to_db(self) -> None:
        try:
            self._flush_to_db()
        except Exception as e:
            logger.exception(f"flush error: {e}")

    def _flush_to_db(self) -> None:
        if not self._buffer:
            return

        with self._lock:
            messages = self._buffer[:]
            self._buffer.clear()
            self._last_flush = time.time()

        if not messages:
            return

        try:
            with transaction.atomic():
                aggregated = self._aggregate(messages)
                if not aggregated:
                    return

                discord_ids = {
                    discord_id
                    for counts in aggregated.values()
                    for discord_id in counts
                }

                users = User.objects.filter(discord_id__in=discord_ids).values(
                    "id", "discord_id"
                )
                user_map = {u["discord_id"]: u["id"] for u in users}

                missing = discord_ids - user_map.keys()
                if missing:
                    logger.warning(f"missing users: {list(missing)[:10]}")

                for counts in aggregated.values():
                    counts = {k: v for k, v in counts.items() if k in user_map}

                stats_count = 0
                for channel_id, channel_counts in aggregated.items():
                    if not channel_counts:
                        continue

                    create_batch = [
                        DiscordMessageStats(
                            member_id=user_map[discord_id],
                            channel_id=channel_id,
                            message_count=0,
                        )
                        for discord_id in channel_counts
                        if discord_id in user_map
                    ]

                    DiscordMessageStats.objects.bulk_create(
                        create_batch, ignore_conflicts=True
                    )

                    stats = DiscordMessageStats.objects.filter(
                        member_id__in=[m.member_id for m in create_batch],
                        channel_id=channel_id,
                    ).values("channel_id", "member_id", "id")

                    stats_map = {
                        (int(s["member_id"]), int(s["channel_id"])): int(s["id"])
                        for s in stats
                    }

                    update_batch = [
                        DiscordMessageStats(
                            id=stats_map[(member_id, channel_id)],
                            member_id=member_id,
                            channel_id=channel_id,
                            message_count=F("message_count") + count,
                        )
                        for discord_id, count in channel_counts.items()
                        if discord_id in user_map
                        and ((member_id := user_map[discord_id]), channel_id)
                        in stats_map
                    ]

                    DiscordMessageStats.objects.bulk_update(
                        update_batch, ["message_count"]
                    )
                    stats_count += len(update_batch)

                logger.info(
                    f"flushed {len(messages)} messages across {len(aggregated)} channels to db, updated {stats_count} stats"
                )

        except Exception as e:
            logger.exception(f"flush failed: {e}")
            with self._lock:
                self._buffer.extend(messages)
            raise

    def __del__(self):
        if self._buffer:
            try:
                self.flush_to_db()
            except Exception as e:
                logger.exception(f"shutdown flush failed: {e}")
