## Scope

This project defines tooling and configuration for mailbox refactoring
and mail delivery control.

## Python

Python tooling SHALL:
1. Read mailbox data via IMAP
2. Analyze existing folder structures
3. Search, filter, and move messages


## Sieve

Sieve scripts SHALL:

1. Classify incoming messages efficiently and reliably based on
   spam classification headers provided by SpamAssassin and rspamd.

2. Modify the Subject header when required to encode classification
   conflicts (ham/spam disagreement) needed for downstream manual
   or IMAP-based processing.

3. Manage mail flow for catch-all delivery, including explicit handling 
   at leastof the following categories:
   - Newsletters
   - Advertisements
   - Official / governmental correspondence
   - Invoices and receipts

4. Handle filter overflow by routing any message not matching an explicit
   classification rule into designated fallback mailboxes:
   - Uncaught: messages delivered via catch-all addresses that do not match
     any defined catch-all category
   - Unknown: messages not delivered via catch-all addresses
