# Exchange EWS MCP — Production Readiness Implementation Plan

> **For Claude:** REQUIRED: Use /subagent-dev to implement this plan. Each task specifies its Agent — dispatch that Amplifier agent as the subagent for implementation. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make exchange-ews MCP production-ready with multi-auth, 29 tools (16 new), bulk operations, and uv dependency management — while keeping full lab backward compatibility.

**Architecture:** Single-file MCP server (server.py) with configurable auth (auto/ntlm/basic/kerberos), SSL toggle, and optional OU scoping. stdio transport, exchangelib backend.

**Tech Stack:** Python 3.11+, exchangelib >=5.0, requests-kerberos (optional), uv package manager

---

## Error Map

| CODEPATH | WHAT CAN FAIL | RESCUE |
|---|---|---|
| get_account() NTLM | Wrong credentials | Clear error: "Authentication failed. Check username/password in config.json" |
| get_account() NTLM | Server unreachable | "Cannot connect to \<server\>. Verify server hostname and network." |
| get_account() auto | Both NTLM+Basic fail | Report both errors |
| get_account() kerberos | No ticket | "Kerberos ticket not found. Run kinit." |
| SSL verification | Cert untrusted | "SSL verification failed. If using self-signed cert, set verify_ssl: false" |
| reply/forward | message_id not found | "Message not found: \<id\>" |
| download_attachment | No attachments on message | Return empty list with note |
| download_attachment | attachment_name not found | "Attachment '\<name\>' not found. Available: [list]" |
| create_draft | Invalid recipient | exchangelib error surfaced |
| send_draft | Draft not found | "Draft not found: \<id\>" |
| bulk_move | Target folder doesn't exist | "Folder '\<name\>' not found. Create it first with create_folder." |
| bulk_move/delete | Filter matches 0 items | Return count=0, no error |
| bulk_delete permanent=true | Large batch timeout | Process in batches of 100 |
| create_folder | Already exists | "Folder '\<name\>' already exists" |
| delete_folder | Non-empty folder | "Folder '\<name\>' has \<N\> items. Move/delete items first or use force param." |
| rename_folder | Name collision | "A folder named '\<name\>' already exists" |
| get_thread | No conversation_id | "Message has no conversation ID" |
| set_out_of_office | Insufficient permissions | Surface exchangelib error |
| mark_read (bulk) | Filter matches 0 | Return count=0, no error |

---

## Task 1: [TRACER] Auth + SSL + Config Refactor

**Agent:** `amplifier-core:modular-builder`

**Files:**
- Modify: `C:\claude\exchange-ews-mcp\server.py` (lines 1–80)
- Modify: `C:\claude\exchange-ews-mcp\config.example.json`

**Steps:**

- [ ] **1.1** Rewrite lines 1–33 to make Kerberos import conditional. Remove the global `NoVerifyHTTPAdapter` assignment and the monkey-patch of `transport.get_auth_instance`. Replace with:

  ```python
  #!/usr/bin/env python3
  """Exchange EWS MCP Server — end-user mailbox operations for Claude Code."""

  import json
  import sys
  import os
  import re
  import base64
  import time
  import warnings
  from datetime import datetime, timedelta, timezone

  from exchangelib import (
      Account, Configuration, IMPERSONATION, DELEGATE,
      Credentials, NTLM, Message, Mailbox, HTMLBody,
      CalendarItem, EWSDateTime, OofSettings,
  )
  from exchangelib.protocol import BaseProtocol, NoVerifyHTTPAdapter

  _ssl_configured = False
  ```

  Keep Kerberos import deferred — only imported inside `get_account()` when `auth_type == "kerberos"`.

- [ ] **1.2** Rewrite `get_config()` (lines 52–62) to add field validation:

  ```python
  def get_config():
      global _config_cache
      if _config_cache:
          return _config_cache
      config_path = os.environ.get(
          "EWS_CONFIG",
          os.path.expanduser("~/.config/exchange-ews-mcp/config.json"),
      )
      with open(config_path) as f:
          cfg = json.load(f)

      # Apply defaults
      cfg.setdefault("auth_type", "auto")
      cfg.setdefault("verify_ssl", True)
      cfg.setdefault("scope_ou", None)
      cfg.setdefault("poll_interval", 3)

      # Validate required fields per auth type
      auth_type = cfg["auth_type"]
      if auth_type in ("ntlm", "basic", "auto"):
          if not cfg.get("username") or not cfg.get("password"):
              raise ValueError(
                  f"auth_type '{auth_type}' requires 'username' and 'password' in config.json"
              )
      if not cfg.get("server"):
          raise ValueError("'server' is required in config.json")

      _config_cache = cfg
      return _config_cache
  ```

- [ ] **1.3** Add `_setup_ssl(verify: bool)` function after `get_config()`:

  ```python
  def _setup_ssl(verify: bool):
      """Configure SSL verification globally. Called once on first account creation."""
      global _ssl_configured
      if _ssl_configured:
          return
      if not verify:
          warnings.filterwarnings("ignore", message="Unverified HTTPS request")
          BaseProtocol.HTTP_ADAPTER_CLS = NoVerifyHTTPAdapter
      # If verify=True: leave default behavior (SSL verification enabled)
      _ssl_configured = True
  ```

