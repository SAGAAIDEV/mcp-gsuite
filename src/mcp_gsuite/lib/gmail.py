from googleapiclient.discovery import build
from .auth import credentials as cred_module

# import logging # Removed, as we use the custom logger
import base64
import traceback
from email.mime.text import MIMEText
from typing import Tuple
from saaga_mcp_base.lib.logging import logger  # Use this logger


class GmailService:
    def __init__(self, user_id: str):
        creds_obj = cred_module.get_stored_credentials(user_email=user_id)
        if not creds_obj:
            # Log before raising an error if it helps in debugging.
            # logger.error(f"No Oauth2 credentials stored for user_id: {user_id}") # Optional based on needs
            raise RuntimeError(f"No Oauth2 credentials stored for user_id: {user_id}")
        self.service = build("gmail", "v1", credentials=creds_obj)
        self.user_id = user_id  # Store user_id for logging purposes

    def _parse_message(self, txt, parse_body=False) -> dict | None:
        """
        Parse a Gmail message into a structured format.

        Args:
            txt (dict): Raw message from Gmail API
            parse_body (bool): Whether to parse and include the message body (default: False)

        Returns:
            dict: Parsed message containing comprehensive metadata
            None: If parsing fails
        """
        try:
            message_id = txt.get("id")
            thread_id = txt.get("threadId")
            payload = txt.get("payload", {})
            headers = payload.get("headers", [])

            metadata = {
                "id": message_id,
                "threadId": thread_id,
                "historyId": txt.get("historyId"),
                "internalDate": txt.get("internalDate"),
                "sizeEstimate": txt.get("sizeEstimate"),
                "labelIds": txt.get("labelIds", []),
                "snippet": txt.get("snippet"),
            }

            for header in headers:
                name = header.get("name", "").lower()
                value = header.get("value", "")

                if name == "subject":
                    metadata["subject"] = value
                elif name == "from":
                    metadata["from"] = value
                elif name == "to":
                    metadata["to"] = value
                elif name == "date":
                    metadata["date"] = value
                elif name == "cc":
                    metadata["cc"] = value
                elif name == "bcc":
                    metadata["bcc"] = value
                elif name == "message-id":
                    metadata["message_id"] = value
                elif name == "in-reply-to":
                    metadata["in_reply_to"] = value
                elif name == "references":
                    metadata["references"] = value
                elif name == "delivered-to":
                    metadata["delivered_to"] = value

            if parse_body:
                body = self._extract_body(payload)
                if body:
                    metadata["body"] = body

                metadata["mimeType"] = payload.get("mimeType")

            return metadata

        except Exception as e:
            logger.error(f"Error parsing message for user_id {self.user_id}: {str(e)}")
            logger.error(traceback.format_exc())
            return None

    def _extract_body(self, payload) -> str | None:
        """
        Extract the email body from the payload.
        Handles both multipart and single part messages, including nested multiparts.
        """
        try:
            # For single part text/plain messages
            if payload.get("mimeType") == "text/plain":
                data = payload.get("body", {}).get("data")
                if data:
                    return base64.urlsafe_b64decode(data).decode("utf-8")

            # For multipart messages (both alternative and related)
            if payload.get("mimeType", "").startswith("multipart/"):
                parts = payload.get("parts", [])

                # First try to find a direct text/plain part
                for part in parts:
                    if part.get("mimeType") == "text/plain":
                        data = part.get("body", {}).get("data")
                        if data:
                            return base64.urlsafe_b64decode(data).decode("utf-8")

                # If no direct text/plain, recursively check nested multipart structures
                for part in parts:
                    if part.get("mimeType", "").startswith("multipart/"):
                        nested_body = self._extract_body(part)
                        if nested_body:
                            return nested_body

                # If still no body found, try the first part as fallback
                if parts and "body" in parts[0] and "data" in parts[0]["body"]:
                    data = parts[0]["body"]["data"]
                    return base64.urlsafe_b64decode(data).decode("utf-8")

            return None

        except Exception as e:
            logger.error(f"Error extracting body for user_id {self.user_id}: {str(e)}")
            return None

    def query_emails(self, query=None, max_results=100):
        """
        Query emails from Gmail based on a search query.

        Args:
            query (str, optional): Gmail search query (e.g., 'is:unread', 'from:example@gmail.com')
                                If None, returns all emails
            max_results (int): Maximum number of emails to retrieve (1-500, default: 100)

        Returns:
            list: List of parsed email messages, newest first
        """
        try:
            # Ensure max_results is within API limits
            max_results = min(max(1, max_results), 500)

            # Get the list of messages
            result = (
                self.service.users()
                .messages()
                .list(userId="me", maxResults=max_results, q=query if query else "")
                .execute()
            )

            messages = result.get("messages", [])
            parsed = []

            # Fetch full message details for each message
            for msg in messages:
                txt = (
                    self.service.users()
                    .messages()
                    .get(userId="me", id=msg["id"])
                    .execute()
                )
                parsed_message = self._parse_message(txt=txt, parse_body=False)
                if parsed_message:
                    parsed.append(parsed_message)

            return parsed

        except Exception as e:
            logger.error(
                f"Error querying emails for user_id: {self.user_id}, query: '{query}'. Error: {str(e)}"
            )
            logger.error(traceback.format_exc())
            return []

    def get_email_by_id(
        self, email_id: str, with_attachments: bool = False
    ) -> Tuple[dict | None, dict]:
        """
        Fetch and parse a complete email message by its ID.
        Optionally includes attachment details.

        Args:
            email_id (str): The Gmail message ID to retrieve.
            with_attachments (bool): Whether to fetch and include attachment details (default: False).

        Returns:
            Tuple[dict | None, dict]: Parsed email message (or None if error) and a dictionary of attachment details.
                                     The attachment dictionary will be empty if with_attachments is False or no attachments exist.
        """
        try:
            # Fetch the complete message by ID
            message = (
                self.service.users().messages().get(userId="me", id=email_id).execute()
            )

            # Parse the message with body included
            parsed_email = self._parse_message(txt=message, parse_body=True)

            if parsed_email is None:
                return None, {}  # Error already logged in _parse_message

            attachments = {}
            if (
                with_attachments
                and message.get("payload")
                and message["payload"].get("parts")
            ):
                for part in message["payload"]["parts"]:
                    if "attachmentId" in part.get("body", {}):
                        attachment_id = part["body"]["attachmentId"]
                        part_id = part.get("partId")
                        attachment = {
                            "filename": part.get("filename"),
                            "mimeType": part.get("mimeType"),
                            "attachmentId": attachment_id,
                            "partId": part_id,
                        }
                        attachments[part_id] = attachment

            return parsed_email, attachments

        except Exception as e:
            logger.error(
                f"Error retrieving email {email_id} for user_id {self.user_id}: {str(e)}"
            )
            logger.error(traceback.format_exc())
            return None, {}

    def create_draft(
        self, to: str, subject: str, body: str, cc: list[str] | None = None
    ) -> dict | None:
        """
        Create a draft email message.

        Args:
            to (str): Email address of the recipient
            subject (str): Subject line of the email
            body (str): Body content of the email
            cc (list[str], optional): List of email addresses to CC

        Returns:
            dict: Draft message data including the draft ID if successful
            None: If creation fails
        """
        try:
            # Create message body
            message_payload = {
                "to": to,
                "subject": subject,
                "text": body,
            }
            if cc:
                message_payload["cc"] = ",".join(cc)

            # Create the message in MIME format
            mime_message = MIMEText(body)
            mime_message["to"] = to
            mime_message["subject"] = subject
            if cc:
                mime_message["cc"] = ",".join(cc)

            # Encode the message
            raw_message = base64.urlsafe_b64encode(mime_message.as_bytes()).decode(
                "utf-8"
            )

            # Create the draft
            draft = (
                self.service.users()
                .drafts()
                .create(userId="me", body={"message": {"raw": raw_message}})
                .execute()
            )

            return draft

        except Exception as e:
            logger.error(
                f"Error creating draft for user_id: {self.user_id}. Error: {str(e)}"
            )
            logger.error(traceback.format_exc())
            return None

    def delete_draft(self, draft_id: str) -> bool:
        """
        Delete a draft email message.

        Args:
            draft_id (str): The ID of the draft to delete

        Returns:
            bool: True if deletion was successful, False otherwise
        """
        try:
            self.service.users().drafts().delete(userId="me", id=draft_id).execute()
            return True

        except Exception as e:
            logger.error(
                f"Error deleting draft {draft_id} for user_id {self.user_id}: {str(e)}"
            )
            logger.error(traceback.format_exc())
            return False

    def create_reply(
        self,
        original_message_id: str,
        reply_body: str,
        send: bool = False,
        cc: list[str] | None = None,
    ) -> dict | None:
        """
        Create a reply to an email message and either send it or save as draft.

        Args:
            original_message_id (str): The ID of the original message to reply to.
            reply_body (str): Body content of the reply
            send (bool): If True, sends the reply immediately. If False, saves as draft.
            cc (list[str], optional): List of email addresses to CC

        Returns:
            dict: Sent message or draft data if successful
            None: If operation fails
        """
        try:
            # Fetch the original message details using its ID
            original_message, _ = self.get_email_by_id(
                email_id=original_message_id, with_attachments=False
            )

            if not original_message:
                logger.error(
                    f"Could not retrieve original message {original_message_id} to create reply for user_id {self.user_id}"
                )
                return None

            to_address = original_message.get("from")
            if not to_address:
                logger.warning(
                    f"Could not determine original sender's address for user_id {self.user_id} from message: {original_message.get('id')}"
                )
                raise ValueError("Could not determine original sender's address")

            subject = original_message.get("subject", "")
            if not subject.lower().startswith("re:"):
                subject = f"Re: {subject}"

            original_date = original_message.get("date", "")
            original_from = original_message.get("from", "")
            original_body = original_message.get("body", "")

            full_reply_body = (
                f"{reply_body}\n\n"
                f"On {original_date}, {original_from} wrote:\n"
                f"> {original_body.replace('\n', '\n> ') if original_body else '[No message body]'}"
            )

            mime_message = MIMEText(full_reply_body)
            mime_message["to"] = to_address
            mime_message["subject"] = subject
            if cc:
                mime_message["cc"] = ",".join(cc)

            mime_message["In-Reply-To"] = original_message.get(
                "message_id"
            )  # Use message_id header
            mime_message["References"] = original_message.get(
                "message_id"
            )  # Use message_id header

            # Ensure threadId is used for replies
            thread_id = original_message.get("threadId")
            if not thread_id:
                logger.warning(
                    f"Missing threadId for reply for user_id {self.user_id}, message: {original_message.get('id')}"
                )

            raw_message = base64.urlsafe_b64encode(mime_message.as_bytes()).decode(
                "utf-8"
            )

            message_body = {
                "raw": raw_message,
                "threadId": thread_id,
            }

            if send:
                # Send the reply immediately
                result = (
                    self.service.users()
                    .messages()
                    .send(userId="me", body=message_body)
                    .execute()
                )
            else:
                # Save as draft
                result = (
                    self.service.users()
                    .drafts()
                    .create(userId="me", body={"message": message_body})
                    .execute()
                )

            return result

        except Exception as e:
            logger.error(
                f"Error {'sending' if send else 'drafting'} reply for user_id {self.user_id}: {str(e)}"
            )
            logger.error(traceback.format_exc())
            return None

    def get_attachment(self, message_id: str, attachment_id: str) -> dict | None:
        """
        Retrieves a Gmail attachment by its ID.

        Args:
            message_id (str): The ID of the Gmail message containing the attachment
            attachment_id (str): The ID of the attachment to retrieve

        Returns:
            dict: Attachment data including filename and base64-encoded content
            None: If retrieval fails
        """
        try:
            attachment = (
                self.service.users()
                .messages()
                .attachments()
                .get(userId="me", messageId=message_id, id=attachment_id)
                .execute()
            )
            return {"size": attachment.get("size"), "data": attachment.get("data")}

        except Exception as e:
            logger.error(
                f"Error retrieving attachment {attachment_id} from message {message_id} for user_id {self.user_id}: {str(e)}"
            )
            logger.error(traceback.format_exc())
            return None

    def create_label(
        self,
        label_name: str,
        label_list_visibility: str = "labelShow",
        message_list_visibility: str = "show",
    ) -> dict | None:
        """
        Create a new label in Gmail.

        Args:
            label_name (str): The name of the new label.
            label_list_visibility (str): Visibility of the label in the label list (e.g., "labelShow", "labelHide").
            message_list_visibility (str): Visibility of messages with this label (e.g., "show", "hide").

        Returns:
            dict: The created label object if successful.
            None: If creation fails.
        """
        try:
            label_object = {
                "name": label_name,
                "labelListVisibility": label_list_visibility,
                "messageListVisibility": message_list_visibility,
            }
            created_label = (
                self.service.users()
                .labels()
                .create(userId="me", body=label_object)
                .execute()
            )
            return created_label
        except Exception as e:
            logger.error(
                f"Error creating label '{label_name}' for user_id {self.user_id}: {str(e)}"
            )
            logger.error(traceback.format_exc())
            return None

    def set_email_labels(
        self,
        message_id: str,
        label_ids_to_add: list[str] | None = None,
        label_ids_to_remove: list[str] | None = None,
    ) -> dict | None:
        """
        Add or remove labels from an email message.

        Args:
            message_id (str): The ID of the message to modify.
            label_ids_to_add (list[str], optional): List of label IDs to add.
            label_ids_to_remove (list[str], optional): List of label IDs to remove.

        Returns:
            dict: The updated message resource if successful.
            None: If modification fails.
        """
        try:
            modify_request = {}
            if label_ids_to_add:
                modify_request["addLabelIds"] = label_ids_to_add
            if label_ids_to_remove:
                modify_request["removeLabelIds"] = label_ids_to_remove

            if not modify_request:
                logger.info(
                    f"No labels to add or remove for message {message_id} for user_id {self.user_id}."
                )
                # Potentially return the current message state or a specific status
                return (
                    self.service.users()
                    .messages()
                    .get(userId="me", id=message_id)
                    .execute()
                )

            updated_message = (
                self.service.users()
                .messages()
                .modify(userId="me", id=message_id, body=modify_request)
                .execute()
            )
            return updated_message
        except Exception as e:
            logger.error(
                f"Error setting labels for message {message_id} for user_id {self.user_id}: {str(e)}"
            )
            logger.error(traceback.format_exc())
            return None
