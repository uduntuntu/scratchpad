from __future__ import annotations
from typing import Set, Dict
import email
from email.header import decode_header
from imapclient import IMAPClient


# --- helpers ---
def decode_mime_header(val: str) -> str:
    """Decode MIME-encoded header into Python string."""
    decoded = ""
    for part, charset in decode_header(val):
        if isinstance(part, bytes):
            try:
                decoded += part.decode(charset or "utf-8", errors="replace")
            except (LookupError, TypeError):
                decoded += part.decode("latin1", errors="replace")
        else:
            decoded += part
    return decoded


# --- IMAP backend ---
class IMAPBackend:
    def __init__(self, host: str, user: str, password: str, port: int = 993):
        self.host = host
        self.user = user
        self.password = password
        self.port = port

    # 1. Connect
    def connect(self) -> IMAPClient:
        """
        Connect to the IMAP server and return an IMAPClient object.
        """
        client = IMAPClient(self.host, port=self.port, ssl=True)
        client.login(self.user, self.password)
        return client

    # 2. List mailboxes
    @staticmethod
    def list_mailboxes(client: IMAPClient) -> set[str]:
        """
        List all mailboxes on the server. Returns a set of mailbox names (str).
        """
        raw_folders = client.list_folders()
        # folder[-1] is mailbox name; IMAPClient handles UTF-7 decoding
        return {folder[-1] for folder in raw_folders}

    # 3. Fetch headers for all messages in a mailbox
    @staticmethod
    def fetch_headers(client: IMAPClient, mailbox: str) -> dict[int, dict[str, str]]:
        """
        Fetch all message headers from a selected mailbox.
        Returns a dict keyed by UID for mass/set operations.
        Only headers are fetched using BODY.PEEK[HEADER].
        """
        client.select_folder(mailbox, readonly=True)
        uids = client.search("ALL")
        headers_by_uid: dict[int, dict[str, str]] = {}

        for uid in uids:
            raw_headers = client.fetch(uid, ["BODY.PEEK[HEADER]"])[uid][b"BODY[HEADER]"]
            msg = email.message_from_bytes(raw_headers)
            headers_by_uid[uid] = {k: decode_mime_header(v) for k, v in msg.items()}

        return headers_by_uid