- [ ] **1.4** Rewrite `get_account()` (lines 65–80) to dispatch based on `auth_type`:

  ```python
  def get_account(email: str):
      if email in _account_cache:
          return _account_cache[email]

      cfg = get_config()
      _setup_ssl(cfg["verify_ssl"])
      auth_type = cfg["auth_type"]

      if auth_type == "kerberos":
          from exchangelib import transport
          from requests_kerberos import HTTPKerberosAuth, OPTIONAL
          KERBEROS = "kerberos"
          transport.AUTH_TYPE_MAP[KERBEROS] = HTTPKerberosAuth
          _orig = transport.get_auth_instance
          def _patched(at, **kw):
              if at == KERBEROS:
                  return HTTPKerberosAuth(mutual_authentication=OPTIONAL)
              return _orig(at, **kw)
          transport.get_auth_instance = _patched
          try:
              config = Configuration(server=cfg["server"], auth_type=KERBEROS)
          except Exception as e:
              raise RuntimeError(f"Kerberos ticket not found. Run kinit. Detail: {e}")

      elif auth_type == "ntlm":
          try:
              credentials = Credentials(cfg["username"], cfg["password"])
              config = Configuration(
                  server=cfg["server"],
                  credentials=credentials,
                  auth_type=NTLM,
              )
          except Exception as e:
              raise RuntimeError(
                  f"Authentication failed. Check username/password in config.json. Detail: {e}"
              )

      elif auth_type == "basic":
          try:
              credentials = Credentials(cfg["username"], cfg["password"])
              config = Configuration(
                  server=cfg["server"],
                  credentials=credentials,
              )
          except Exception as e:
              raise RuntimeError(
                  f"Authentication failed. Check username/password in config.json. Detail: {e}"
              )

      else:  # auto — try NTLM first, fall back to Basic
          from exchangelib.errors import UnauthorizedError, TransportError
          credentials = Credentials(cfg["username"], cfg["password"])
          ntlm_error = None
          try:
              config = Configuration(
                  server=cfg["server"],
                  credentials=credentials,
                  auth_type=NTLM,
              )
              account = Account(
                  primary_smtp_address=email,
                  config=config,
                  autodiscover=False,
                  access_type=IMPERSONATION,
              )
              # Probe to force connection
              _ = account.inbox.total_count
              _account_cache[email] = account
              return account
          except (UnauthorizedError, TransportError, Exception) as e:
              ntlm_error = str(e)

          try:
              config = Configuration(
                  server=cfg["server"],
                  credentials=credentials,
              )
          except Exception as e:
              raise RuntimeError(
                  f"Auto auth failed. NTLM error: {ntlm_error}. Basic error: {e}"
              )

      try:
          account = Account(
              primary_smtp_address=email,
              config=config,
              autodiscover=False,
              access_type=IMPERSONATION,
          )
      except Exception as e:
          server = cfg.get("server", "unknown")
          raise RuntimeError(
              f"Cannot connect to {server}. Verify server hostname and network. Detail: {e}"
          )

      _account_cache[email] = account
      return account
  ```

- [ ] **1.5** Update `config.example.json` with all fields documented:

  ```json
  {
    "_comment_server": "Exchange server hostname or IP",
    "server": "mail.example.com",

    "_comment_auth": "Auth type: auto (default), ntlm, basic, kerberos",
    "auth_type": "auto",

    "_comment_creds": "Required for ntlm/basic/auto. Omit for kerberos.",
    "username": "DOMAIN\\your.username",
    "password": "your-password",

    "_comment_ssl": "Set false for self-signed certs (lab use only)",
    "verify_ssl": true,

    "_comment_scope": "Optional OU scope for documentation/logging. Null = unrestricted.",
    "scope_ou": null,

    "_comment_poll": "Polling interval in seconds for verify_* tools (default: 3)",
    "poll_interval": 3
  }
  ```

- [ ] **1.6** Test: confirm that with the lab config (`auth_type: kerberos`, `verify_ssl: false`), `get_account()` returns a valid `Account` object and `account.inbox.total_count` does not raise. Confirm with a production-style NTLM config (can mock or document test steps).

- [ ] **1.7** Commit:
  ```
  feat(exchange-ews): configurable multi-auth with NTLM/Basic/Kerberos/Auto
  ```

---

## Task 2: Folder Management Tools

**Agent:** `amplifier-core:modular-builder`

**Files:**
- Modify: `C:\claude\exchange-ews-mcp\server.py` (add tool functions after line 632; add entries to TOOLS dict)

**Steps:**

- [ ] **2.1** Add helper `_get_folder(account, folder_name)` after the existing tool functions. This resolves a folder by name using `account.root.walk()`. Returns the folder object or raises `ValueError` with a helpful message:

  ```python
  def _get_folder(account, folder_name: str):
      """Resolve a folder by display name. Raises ValueError if not found."""
      for folder in account.root.walk():
          if folder.name == folder_name:
              return folder
      raise ValueError(
          f"Folder '{folder_name}' not found. "
          f"Use the folders tool to list available folders."
      )
  ```

- [ ] **2.2** Add `tool_create_folder()`:

  ```python
  def tool_create_folder(params: dict) -> dict:
      email = params["email"]
      name = params["name"]
      parent_name = params.get("parent_folder", "Inbox")
      account = get_account(email)

      from exchangelib import Folder

      # Check for name collision
      parent = _get_folder(account, parent_name)
      for child in parent.children:
          if child.name == name:
              return {"error": f"Folder '{name}' already exists under '{parent_name}'"}

      new_folder = Folder(parent=parent, name=name)
      new_folder.save()
      return {
          "created": True,
          "folder_name": name,
          "parent_folder": parent_name,
          "folder_id": new_folder.id,
      }
  ```

- [ ] **2.3** Add `tool_delete_folder()`:

  ```python
  def tool_delete_folder(params: dict) -> dict:
      email = params["email"]
      folder_name = params["folder_name"]
      force = params.get("force", False)
      account = get_account(email)

      folder = _get_folder(account, folder_name)
      item_count = folder.total_count

      if item_count > 0 and not force:
          return {
              "error": (
                  f"Folder '{folder_name}' has {item_count} items. "
                  f"Move/delete items first or use force=true to delete with contents."
              )
          }

      if item_count > 0 and force:
          folder.empty(delete_sub_folders=True)

      folder.delete()
      return {"deleted": True, "folder_name": folder_name, "items_removed": item_count}
  ```

- [ ] **2.4** Add `tool_rename_folder()`:

  ```python
  def tool_rename_folder(params: dict) -> dict:
      email = params["email"]
      folder_name = params["folder_name"]
      new_name = params["new_name"]
      account = get_account(email)

      folder = _get_folder(account, folder_name)

      # Check for collision at same parent level
      parent = folder.parent
      if parent:
          for sibling in parent.children:
              if sibling.name == new_name and sibling.id != folder.id:
                  return {"error": f"A folder named '{new_name}' already exists"}

      folder.name = new_name
      folder.save(update_fields=["name"])
      return {"renamed": True, "old_name": folder_name, "new_name": new_name}
  ```

