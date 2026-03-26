from __future__ import annotations
import email


def filter_by_substring(items: set[str], needle: str) -> set[str]:
    return {item for item in items if needle in item}


def all_uids(headers_by_uid: dict[int, dict[str, str]]) -> set[int]:
    return set(headers_by_uid.keys())


def list_unique_addresses(
    headers_by_uid: dict[int, dict[str, str]], header: str
) -> set[str]:
    unique: set[str] = set()

    for hdrs in headers_by_uid.values():
        val = hdrs.get(header, "")
        if val:
            addresses = [addr.strip() for addr in val.split(",")]
            unique.update(addresses)

    return unique


def available_headers(
    headers_by_uid: dict[int, dict[str, str]],
    uid_set: set[int],
) -> set[str]:
    headers: set[str] = set()

    for uid in uid_set:
        hdrs = headers_by_uid.get(uid)
        if hdrs:
            headers.update(hdrs.keys())

    return headers


def filter_by_header_value(
    headers_by_uid: dict[int, dict[str, str]],
    header: str,
    needle: str,
) -> set[int]:
    result: set[int] = set()

    for uid, hdrs in headers_by_uid.items():
        val = hdrs.get(header, "")
        if needle in val:
            result.add(uid)

    return result


def print_messages_in_uid_set(
    headers_by_uid: dict[int, dict[str, str]],
    uid_set: set[int],
) -> None:
    for uid in sorted(uid_set):
        hdrs = headers_by_uid[uid]
        date = hdrs.get("Date", "(no Date)")
        from_ = hdrs.get("From", "(no From)")
        to = hdrs.get("To", "(no To)")
        subject = hdrs.get("Subject", "(no Subject)")
        print(f"{uid} | {date} | {from_} -> {to}: {subject}")


def print_message(raw: bytes):
    msg = email.message_from_bytes(raw)

    print(f"From: {msg.get('From','')}")
    print(f"To: {msg.get('To','')}")
    print(f"Date: {msg.get('Date','')}")
    print(f"Subject: {msg.get('Subject','')}")
    print()

    body = None

    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/plain":
                body = part.get_payload(decode=True)
                charset = part.get_content_charset() or "utf-8"
                print(body)
                return
    else:
        body = msg.get_payload(decode=True)
        charset = msg.get_content_charset() or "utf-8"

    if body:
        print(body)


def select_unique(options: set[str], needle: str) -> str | None:
    if not options:
        print("Empty set of options.")
        return None

    if needle in options:
        return needle

    matches = filter_by_substring(options, needle)

    if not matches:
        print("No matches found.")
        return None

    if len(matches) == 1:
        return next(iter(matches))

    print("Multiple matches found:")
    for mb in sorted(matches):
        print(f"- {mb}")

    print("Enter a more precise search term.")
    return None