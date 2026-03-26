from __future__ import annotations
from backend import IMAPBackend, CredentialsRequired
from helpers import (
    all_uids,
    list_unique_addresses,
    available_headers,
    filter_by_header_value,
    print_messages_in_uid_set,
    select_unique,
    print_message,
)
import getpass


class ExitToMenu(Exception):
    pass


def main() -> None:

    host = input("IMAP server host: ").strip()
    user = input("Username: ").strip()
    account = IMAPBackend(host, user, None)
    try:
        client = account.connect()
    except CredentialsRequired:
        password = getpass.getpass("Password: ")
        account = IMAPBackend(host, user, password)
        client = account.connect()

    mailboxes: set[str] = set()
    mailbox: str | None = None

    headers_by_uid: dict[int, dict[str, str]] = {}
    uid_set: set[int] = set()
    headers: set[str] = set()

    print("Connection: OK")

    def needle(prompt: str) -> str:
        value = input(f"{prompt} (or 'exit'): ").strip()
        if value.lower() == "exit":
            raise ExitToMenu()
        return value

    def select_mailbox():
        nonlocal mailboxes, mailbox, headers_by_uid, uid_set, headers

        mailboxes = account.list_mailboxes(client)
        mailbox = None

        while not mailbox:
            mailbox = select_unique(mailboxes, needle("Select folder (partial search OK): "))

        info = client.select_folder(mailbox, readonly=True)
        print(f"Selected folder {mailbox}: {info[b'EXISTS']} messages.")

        headers_by_uid = account.fetch_headers(client, mailbox)
        uid_set = set(headers_by_uid.keys())
        headers = available_headers(headers_by_uid, uid_set)

    def refresh_headers():
        nonlocal headers_by_uid, uid_set, headers, mailbox

        if not mailbox:
            return

        headers_by_uid = account.fetch_headers(client, mailbox)
        uid_set = set(headers_by_uid.keys())
        headers = available_headers(headers_by_uid, uid_set)

        print(f"Fetched {len(uid_set)} messages from {mailbox}")

    def show_senders():
        senders = list_unique_addresses(headers_by_uid, "From")
        print(f"Unique senders ({len(senders)}):")
        for s in sorted(senders):
            print(s)

    def show_recipients():
        recipients = list_unique_addresses(headers_by_uid, "To")
        print(f"Unique recipients ({len(recipients)}):")
        for r in sorted(recipients):
            print(r)

    def list_headers_action():
        print(f"Header fields ({len(headers)}):")
        for h in sorted(headers):
            print(h)

    def filter_uid_action():
        nonlocal uid_set

        try:
            reset = needle("Reset UID set before filtering? (y/N)")
            if reset.lower() == "y":
                uid_set = all_uids(headers_by_uid)

            header = select_unique(headers, needle("Select header (partial name OK)"))
            if not header:
                return

            value = needle(f"Filter by value for header '{header}'")
            filtered = filter_by_header_value(headers_by_uid, header, value)
            uid_set &= filtered

            print(f"Filtered, {len(uid_set)} messages remaining")

        except ExitToMenu:
            print("Returning to main menu.")

    def print_messages_action():
        print_messages_in_uid_set(headers_by_uid, uid_set)

    def show_message_action():
        try:
            uid = int(needle("Select message"))
        except ValueError:
            print("Invalid UID")
            return

        if uid not in uid_set:
            print("UID not in current set")
            return

        data = client.fetch([uid], ["RFC822"])
        print_message(b'data[uid]["RFC822"]')

    def move_uid_set_action():
        nonlocal mailbox

        if not mailbox:
            return

        dst_mailbox = select_unique(mailboxes, needle("Select destination folder"))
        if not dst_mailbox:
            return

        print(f"Moving {len(uid_set)} messages from {mailbox} to {dst_mailbox}")
        IMAPBackend.move_uid_set(client, mailbox, dst_mailbox, uid_set)
        refresh_headers()

    def delete_empty_mailbox():
        nonlocal mailbox

        refresh_headers()

        if not headers_by_uid:
            client.unselect_folder()
            client.delete_folder(mailbox)
            print(f"Deleted empty folder {mailbox}")
            select_mailbox()
        else:
            print(f"Mailbox {mailbox} not empty. Aborted.")

    menu_actions = {
        "1": select_mailbox,
        "2": refresh_headers,
        "3": show_senders,
        "4": show_recipients,
        "5": list_headers_action,
        "6": filter_uid_action,
        "7": print_messages_action,
        "8": show_message_action,
        "9": move_uid_set_action,
        "10": delete_empty_mailbox,
    }

    while not mailbox:
        try:
            select_mailbox()
            break
        except ExitToMenu:
            print("No mailbox selected. Exiting.")
            client.logout()
            return

    while True:
        print("\nMenu:")
        print("0: Exit")
        print("1: Select folder (mailbox)")
        print("2: Refresh headers")
        print("3: Unique senders")
        print("4: Unique recipients")
        print("5: List headers in UID set")
        print("6: Filter UID set by header value")
        print("7: Print messages")
        print("8. Show message")
        print("9. Move messages in UID set")
        print("10. Delete empty mailbox")

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
            print("Returning to main menu.")

    client.logout()
    print("Logged out")


if __name__ == "__main__":
    main()