- [ ] **2.5** Add TOOLS dict entries for all three folder tools:

  ```python
  "create_folder": {
      "description": "Create a new mail folder under a specified parent folder",
      "inputSchema": {
          "type": "object",
          "properties": {
              "email": {"type": "string", "description": "Mailbox email address"},
              "name": {"type": "string", "description": "Name for the new folder"},
              "parent_folder": {
                  "type": "string",
                  "description": "Parent folder name (default: Inbox)",
                  "default": "Inbox"
              },
          },
          "required": ["email", "name"],
      },
      "handler": tool_create_folder,
  },
  "delete_folder": {
      "description": "Delete a mail folder. Fails if non-empty unless force=true",
      "inputSchema": {
          "type": "object",
          "properties": {
              "email": {"type": "string", "description": "Mailbox email address"},
              "folder_name": {"type": "string", "description": "Name of folder to delete"},
              "force": {
                  "type": "boolean",
                  "description": "Delete folder and all contents (default: false)",
                  "default": False,
              },
          },
          "required": ["email", "folder_name"],
      },
      "handler": tool_delete_folder,
  },
  "rename_folder": {
      "description": "Rename a mail folder",
      "inputSchema": {
          "type": "object",
          "properties": {
              "email": {"type": "string", "description": "Mailbox email address"},
              "folder_name": {"type": "string", "description": "Current folder name"},
              "new_name": {"type": "string", "description": "New folder name"},
          },
          "required": ["email", "folder_name", "new_name"],
      },
      "handler": tool_rename_folder,
  },
  ```

- [ ] **2.6** Test each tool manually or via a test script confirming create/delete/rename work end-to-end in the lab Exchange environment.

- [ ] **2.7** Commit:
  ```
  feat(exchange-ews): add folder management tools (create, delete, rename)
  ```

---

## Task 3: Reply, Forward, and Thread View

**Agent:** `amplifier-core:modular-builder`

**Files:**
- Modify: `C:\claude\exchange-ews-mcp\server.py`

**Steps:**

- [ ] **3.1** Add shared `_find_message(account, message_id)` helper. This searches across ALL folders so reply/forward/move work on any mailbox folder, not just inbox:

  ```python
  def _find_message(account, message_id: str):
      """Find a message by ID across all folders. Raises ValueError if not found."""
      for folder in account.root.walk():
          try:
              items = list(folder.filter(id=message_id))
              if items:
                  return items[0]
          except Exception:
              continue
      raise ValueError(f"Message not found: {message_id}")
  ```

- [ ] **3.2** Add `tool_reply()`:

  ```python
  def tool_reply(params: dict) -> dict:
      email = params["email"]
      message_id = params["message_id"]
      body = params["body"]
      reply_all = params.get("reply_all", False)
      account = get_account(email)

      item = _find_message(account, message_id)
      subject = f"Re: {item.subject}" if item.subject else "Re: (no subject)"

      if reply_all:
          item.reply_all(subject=subject, body=body)
      else:
          item.reply(subject=subject, body=body)

      return {
          "sent": True,
          "reply_all": reply_all,
          "original_subject": item.subject,
          "reply_subject": subject,
      }
  ```

- [ ] **3.3** Add `tool_forward()`:

  ```python
  def tool_forward(params: dict) -> dict:
      email = params["email"]
      message_id = params["message_id"]
      to = params["to"]
      body = params.get("body", "")
      account = get_account(email)

      item = _find_message(account, message_id)
      subject = f"Fwd: {item.subject}" if item.subject else "Fwd: (no subject)"

      # Normalize to list
      to_list = [to] if isinstance(to, str) else to
      recipients = [Mailbox(email_address=addr) for addr in to_list]

      item.forward(subject=subject, body=body, to_recipients=recipients)

      return {
          "forwarded": True,
          "to": to_list,
          "original_subject": item.subject,
          "forward_subject": subject,
      }
  ```

- [ ] **3.4** Add `tool_get_thread()`:

  ```python
  def tool_get_thread(params: dict) -> dict:
      email = params["email"]
      message_id = params["message_id"]
      account = get_account(email)

      item = _find_message(account, message_id)
      conv_id = item.conversation_id
      if not conv_id:
          return {"error": "Message has no conversation ID"}

      # Collect thread messages across all folders
      thread_messages = []
      for folder in account.root.walk():
          try:
              msgs = folder.filter(conversation_id=conv_id).order_by("datetime_received")
              for msg in msgs:
                  thread_messages.append({
                      "id": msg.id,
                      "subject": msg.subject,
                      "from": str(msg.sender) if msg.sender else None,
                      "date": msg.datetime_received.isoformat() if msg.datetime_received else None,
                      "is_read": msg.is_read,
                      "folder": folder.name,
                      "body_preview": (msg.text_body or "")[:200] if msg.text_body else "",
                  })
          except Exception:
              continue

      # Sort by received date
      thread_messages.sort(key=lambda m: m["date"] or "")

      return {
          "conversation_id": str(conv_id),
          "message_count": len(thread_messages),
          "messages": thread_messages,
      }
  ```

- [ ] **3.5** Add TOOLS dict entries:

  ```python
  "reply": {
      "description": "Reply to an email message, optionally replying to all recipients",
      "inputSchema": {
          "type": "object",
          "properties": {
              "email": {"type": "string", "description": "Mailbox email address"},
              "message_id": {"type": "string", "description": "ID of the message to reply to"},
              "body": {"type": "string", "description": "Reply body text"},
              "reply_all": {
                  "type": "boolean",
                  "description": "Reply to all recipients (default: false)",
                  "default": False,
              },
          },
          "required": ["email", "message_id", "body"],
      },
      "handler": tool_reply,
  },
  "forward": {
      "description": "Forward an email message to one or more recipients",
      "inputSchema": {
          "type": "object",
          "properties": {
              "email": {"type": "string", "description": "Mailbox email address"},
              "message_id": {"type": "string", "description": "ID of the message to forward"},
              "to": {
                  "oneOf": [
                      {"type": "string"},
                      {"type": "array", "items": {"type": "string"}},
                  ],
                  "description": "Recipient email address(es)",
              },
              "body": {"type": "string", "description": "Optional additional text to prepend"},
          },
          "required": ["email", "message_id", "to"],
      },
      "handler": tool_forward,
  },
  "get_thread": {
      "description": "Get all messages in the same conversation thread as a given message",
      "inputSchema": {
          "type": "object",
          "properties": {
              "email": {"type": "string", "description": "Mailbox email address"},
              "message_id": {"type": "string", "description": "ID of any message in the thread"},
          },
          "required": ["email", "message_id"],
      },
      "handler": tool_get_thread,
  },
  ```

