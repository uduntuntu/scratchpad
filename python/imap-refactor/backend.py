from __future__ import annotations
from typing import Set, Dict
import email
from email.header import decode_header
from imapclient import IMAPClient
import os

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

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


# --- Exception for credentials exchange ---
class CredentialsRequired(Exception):
    pass

# --- IMAP backend ---
class IMAPBackend:
    def __init__(self, host: str, user: str, password: str | None, port: int = 993):
        self.host = host
        self.user = user
        self.password = password
        self.port = port

    # --- Google Mail backend ---
    SCOPES = ["https://mail.google.com/"]

    def get_gmail_token(self) -> str:

        token_path = "token.json"
        cred_path = "credentials.json"

        creds = None

        if os.path.exists(token_path):
            creds = Credentials.from_authorized_user_file(token_path, self.SCOPES)

        if not creds or not creds.valid:

            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())

            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    cred_path,
                    self.SCOPES
                )

                creds = flow.run_local_server(port=0)

            with open(token_path, "w") as f:
                f.write(creds.to_json())

        token = creds.token
        if token is None:
            raise RuntimeError("OAuth token is missing")

        return token

    # 1. Connect
    def connect(self):

        client = IMAPClient(self.host, port=self.port, ssl=True)

        if self.host.endswith("gmail.com"):
            token = self.get_gmail_token()
            client.oauth2_login(self.user, token)
            return client

        if not self.user or not self.password:
            raise CredentialsRequired()

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
        client.select_folder(mailbox, readonly=True)

        uids = client.search("ALL")
        headers_by_uid: dict[int, dict[str, str]] = {}

        chunk_size = 500
        
        if not uids:
            return headers_by_uid

        for i in range(0, len(uids), chunk_size):
            chunk = uids[i:i + chunk_size]

            data = client.fetch(chunk, ["BODY.PEEK[HEADER]"])

            for uid, msgdata in data.items():
                raw_headers = msgdata[b"BODY[HEADER]"]
                if not isinstance(raw_headers, (bytes, bytearray)):
                    continue
                msg = email.message_from_bytes(raw_headers)
                headers_by_uid[uid] = {k: decode_mime_header(v) for k, v in msg.items()}

        return headers_by_uid
    
    # 4. Move all messages identified by UID from mailbox to another

    @staticmethod
    def move_uid_set(
        client: IMAPClient, 
        src_mailbox: str, 
        dst_mailbox: str, 
        uid_set: set[int],
        ) -> None:

        if not uid_set:
            return

        client.select_folder(src_mailbox)
        client.move(uid_set, dst_mailbox)