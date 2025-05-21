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

    def get_email_by_id_with_attachments(
        self, email_id: str
    ) -> Tuple[dict | None, dict]:
        """Fetch and parse a complete email message by its ID, ensuring attachments are included."""
        return self.get_email_by_id(email_id, with_attachments=True)

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

    def update_draft(
        self,
        draft_id: str,
        to: str | None = None,
        subject: str | None = None,
        body: str | None = None,
        cc: list[str] | None = None,
    ) -> dict | None:
        """
        Update an existing draft email message.
        Only provided fields will be updated.

        Args:
            draft_id (str): The ID of the draft to update.
            to (str, optional): New email address of the recipient.
            subject (str, optional): New subject line of the email.
            body (str, optional): New body content of the email.
            cc (list[str], optional): New list of email addresses to CC.

        Returns:
            dict: Updated draft message data if successful.
            None: If update fails.
        """
        try:
            # Get the current draft message to preserve existing fields if not updated
            # We need 'format': 'full' to get enough details to reconstruct,
            # or 'metadata' if we only update specific headers and body.
            # For simplicity and robustness, let's fetch minimal data and reconstruct.
            # However, the Gmail API's draft.update expects a full message resource.
            # It's often easier to create a new MIME message with the *new* desired state.

            # Fetch the existing draft details to get its current state, specifically threadId
            existing_draft_metadata = (
                self.service.users().drafts().get(userId="me", id=draft_id).execute()
            )
            if not existing_draft_metadata or "message" not in existing_draft_metadata:
                logger.error(
                    f"Could not retrieve existing draft {draft_id} for update for user_id {self.user_id}"
                )
                return None

            # Get the original message ID and thread ID for context if needed, though draft update usually handles this.
            original_message_id = existing_draft_metadata["message"].get(
                "id"
            )  # This is message ID, not draft ID
            thread_id = existing_draft_metadata["message"].get("threadId")

            # To update a draft, you typically provide the *new* complete message content.
            # We need to know what the current 'to', 'subject', 'body', 'cc' are
            # if we want to only update some of them.
            # The API for draft update replaces the entire message part of the draft.
            # So, if 'to' is not provided, the existing 'to' will be wiped unless we fetch it first.

            # Fetch the full message of the draft to get all current parts
            # This is resource intensive if only small changes are made.
            # A more optimized way might involve more complex MIME manipulation,
            # but for now, we'll re-create the message based on old + new.

            # Simpler approach: Assume we always provide all necessary fields or rebuild from scratch.
            # For now, let's assume the update provides all necessary components or it's a fresh message.
            # If only some fields are provided, the others will be blanked out unless fetched and re-added.
            # Let's require all fields or make them fall back to current draft's values if not provided.

            # To properly update, we should fetch the full existing message if fields are optional.
            # Let's fetch the raw message from the draft to be safe, then modify it.
            # This is not straightforward with MIME parsing and rebuilding.

            # Alternative: Gmail API draft.update replaces the draft's message with the one provided.
            # So, we need to construct the *entire new* message.
            # If 'to' is not given, what should it be? We need the old 'to'.
            # This means we DO need to fetch the existing full message.

            current_message_details = (
                self.service.users()
                .messages()
                .get(userId="me", id=original_message_id, format="full")
                .execute()
            )
            parsed_current_message = self._parse_message(
                current_message_details, parse_body=True
            )

            if not parsed_current_message:
                logger.error(
                    f"Could not parse current message {original_message_id} of draft {draft_id} for update."
                )
                return None

            updated_to = to if to is not None else parsed_current_message.get("to")
            updated_subject = (
                subject
                if subject is not None
                else parsed_current_message.get("subject")
            )
            updated_body = (
                body if body is not None else parsed_current_message.get("body")
            )

            # CC needs careful handling: if cc is an empty list, it should clear CC.
            # If cc is None, it means "don't change CC".
            updated_cc_list = None
            if cc is not None:  # If cc is provided (even if empty list)
                updated_cc_list = cc
            elif "cc" in parsed_current_message:  # if cc not provided, use existing
                updated_cc_list = (
                    parsed_current_message.get("cc").split(",")
                    if isinstance(parsed_current_message.get("cc"), str)
                    else parsed_current_message.get("cc")
                )

            if not updated_to:  # 'To' field is generally required
                logger.error(
                    f"Recipient ('to') field is missing for updating draft {draft_id}."
                )
                return None

            mime_message = MIMEText(updated_body or "")  # Body can be empty
            mime_message["to"] = updated_to
            mime_message["subject"] = updated_subject or ""  # Subject can be empty

            if updated_cc_list:
                mime_message["cc"] = ",".join(updated_cc_list)

            # Preserve In-Reply-To and References if they exist, for replies/forwards
            if parsed_current_message.get("in_reply_to"):
                mime_message["In-Reply-To"] = parsed_current_message.get("in_reply_to")
            if parsed_current_message.get("references"):
                mime_message["References"] = parsed_current_message.get("references")

            raw_message = base64.urlsafe_b64encode(mime_message.as_bytes()).decode(
                "utf-8"
            )

            updated_draft_body = {"message": {"raw": raw_message}}
            # If the original draft was part of a thread, ensure the updated draft stays in it.
            if thread_id:
                updated_draft_body["message"]["threadId"] = thread_id

            draft = (
                self.service.users()
                .drafts()
                .update(userId="me", id=draft_id, body=updated_draft_body)
                .execute()
            )
            return draft

        except Exception as e:
            logger.error(
                f"Error updating draft {draft_id} for user_id {self.user_id}. Error: {str(e)}"
            )
            logger.error(traceback.format_exc())
            return None

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
        label_names_to_add: list[str] | None = None,
        label_names_to_remove: list[str] | None = None,
    ) -> dict | None:
        """
        Add or remove labels from an email message using their names.

        Args:
            message_id (str): The ID of the message to modify.
            label_names_to_add (list[str], optional): List of label names to add.
            label_names_to_remove (list[str], optional): List of label names to remove.

        Returns:
            dict: The updated message resource if successful.
            None: If modification fails or label names cannot be resolved.
        """
        try:
            resolved_label_ids_to_add = []
            resolved_label_ids_to_remove = []

            if label_names_to_add or label_names_to_remove:
                all_user_labels = self.list_labels()  # Calls the method added earlier
                if all_user_labels is None:
                    logger.error(
                        f"Could not list labels for user {self.user_id} to map names to IDs in set_email_labels."
                    )
                    return None  # Indicate failure to resolve/list labels

                label_name_to_id_map = {
                    label["name"].upper(): label["id"] for label in all_user_labels
                }
                logger.debug(
                    f"Available labels for user {self.user_id} for mapping: {label_name_to_id_map}"
                )

                if label_names_to_add:
                    for name in label_names_to_add:
                        uid = label_name_to_id_map.get(name.upper())
                        if uid:
                            resolved_label_ids_to_add.append(uid)
                        else:
                            logger.warning(
                                f"Label name '{name}' not found for user {self.user_id}. Ignoring for addition."
                            )

                if label_names_to_remove:
                    for name in label_names_to_remove:
                        uid = label_name_to_id_map.get(name.upper())
                        if uid:
                            resolved_label_ids_to_remove.append(uid)
                        else:
                            logger.warning(
                                f"Label name '{name}' not found for user {self.user_id}. Ignoring for removal."
                            )

            # Remove duplicates that might arise if a name was already an ID-like string by chance
            # or if names were repeated.
            resolved_label_ids_to_add = list(set(resolved_label_ids_to_add))
            resolved_label_ids_to_remove = list(set(resolved_label_ids_to_remove))

            modify_request = {}
            if resolved_label_ids_to_add:
                modify_request["addLabelIds"] = resolved_label_ids_to_add
            if resolved_label_ids_to_remove:
                modify_request["removeLabelIds"] = resolved_label_ids_to_remove

            if not modify_request:
                logger.info(
                    f"No valid labels to add or remove for message {message_id} for user_id {self.user_id} after name resolution."
                )
                # Return current message state if no actual changes are to be made
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
            logger.info(
                f"Successfully modified labels for message {message_id} for user {self.user_id} using names. Added: {resolved_label_ids_to_add}, Removed: {resolved_label_ids_to_remove}"
            )
            return updated_message
        except Exception as e:
            logger.error(
                f"Error setting labels by name for message {message_id} for user_id {self.user_id}: {str(e)}"
            )
            logger.error(traceback.format_exc())
            return None

    def send_draft(self, draft_id: str) -> dict | None:
        """
        Sends a previously created draft email.

        Args:
            draft_id (str): The ID of the draft to send.

        Returns:
            dict: The sent message data if successful.
            None: If sending fails.
        """
        try:
            # Get the message from the draft
            draft_message = (
                self.service.users()
                .drafts()
                .get(userId="me", id=draft_id, format="raw")
                .execute()
            )

            # The raw message content is in the 'raw' field
            raw_message = draft_message["message"]["raw"]

            # Send the message
            sent_message = (
                self.service.users()
                .messages()
                .send(userId="me", body={"raw": raw_message})
                .execute()
            )

            # Optionally, delete the draft after sending
            # self.delete_draft(draft_id) # Uncomment if you want to delete the draft automatically after sending

            return sent_message

        except Exception as e:
            logger.error(
                f"Error sending draft {draft_id} for user_id {self.user_id}: {str(e)}"
            )
            logger.error(traceback.format_exc())
            return None

    def list_labels(self) -> list[dict] | None:
        """
        List all labels for the user.

        Returns:
            list[dict]: A list of label resources (dictionaries), each containing id, name, etc.
            None: If listing fails.
        """
        try:
            results = self.service.users().labels().list(userId="me").execute()
            labels = results.get("labels", [])
            return labels
        except Exception as e:
            logger.error(f"Error listing labels for user_id {self.user_id}: {str(e)}")
            logger.error(traceback.format_exc())
            return None