- [ ] **3.6** Test: send a test reply and verify it appears in the recipient's inbox. Confirm thread view returns messages from multiple folders.

- [ ] **3.7** Commit:
  ```
  feat(exchange-ews): add reply, forward, and thread view tools
  ```

---

## Task 4: Attachments and Drafts

**Agent:** `amplifier-core:modular-builder`

**Files:**
- Modify: `C:\claude\exchange-ews-mcp\server.py`

**Steps:**

- [ ] **4.1** Add `tool_download_attachment()`. Ensure `import base64` is present in the top-level imports (added in Task 1):

  ```python
  def tool_download_attachment(params: dict) -> dict:
      email = params["email"]
      message_id = params["message_id"]
      attachment_name = params.get("attachment_name")
      account = get_account(email)

      from exchangelib.items import FileAttachment

      item = _find_message(account, message_id)

      if not item.attachments:
          return {"attachments": [], "note": "No attachments on this message"}

      file_attachments = [
          att for att in item.attachments
          if isinstance(att, FileAttachment)
      ]

      if attachment_name:
          file_attachments = [a for a in file_attachments if a.name == attachment_name]
          if not file_attachments:
              all_names = [a.name for a in item.attachments if isinstance(a, FileAttachment)]
              return {
                  "error": (
                      f"Attachment '{attachment_name}' not found. "
                      f"Available: {all_names}"
                  )
              }

      results = []
      for att in file_attachments:
          results.append({
              "name": att.name,
              "size": att.size,
              "content_type": att.content_type,
              "content_base64": base64.b64encode(att.content).decode("utf-8"),
          })

      return {"attachments": results, "count": len(results)}
  ```

- [ ] **4.2** Add `tool_create_draft()`:

  ```python
  def tool_create_draft(params: dict) -> dict:
      email = params["email"]
      to = params["to"]
      subject = params["subject"]
      body = params["body"]
      cc = params.get("cc")
      account = get_account(email)

      to_list = [to] if isinstance(to, str) else to
      to_recipients = [Mailbox(email_address=addr) for addr in to_list]

      cc_recipients = []
      if cc:
          cc_list = [cc] if isinstance(cc, str) else cc
          cc_recipients = [Mailbox(email_address=addr) for addr in cc_list]

      msg_body = HTMLBody(body) if "<" in body else body

      draft = Message(
          account=account,
          folder=account.drafts,
          subject=subject,
          body=msg_body,
          to_recipients=to_recipients,
          cc_recipients=cc_recipients if cc_recipients else None,
      )
      draft.save()

      return {
          "created": True,
          "draft_id": draft.id,
          "subject": subject,
          "to": to_list,
      }
  ```

- [ ] **4.3** Add `tool_list_drafts()`:

  ```python
  def tool_list_drafts(params: dict) -> dict:
      email = params["email"]
      limit = params.get("limit", 10)
      account = get_account(email)

      drafts = []
      for draft in account.drafts.all().order_by("-datetime_created")[:limit]:
          drafts.append({
              "id": draft.id,
              "subject": draft.subject,
              "to": [str(r) for r in (draft.to_recipients or [])],
              "created": draft.datetime_created.isoformat() if draft.datetime_created else None,
          })

      return {"drafts": drafts, "count": len(drafts)}
  ```

- [ ] **4.4** Add `tool_send_draft()`:

  ```python
  def tool_send_draft(params: dict) -> dict:
      email = params["email"]
      draft_id = params["draft_id"]
      account = get_account(email)

      try:
          drafts = list(account.drafts.filter(id=draft_id))
          if not drafts:
              return {"error": f"Draft not found: {draft_id}"}
          draft = drafts[0]
          draft.send()
          return {"sent": True, "draft_id": draft_id, "subject": draft.subject}
      except Exception as e:
          return {"error": f"Failed to send draft: {e}"}
  ```

- [ ] **4.5** Add TOOLS dict entries:

  ```python
  "download_attachment": {
      "description": "Download attachment(s) from an email message as base64-encoded content",
      "inputSchema": {
          "type": "object",
          "properties": {
              "email": {"type": "string", "description": "Mailbox email address"},
              "message_id": {"type": "string", "description": "ID of the message"},
              "attachment_name": {
                  "type": "string",
                  "description": "Specific attachment filename (optional — returns all if omitted)",
              },
          },
          "required": ["email", "message_id"],
      },
      "handler": tool_download_attachment,
  },
  "create_draft": {
      "description": "Create a new draft email (does not send)",
      "inputSchema": {
          "type": "object",
          "properties": {
              "email": {"type": "string", "description": "Mailbox email address"},
              "to": {
                  "oneOf": [
                      {"type": "string"},
                      {"type": "array", "items": {"type": "string"}},
                  ],
                  "description": "Recipient email address(es)",
              },
              "subject": {"type": "string", "description": "Email subject"},
              "body": {"type": "string", "description": "Email body (HTML or plain text)"},
              "cc": {
                  "oneOf": [
                      {"type": "string"},
                      {"type": "array", "items": {"type": "string"}},
                  ],
                  "description": "CC recipient(s) (optional)",
              },
          },
          "required": ["email", "to", "subject", "body"],
      },
      "handler": tool_create_draft,
  },
  "list_drafts": {
      "description": "List drafts in the Drafts folder",
      "inputSchema": {
          "type": "object",
          "properties": {
              "email": {"type": "string", "description": "Mailbox email address"},
              "limit": {"type": "integer", "description": "Max drafts to return (default: 10)"},
          },
          "required": ["email"],
      },
      "handler": tool_list_drafts,
  },
  "send_draft": {
      "description": "Send an existing draft by its ID",
      "inputSchema": {
          "type": "object",
          "properties": {
              "email": {"type": "string", "description": "Mailbox email address"},
              "draft_id": {"type": "string", "description": "ID of the draft to send"},
          },
          "required": ["email", "draft_id"],
      },
      "handler": tool_send_draft,
  },
  ```

