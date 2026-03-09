from __future__ import annotations
from typing import Set, Dict
import email
from email.header import decode_header
from imapclient import IMAPClient
import os
import json
import base64

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

# --- Google Mail backend ---
SCOPES = ["https://mail.google.com/"]

def get_gmail_token(self):

    token_path = os.path.join(self.config_dir, "token.json")
    cred_path = os.path.join(self.config_dir, "credentials.json")

    creds = None

    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)

    if not creds or not creds.valid:

        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())

        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                cred_path,
                SCOPES
            )

            creds = flow.run_local_server(port=0)

        with open(token_path, "w") as f:
            f.write(creds.to_json())

    return creds.token

# --- Exception for credentials exchange ---
class CredentialsRequired(Exception):
    pass

# --- IMAP backend ---
class IMAPBackend:
    def __init__(self, host: str, user: str, password: str, port: int = 993):
        self.host = host
        self.user = user
        self.password = password
        self.port = port

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
