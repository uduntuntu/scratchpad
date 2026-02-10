from __future__ import annotations
from backend import IMAPBackend
from helpers import (
    all_uids,
    list_unique_addresses,
    available_headers,
    filter_by_header_value,
    print_messages,
    select_unique,
)
import getpass

# --- custom exception for returning to main menu ---
class ExitToMenu(Exception):
    pass

def main() -> None:
    # --- credentials ---
    host = input("IMAP server host: ").strip()
    user = input("Username: ").strip()
    password = getpass.getpass("Password: ")

    account = IMAPBackend(host, user, password)
    client = account.connect()
    mailboxes = account.list_mailboxes(client)
    mailbox: str = None

    headers_by_uid: dict[int, dict[str, str]] = None
    uid_set: set[int] = None
    headers: set[str] = None
    print("Connection: OK")

    # --- helper for consistent user input ---
    def needle(prompt: str) -> str:
        """
        Prompt user for input. Raises ExitToMenu if user types 'exit'.
        Strips whitespace automatically.
        """
        value = input(f"{prompt} (or 'exit'): ").strip()
        if value.lower() == "exit":
            raise ExitToMenu()
        return value

    # --- define menu actions ---
    def select_mailbox():
        global mailbox
        mailbox = None
        while not mailbox:
            mailbox = select_unique(mailboxes, needle("Select folder (partial search OK): "))

        info = client.select_folder(mailbox, readonly=True)
        print(f"Selected folder {mailbox}: {info[b'EXISTS']} messages.") 

    def fetch_headers():
        global headers_by_uid, uid_set, headers, mailbox
        headers_by_uid = account.fetch_headers(client, mailbox)
        uid_set = set(headers_by_uid.keys())
        headers = available_headers(headers_by_uid, uid_set)
           
        print(f"Fetched {len(uid_set)} messages from {mailbox}")
   
    def show_senders():
        global headers_by_uid
        fetch_headers()
        senders = list_unique_addresses(headers_by_uid, "From")
        print(f"Unique senders ({len(senders)}):")
        for s in sorted(senders):
            print(s)

    def show_recipients():
        global headers_by_uid
        fetch_headers()
        recipients = list_unique_addresses(headers_by_uid, "To")
        print(f"Unique recipients ({len(recipients)}):")
        for r in sorted(recipients):
            print(r)

    def list_headers_action():
        global headers
        fetch_headers()
        print(f"Header fields ({len(headers)}):")
        for h in sorted(headers):
            print(h)

    def filter_uid_action():
        global headers, headers_by_uid, uid_set
        fetch_headers()
        # reset UID set if requested
        try:
            reset = needle("Reset UID set before filtering? (y/N)")
            if reset.lower() == "y":
                uid_set = all_uids(headers_by_uid)

            # select header interactively
            header = select_unique(headers, needle("Select header (partial name OK)"))

            # select value to filter by
            value = needle(f"Filter by value for header '{header}'")
            filtered = filter_by_header_value(headers_by_uid, header, value)
            uid_set &= filtered
            print(f"Filtered, {len(uid_set)} messages remaining")
        except ExitToMenu:
            # return to main menu cleanly
            print("Returning to main menu.")

    def print_messages_action():
        global headers_by_uid, uid_set
        fetch_headers()
        print_messages(headers_by_uid, uid_set)

    # --- dispatch dictionary ---
    menu_actions = {
        "1": select_mailbox,
        "2": fetch_headers,
        "3": show_senders,
        "4": show_recipients,
        "5": list_headers_action,
        "6": filter_uid_action,
        "7": print_messages_action,
    }

# --- Select initial mailbox ---
    while not mailbox:
        try:
            select_mailbox()
            break
        except ExitToMenu:
            print("No mailbox selected. Exiting.")
            client.logout()
            return

    # --- main menu loop ---
    while True:
        print("\nMenu:")
        print("0: Exit")
        print("1: Select folder (mailbox)")
        print("2: Fetch headers")
        print("3: Unique senders")
        print("4: Unique recipients")
        print("5: List headers in UID set")
        print("6: Filter UID set by header value")
        print("7: Print messages")
        try:
            choice = needle("Enter choice")
            if choice == "0":
                break
            action = menu_actions.get(choice)
            if action:
                action()
            else:
                print("Invalid choice")
        except ExitToMenu:
            # Any 'exit' typed during needle() inside actions returns here
            print("Returning to main menu.")

    client.logout()
    print("Logged out")

if __name__ == "__main__":
    main()