- [ ] **4.6** Test draft lifecycle: create → list (confirm appears) → send (confirm arrives in recipient inbox). Test attachment download with a known message containing a file.

- [ ] **4.7** Commit:
  ```
  feat(exchange-ews): add attachment download and draft management tools
  ```

---

## Task 5: Message Management (mark_read, flag, OOF)

**Agent:** `amplifier-core:modular-builder`

**Files:**
- Modify: `C:\claude\exchange-ews-mcp\server.py`

**Steps:**

- [ ] **5.1** Add `tool_mark_read()`. Supports both single-message mode (via `message_id`) and bulk mode (via `filter` dict):

  ```python
  def tool_mark_read(params: dict) -> dict:
      email = params["email"]
      message_id = params.get("message_id")
      filter_params = params.get("filter")
      is_read = params.get("is_read", True)
      account = get_account(email)

      if message_id:
          item = _find_message(account, message_id)
          item.is_read = is_read
          item.save(update_fields=["is_read"])
          return {"updated": 1, "is_read": is_read, "message_id": message_id}

      if filter_params:
          qs = _build_filter(account, filter_params)
          count = 0
          for item in qs:
              item.is_read = is_read
              item.save(update_fields=["is_read"])
              count += 1
          return {"updated": count, "is_read": is_read}

      return {"error": "Provide either message_id or filter"}
  ```

- [ ] **5.2** Add `tool_flag_message()`. Imports `Flag` from exchangelib:

  ```python
  def tool_flag_message(params: dict) -> dict:
      email = params["email"]
      message_id = params["message_id"]
      flag = params.get("flag", "flagged")
      account = get_account(email)

      from exchangelib.fields import Flag as EWSFlag

      item = _find_message(account, message_id)

      # Map string to exchangelib flag status
      flag_map = {
          "flagged": "Flagged",
          "complete": "Complete",
          "not_flagged": "NotFlagged",
      }
      flag_status = flag_map.get(flag.lower(), "Flagged")

      # exchangelib stores flag status as a string property
      item.flag = item.flag.__class__(flag_status=flag_status) if item.flag else None
      item.save(update_fields=["flag"])

      return {"flagged": True, "message_id": message_id, "flag_status": flag_status}
  ```

  Note: If `Flag` import fails (API differs by exchangelib version), the implementer should fall back to setting `item.importance` as a proxy, documenting the discrepancy.

- [ ] **5.3** Add `tool_get_out_of_office()`:

  ```python
  def tool_get_out_of_office(params: dict) -> dict:
      email = params["email"]
      account = get_account(email)

      oof = account.oof_settings
      return {
          "state": str(oof.state) if oof.state else None,
          "external_audience": str(oof.external_audience) if oof.external_audience else None,
          "internal_reply": oof.internal_reply,
          "external_reply": oof.external_reply,
          "start": oof.start.isoformat() if oof.start else None,
          "end": oof.end.isoformat() if oof.end else None,
      }
  ```

- [ ] **5.4** Add `tool_set_out_of_office()`:

  ```python
  def tool_set_out_of_office(params: dict) -> dict:
      email = params["email"]
      state = params["state"]
      internal_reply = params.get("internal_reply", "")
      external_reply = params.get("external_reply", "")
      start = params.get("start")
      end = params.get("end")
      account = get_account(email)

      start_dt = datetime.fromisoformat(start) if start else None
      end_dt = datetime.fromisoformat(end) if end else None

      try:
          settings = OofSettings(
              state=state,
              internal_reply=internal_reply,
              external_reply=external_reply,
              start=start_dt,
              end=end_dt,
          )
          account.oof_settings = settings
          return {"set": True, "state": state}
      except Exception as e:
          return {"error": f"Failed to set out-of-office: {e}"}
  ```

- [ ] **5.5** Add TOOLS dict entries:

  ```python
  "mark_read": {
      "description": "Mark one or more messages as read or unread",
      "inputSchema": {
          "type": "object",
          "properties": {
              "email": {"type": "string", "description": "Mailbox email address"},
              "message_id": {"type": "string", "description": "ID of a single message (optional)"},
              "filter": {
                  "type": "object",
                  "description": "Filter for bulk update (subject, sender, date_before, date_after)",
              },
              "is_read": {
                  "type": "boolean",
                  "description": "True = mark read, False = mark unread (default: true)",
                  "default": True,
              },
          },
          "required": ["email"],
      },
      "handler": tool_mark_read,
  },
  "flag_message": {
      "description": "Flag a message (flagged / complete / not_flagged)",
      "inputSchema": {
          "type": "object",
          "properties": {
              "email": {"type": "string", "description": "Mailbox email address"},
              "message_id": {"type": "string", "description": "ID of the message to flag"},
              "flag": {
                  "type": "string",
                  "enum": ["flagged", "complete", "not_flagged"],
                  "description": "Flag status (default: flagged)",
              },
          },
          "required": ["email", "message_id"],
      },
      "handler": tool_flag_message,
  },
  "get_out_of_office": {
      "description": "Get current out-of-office / automatic reply settings",
      "inputSchema": {
          "type": "object",
          "properties": {
              "email": {"type": "string", "description": "Mailbox email address"},
          },
          "required": ["email"],
      },
      "handler": tool_get_out_of_office,
  },
  "set_out_of_office": {
      "description": "Enable, disable, or schedule out-of-office automatic replies",
      "inputSchema": {
          "type": "object",
          "properties": {
              "email": {"type": "string", "description": "Mailbox email address"},
              "state": {
                  "type": "string",
                  "enum": ["Enabled", "Disabled", "Scheduled"],
                  "description": "OOF state",
              },
              "internal_reply": {"type": "string", "description": "Reply text for internal senders"},
              "external_reply": {"type": "string", "description": "Reply text for external senders"},
              "start": {"type": "string", "description": "Start datetime ISO 8601 (for Scheduled)"},
              "end": {"type": "string", "description": "End datetime ISO 8601 (for Scheduled)"},
          },
          "required": ["email", "state"],
      },
      "handler": tool_set_out_of_office,
  },
  ```

