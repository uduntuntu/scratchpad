#!/usr/bin/env python3
from __future__ import annotations
from typing import Set, Dict

def filter_by_substring(items: set[str], needle: str) -> set[str]:
    """
    Returns subset of raw bytes where decoded item contains the Unicode needle.
    Works for mailbox selection or any IMAP raw-byte sets.
    """
    result: set[bytes] = set()
    for item in items:
        if needle in item:
            result.add(item) 
    return result


def all_uids(headers_by_uid: dict[bytes, dict[str, str]]) -> set[bytes]:
    """Return all UIDs from the headers dictionary."""
    return set(headers_by_uid.keys())


def list_unique_addresses(
    headers_by_uid: dict[bytes, dict[str, str]], header: str
) -> set[str]:
    """Return a set of unique addresses from the specified header."""
    unique: set[str] = set()
    for hdrs in headers_by_uid.values():
        val = hdrs.get(header, "")
        if val:
            addresses = [addr.strip() for addr in val.split(",")]
            unique.update(addresses)
    return unique


def available_headers(headers_by_uid: dict[bytes, dict[str, str]], uid_set: set[bytes]) -> set[str]:
    """
    Return all unique headers present in the messages identified by uid_set.
    """
    headers: set[str] = set()
    for uid in uid_set:
        hdrs = headers_by_uid.get(uid)
        if hdrs:
            headers.update(hdrs.keys())
    return headers


def filter_by_header_value(
    headers_by_uid: dict[bytes, dict[str, str]], header: str, needle: str
) -> set[bytes]:
    """
    Returns UID set where the specified header contains the Unicode needle.
    """
    result: set[bytes] = set()
    for uid, hdrs in headers_by_uid.items():
        val = hdrs.get(header, "")
        if needle in val:
            result.add(uid)
    return result


def print_messages_in_uid_set(
    headers_by_uid: dict[bytes, dict[str, str]], uid_set: set[bytes]
) -> None:
    """Print message info (UID | Date | From -> To: Subject) for the given UID set."""
    for uid in sorted(uid_set):
        hdrs = headers_by_uid[uid]
        date = hdrs.get("Date", "(no Date)")
        from_ = hdrs.get("From", "(no From)")
        to = hdrs.get("To", "(no To)")
        subject = hdrs.get("Subject", "(no Subject)")
        print(f"{uid} | {date} | {from_} -> {to}: {subject}")

def select_unique(options: set[str], needle: str) -> str:
    if not options:
        print("Empty set of options.")
        return
    if needle in options:
        return needle
    while True:
        matches = filter_by_substring(options, needle)
        if not matches:
            print("No matches found. Try again.")
            return
        elif len(matches) == 1:
            match = next(iter(matches))
            return match
        else:    
            print("Multiple matches found:")
            for mb in sorted(matches):
                print(f"- {mb}")
            print("Enter a more precise search term.")
            return
            

