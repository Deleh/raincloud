from datetime import datetime, timedelta
import uuid


class SessionHandler:
    def __init__(self):
        self.sessions = []

    def create_session_id(self):
        """Create a new session ID."""
        ids = [s[2] for s in self.sessions]
        id_ = uuid.uuid4()
        while id_ in ids:
            id_ = uuid.uuid4()
        return id_

    def add_session(self, directory, id_):
        """Add session with 'id_' allowing access to 'directory'."""
        self.sessions.append((datetime.now(), directory, id_))

    def clean_sessions(self):
        """Remove all sessions which are older than one day."""
        self.sessions = [
            s for s in self.sessions if s[0] > datetime.now() - timedelta(days=1)
        ]

    def validate_session(self, directory, id_):
        """check if session with 'id_' is allowed to access 'directory'."""
        valid_dates = [s[0] for s in self.sessions if s[1] == directory and s[2] == id_]
        if len(valid_dates) > 0 and valid_dates[0] > datetime.now() - timedelta(days=1):
            return True
        return False

    def delete_session(self, id_):
        """Delete session with 'id_'."""
        self.sessions = [s for s in self.sessions if s[2] != id_]