- [ ] **5.6** Test: get OOF status (should return Disabled), set to Scheduled with a future date, verify get returns the new state, then disable. Test mark_read on a known unread message.

- [ ] **5.7** Commit:
  ```
  feat(exchange-ews): add message management and out-of-office tools
  ```

---

## Task 6: Bulk Operations

**Agent:** `amplifier-core:modular-builder`

**Files:**
- Modify: `C:\claude\exchange-ews-mcp\server.py`

**Steps:**

- [ ] **6.1** Add shared `_build_filter(account, filter_params, source_folder=None)` helper. Translates a filter dict into exchangelib queryset:

  ```python
  def _build_filter(account, filter_params: dict, source_folder=None):
      """
      Build an exchangelib queryset from a filter dict.
      Supported keys: subject, sender, date_before, date_after.
      source_folder: folder name to search (default: inbox).
      Returns a queryset.
      """
      folder = source_folder or account.inbox
      if isinstance(source_folder, str):
          folder = _get_folder(account, source_folder)

      qs = folder.all()

      if filter_params.get("subject"):
          qs = qs.filter(subject__icontains=filter_params["subject"])
      if filter_params.get("sender"):
          qs = qs.filter(sender__icontains=filter_params["sender"])
      if filter_params.get("date_before"):
          dt = datetime.fromisoformat(filter_params["date_before"])
          qs = qs.filter(datetime_received__lte=dt)
      if filter_params.get("date_after"):
          dt = datetime.fromisoformat(filter_params["date_after"])
          qs = qs.filter(datetime_received__gte=dt)

      return qs
  ```

- [ ] **6.2** Add `tool_bulk_move()` with safety preview pattern:

  ```python
  def tool_bulk_move(params: dict) -> dict:
      email = params["email"]
      filter_params = params.get("filter", {})
      target_folder_name = params["target_folder"]
      confirm = params.get("confirm", False)
      source_folder = params.get("source_folder", None)
      account = get_account(email)

      qs = _build_filter(account, filter_params, source_folder)
      count = qs.count()

      if not confirm:
          return {
              "action": "bulk_move",
              "matching_count": count,
              "source_folder": source_folder or "Inbox",
              "target_folder": target_folder_name,
              "preview": True,
              "note": "Set confirm=true to execute the move",
          }

      # Find target folder
      try:
          target = _get_folder(account, target_folder_name)
      except ValueError:
          return {
              "error": (
                  f"Folder '{target_folder_name}' not found. "
                  f"Create it first with create_folder."
              )
          }

      qs.move(to_folder=target)
      return {"moved": count, "target_folder": target_folder_name}
  ```

- [ ] **6.3** Add `tool_bulk_delete()` with safety preview and batching for permanent deletes:

  ```python
  def tool_bulk_delete(params: dict) -> dict:
      email = params["email"]
      filter_params = params.get("filter", {})
      permanent = params.get("permanent", False)
      confirm = params.get("confirm", False)
      source_folder = params.get("source_folder", None)
      account = get_account(email)

      qs = _build_filter(account, filter_params, source_folder)
      count = qs.count()

      if not confirm:
          return {
              "action": "bulk_delete",
              "matching_count": count,
              "permanent": permanent,
              "preview": True,
              "note": "Set confirm=true to execute the delete",
          }

      if count == 0:
          return {"deleted": 0, "permanent": permanent}

      if permanent:
          # Batch to avoid timeout on large sets
          BATCH_SIZE = 100
          deleted = 0
          items = list(qs)
          for i in range(0, len(items), BATCH_SIZE):
              batch = items[i:i + BATCH_SIZE]
              for item in batch:
                  item.delete(delete_type="HardDelete")
              deleted += len(batch)
          return {"deleted": deleted, "permanent": True}
      else:
          qs.delete()
          return {"deleted": count, "permanent": False, "note": "Moved to Deleted Items"}
  ```

- [ ] **6.4** Add `tool_bulk_archive()`:

  ```python
  def tool_bulk_archive(params: dict) -> dict:
      email = params["email"]
      older_than_days = params["older_than_days"]
      target_folder_name = params.get("target_folder", "Archive")
      confirm = params.get("confirm", False)
      account = get_account(email)

      cutoff = datetime.now(timezone.utc) - timedelta(days=older_than_days)
      qs = account.inbox.filter(datetime_received__lte=cutoff)
      count = qs.count()

      if not confirm:
          return {
              "action": "bulk_archive",
              "matching_count": count,
              "older_than_days": older_than_days,
              "target_folder": target_folder_name,
              "cutoff_date": cutoff.isoformat(),
              "preview": True,
              "note": "Set confirm=true to execute the archive",
          }

      if count == 0:
          return {"archived": 0, "target_folder": target_folder_name}

      try:
          target = _get_folder(account, target_folder_name)
      except ValueError:
          return {
              "error": (
                  f"Folder '{target_folder_name}' not found. "
                  f"Create it first with create_folder."
              )
          }

      qs.move(to_folder=target)
      return {"archived": count, "target_folder": target_folder_name, "cutoff_date": cutoff.isoformat()}
  ```

