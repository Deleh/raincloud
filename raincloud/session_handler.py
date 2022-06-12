import json
from redis import from_url
import time
import uuid


class RaincloudNetworkException(Exception):
    pass


class SessionHandler:
    def __init__(self, redis_url="redis://127.0.0.1:6379/0"):
        try:
            self.redis = from_url(redis_url)
        except Exception as ex:
            raise RaincloudNetworkException(
                f"Exception while connecting to redis: {ex}"
            )

        if not self.redis.get("raincloud_sessions"):
            self.redis.set("raincloud_sessions", json.dumps([]))

    def _get_sessions(self):
        """Get sessions from redis server."""
        try:
            return json.loads(self.redis.get("raincloud_sessions"))
        except Exception as ex:
            raise RaincloudNetworkException(
                f"Exception while getting sessions from redis: {ex}"
            )

    def _save_sessions(self, sessions):
        """Save 'sessions' to redis."""
        try:
            self.redis.set("raincloud_sessions", json.dumps(sessions))
        except Exception as ex:
            raise RaincloudNetworkException(
                f"Exception while saving sessions to redis: {ex}"
            )

    def create_session_id(self):
        """Create a new session ID."""
        ids = [s[2] for s in self._get_sessions()]
        id_ = uuid.uuid4()
        while id_ in ids:
            id_ = uuid.uuid4()
        return str(id_)

    def add_session(self, directory, id_):
        """Add session with 'id_' allowing access to 'directory'."""
        sessions = self._get_sessions()
        sessions.append((time.time(), directory, id_))
        self._save_sessions(sessions)

    def clean_sessions(self):
        """Remove all sessions which are older than one day."""
        sessions = self._get_sessions()
        sessions = [s for s in sessions if s[0] > time.time() - 86400]
        self._save_sessions(sessions)

    def validate_session(self, directory, id_):
        """check if session with 'id_' is allowed to access 'directory'."""
        valid_dates = [
            s[0] for s in self._get_sessions() if s[1] == directory and s[2] == id_
        ]
        if len(valid_dates) > 0 and valid_dates[0] > time.time() - 86400:
            return True
        return False

    def delete_session(self, id_):
        """Delete session with 'id_'."""
        sessions = self._get_sessions()
        sessions = [s for s in sessions if s[2] != id_]
        self._save_sessions(sessions)