- [ ] **6.5** Add TOOLS dict entries:

  ```python
  "bulk_move": {
      "description": "Move matching messages to a target folder. Returns preview count without confirm=true.",
      "inputSchema": {
          "type": "object",
          "properties": {
              "email": {"type": "string", "description": "Mailbox email address"},
              "filter": {
                  "type": "object",
                  "description": "Filter: subject (contains), sender (contains), date_before, date_after (ISO 8601)",
              },
              "target_folder": {"type": "string", "description": "Destination folder name"},
              "source_folder": {"type": "string", "description": "Source folder name (default: Inbox)"},
              "confirm": {
                  "type": "boolean",
                  "description": "Set true to execute move (default: false returns preview only)",
                  "default": False,
              },
          },
          "required": ["email", "filter", "target_folder"],
      },
      "handler": tool_bulk_move,
  },
  "bulk_delete": {
      "description": "Delete matching messages. Returns preview count without confirm=true. Use permanent=true for hard delete.",
      "inputSchema": {
          "type": "object",
          "properties": {
              "email": {"type": "string", "description": "Mailbox email address"},
              "filter": {
                  "type": "object",
                  "description": "Filter: subject (contains), sender (contains), date_before, date_after (ISO 8601)",
              },
              "permanent": {
                  "type": "boolean",
                  "description": "Hard delete (default: false = move to Deleted Items)",
                  "default": False,
              },
              "source_folder": {"type": "string", "description": "Source folder name (default: Inbox)"},
              "confirm": {
                  "type": "boolean",
                  "description": "Set true to execute delete (default: false returns preview only)",
                  "default": False,
              },
          },
          "required": ["email", "filter"],
      },
      "handler": tool_bulk_delete,
  },
  "bulk_archive": {
      "description": "Archive messages older than N days to Archive folder. Returns preview without confirm=true.",
      "inputSchema": {
          "type": "object",
          "properties": {
              "email": {"type": "string", "description": "Mailbox email address"},
              "older_than_days": {"type": "integer", "description": "Archive messages older than this many days"},
              "target_folder": {
                  "type": "string",
                  "description": "Destination folder name (default: Archive)",
                  "default": "Archive",
              },
              "confirm": {
                  "type": "boolean",
                  "description": "Set true to execute archive (default: false returns preview only)",
                  "default": False,
              },
          },
          "required": ["email", "older_than_days"],
      },
      "handler": tool_bulk_archive,
  },
  ```

- [ ] **6.6** Test: run bulk_move without confirm — verify preview count returned, no move executed. Run with confirm=true — verify messages moved. Test bulk_delete soft delete. Test bulk_archive with 1-day cutoff.

- [ ] **6.7** Commit:
  ```
  feat(exchange-ews): add bulk operations with safety preview
  ```

---

## Task 7: Existing Tool Fixes

**Agent:** `amplifier-core:modular-builder`

**Files:**
- Modify: `C:\claude\exchange-ews-mcp\server.py`

**Steps:**

- [ ] **7.1** Add `_validate_email(email: str) -> None` helper. Call at the top of EVERY tool function (can be added systematically with a helper call, not re-typed 29 times):

  ```python
  _EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")

  def _validate_email(email: str) -> None:
      """Raise ValueError if email doesn't look valid."""
      if not _EMAIL_RE.match(email):
          raise ValueError(f"Invalid email address: '{email}'")
  ```

  Add `_validate_email(email)` as the second line (after `email = params["email"]`) in every existing and new tool function.

- [ ] **7.2** Fix `tool_search()` — add optional `folder` param. When omitted, search across all folders and collect results:

  ```python
  # Inside tool_search(), after getting account:
  folder_name = params.get("folder")
  if folder_name:
      folders_to_search = [_get_folder(account, folder_name)]
  else:
      folders_to_search = list(account.root.walk())

  all_results = []
  for folder in folders_to_search:
      try:
          qs = folder.filter(subject__icontains=query)
          # ... existing result-building logic ...
          all_results.extend(results)
      except Exception:
          continue
  ```

  Update the TOOLS dict `search` entry to add the `folder` property:
  ```python
  "folder": {
      "type": "string",
      "description": "Folder name to search (optional — searches all folders if omitted)"
  }
  ```

- [ ] **7.3** Fix `tool_move_message()` — replace `account.inbox.get(id=message_id)` with `_find_message(account, message_id)`. No schema change needed.

- [ ] **7.4** Fix `tool_get_mailbox_size()` — replace the item iteration loop with folder property access. exchangelib's `Folder` exposes `total_count` and `total_size` without fetching items:

  ```python
  # Replace the iteration loop with:
  total_size = 0
  folder_stats = []
  for folder in account.root.walk():
      try:
          size = folder.total_size or 0
          count = folder.total_count or 0
          if count > 0:
              folder_stats.append({
                  "name": folder.name,
                  "item_count": count,
                  "size_bytes": size,
              })
          total_size += size
      except Exception:
          continue

  return {
      "total_size_bytes": total_size,
      "total_size_mb": round(total_size / (1024 * 1024), 2),
      "folders": folder_stats,
  }
  ```

- [ ] **7.5** Fix `verify_*` tools — replace all hardcoded `time.sleep()` calls with configurable polling. Replace every `time.sleep(N)` with:

  ```python
  cfg = get_config()
  poll_interval = cfg.get("poll_interval", 3)
  time.sleep(poll_interval)
  ```

  Replace loop-based sleeps with loops that use `poll_interval`. Remove any fixed 10s/15s/5s waits.

- [ ] **7.6** Verify all 13 existing tools still pass end-to-end in the lab environment. Run each tool and confirm output matches pre-fix behavior.

- [ ] **7.7** Commit:
  ```
  fix(exchange-ews): search all folders, faster mailbox size, configurable polling
  ```

---

## Task 8: Project Modernization

**Agent:** `amplifier-core:modular-builder`

**Files:**
- Create: `C:\claude\exchange-ews-mcp\pyproject.toml`
- Modify: `C:\claude\exchange-ews-mcp\README.md` (full rewrite)
- Modify: `C:\claude\exchange-ews-mcp\config.example.json` (final update — may already be done in Task 1)

**Steps:**

- [ ] **8.1** Create `pyproject.toml`:

  ```toml
  [project]
  name = "exchange-ews-mcp"
  version = "2.0.0"
  description = "Exchange EWS MCP Server — mailbox operations for Claude Code and Claude Desktop"
  requires-python = ">=3.11"
  dependencies = [
      "exchangelib>=5.0",
  ]

  [project.optional-dependencies]
  kerberos = ["requests-kerberos>=0.14"]

  [build-system]
  requires = ["hatchling"]
  build-backend = "hatchling.build"

  [tool.uv]
  dev-dependencies = []
  ```

- [ ] **8.2** Rewrite `README.md` with:

  **Sections to include:**

  1. **Header**: "Exchange EWS MCP — Production-Ready Mailbox Operations for Claude"
  2. **Architecture**: "Single-file stdio MCP server. Multi-auth (NTLM / Basic / Kerberos / Auto). SSL verification configurable. exchangelib backend."
  3. **Installation** (using uv):
     ```bash
     git clone <repo> && cd exchange-ews-mcp
     uv sync                      # base deps
     uv sync --extra kerberos     # add Kerberos support
     ```
  4. **Configuration** — two full examples (Production NTLM + Lab Kerberos) with every field documented.
  5. **Claude Desktop Registration**:
     ```json
     {
       "mcpServers": {
         "exchange-ews": {
           "command": "uv",
           "args": ["run", "--project", "/path/to/exchange-ews-mcp", "python", "server.py"],
           "env": {}
         }
       }
     }
     ```
  6. **Claude Code Registration**:
     ```bash
     claude mcp add exchange-ews -- uv run --project /path/to/exchange-ews-mcp python server.py
     ```
  7. **All 29 Tools** — table with columns: Tool | Description | Key Params:

     | Tool | Description | Key Params |
     |------|-------------|------------|
     | `inbox` | List inbox messages | email, limit |
     | `read_message` | Read a message | email, message_id |
     | `send_message` | Send email | email, to, subject, body |
     | `search` | Search messages | email, query, folder (opt) |
     | `move_message` | Move a message | email, message_id, target_folder |
     | `delete_message` | Delete a message | email, message_id |
     | `folders` | List all folders | email |
     | `calendar_read` | Read calendar events | email, days_ahead |
     | `calendar_create` | Create calendar event | email, subject, start, end |
     | `get_mailbox_size` | Mailbox size by folder | email |
     | `mail_flow_test` | Send and verify delivery | email, test_address |
     | `verify_forwarding` | Check forwarding config | email, expected_target |
     | `verify_auto_reply` | Check OOF/auto-reply | email |
     | `reply` | Reply to message | email, message_id, body, reply_all |
     | `forward` | Forward message | email, message_id, to, body |
     | `get_thread` | Full conversation thread | email, message_id |
     | `download_attachment` | Get attachment as base64 | email, message_id, attachment_name |
     | `create_draft` | Create draft | email, to, subject, body |
     | `list_drafts` | List drafts | email, limit |
     | `send_draft` | Send existing draft | email, draft_id |
     | `create_folder` | Create folder | email, name, parent_folder |
     | `delete_folder` | Delete folder | email, folder_name, force |
     | `rename_folder` | Rename folder | email, folder_name, new_name |
     | `mark_read` | Mark read/unread | email, message_id or filter |
     | `flag_message` | Flag a message | email, message_id, flag |
     | `get_out_of_office` | Get OOF settings | email |
     | `set_out_of_office` | Set OOF settings | email, state |
     | `bulk_move` | Move matching messages | email, filter, target_folder, confirm |
     | `bulk_delete` | Delete matching messages | email, filter, permanent, confirm |
     | `bulk_archive` | Archive by age | email, older_than_days, confirm |

  8. **Bulk Operations Safety** — one paragraph explaining the preview/confirm pattern and why it exists.
  9. **Security Model** — credentials in config file only, file permissions, no env var leakage.
  10. **Backward Compatibility** — the two-line lab config change.

- [ ] **8.3** Run `cd C:\claude\exchange-ews-mcp && uv sync` — confirm no errors. Verify `uv run python server.py` starts without import errors (will wait for stdin — Ctrl+C to exit).

- [ ] **8.4** Confirm `config.example.json` has all fields (should be done in Task 1 step 1.5; verify it matches):

  ```json
  {
    "_comment_server": "Exchange server hostname or IP",
    "server": "mail.example.com",
    "_comment_auth": "Auth type: auto (default), ntlm, basic, kerberos",
    "auth_type": "auto",
    "_comment_creds": "Required for ntlm/basic/auto. Omit for kerberos.",
    "username": "DOMAIN\\your.username",
    "password": "your-password",
    "_comment_ssl": "Set false for self-signed certs (lab use only)",
    "verify_ssl": true,
    "_comment_scope": "Optional OU scope for documentation/logging. Null = unrestricted.",
    "scope_ou": null,
    "_comment_poll": "Polling interval in seconds for verify_* tools (default: 3)",
    "poll_interval": 3
  }
  ```

- [ ] **8.5** Commit:
  ```
  chore(exchange-ews): add pyproject.toml, rewrite README for v2.0
  ```

---

## Requirement → Task Coverage Matrix

```
Requirement → Task Mapping:
  ✓ Auth refactor (NTLM/Basic/Kerberos/Auto) → Task 1
  ✓ SSL configurable → Task 1
  ✓ Scope optional → Task 1
  ✓ reply tool → Task 3
  ✓ forward tool → Task 3
  ✓ get_thread tool → Task 3
  ✓ download_attachment tool → Task 4
  ✓ create_draft tool → Task 4
  ✓ send_draft tool → Task 4
  ✓ list_drafts tool → Task 4
  ✓ create_folder tool → Task 2
  ✓ delete_folder tool → Task 2
  ✓ rename_folder tool → Task 2
  ✓ mark_read tool → Task 5
  ✓ flag_message tool → Task 5
  ✓ get_out_of_office tool → Task 5
  ✓ set_out_of_office tool → Task 5
  ✓ bulk_move tool → Task 6
  ✓ bulk_delete tool → Task 6
  ✓ bulk_archive tool → Task 6
  ✓ search all-folders fix → Task 7
  ✓ move_message all-folders fix → Task 7
  ✓ get_mailbox_size performance fix → Task 7
  ✓ verify_* sleep fix → Task 7
  ✓ Email validation → Task 7
  ✓ pyproject.toml → Task 8
  ✓ README rewrite → Task 8
  ✓ config.example.json update → Task 8
  ✓ Lab backward compatibility → Task 1 (verified in test step)
```
