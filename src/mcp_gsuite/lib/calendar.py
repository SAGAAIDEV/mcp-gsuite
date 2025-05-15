from googleapiclient.discovery import build
from .auth import credentials as cred_module
import logging
import traceback
from datetime import datetime
import pytz


class CalendarService:
    def __init__(self, user_id: str):
        creds_obj = cred_module.get_stored_credentials(user_email=user_id)
        if not creds_obj:
            raise RuntimeError("No Oauth2 credentials stored")
        self.service = build(
            "calendar", "v3", credentials=creds_obj
        )  # Note: using v3 for Calendar API

    def list_calendars(self) -> list:
        """
        Lists all calendars accessible by the user.

        Returns:
            list: List of calendar objects with their metadata
        """
        try:
            calendar_list = self.service.calendarList().list().execute()

            calendars = []

            for calendar in calendar_list.get("items", []):
                if calendar.get("kind") == "calendar#calendarListEntry":
                    calendars.append(
                        {
                            "id": calendar.get("id"),
                            "summary": calendar.get("summary"),
                            "primary": calendar.get("primary", False),
                            "time_zone": calendar.get("timeZone"),
                            "etag": calendar.get("etag"),
                            "access_role": calendar.get("accessRole"),
                        }
                    )

            return calendars

        except Exception as e:
            logging.error(f"Error retrieving calendars: {str(e)}")
            logging.error(traceback.format_exc())
            raise e

    def get_events(
        self,
        time_min=None,
        time_max=None,
        max_results=250,
        show_deleted=False,
        calendar_id: str = "primary",
    ):
        """
        Retrieve calendar events within a specified time range.

        Args:
            time_min (str, optional): Start time in RFC3339 format. Defaults to current time.
            time_max (str, optional): End time in RFC3339 format
            max_results (int): Maximum number of events to return (1-2500)
            show_deleted (bool): Whether to include deleted events

        Returns:
            list: List of calendar events
        """
        try:
            # If no time_min specified, use current time
            if not time_min:
                time_min = datetime.now(pytz.UTC).isoformat()

            # Ensure max_results is within limits
            max_results = min(max(1, max_results), 2500)

            # Prepare parameters
            params = {
                "calendarId": calendar_id,
                "timeMin": time_min,
                "maxResults": max_results,
                "singleEvents": True,
                "orderBy": "startTime",
                "showDeleted": show_deleted,
            }

            # Add optional time_max if specified
            if time_max:
                params["timeMax"] = time_max

            # Execute the events().list() method
            events_result = self.service.events().list(**params).execute()

            # Extract the events
            events = events_result.get("items", [])

            # Process and return the events
            processed_events = []
            for event in events:
                processed_event = {
                    "id": event.get("id"),
                    "summary": event.get("summary"),
                    "description": event.get("description"),
                    "start": event.get("start"),
                    "end": event.get("end"),
                    "status": event.get("status"),
                    "creator": event.get("creator"),
                    "organizer": event.get("organizer"),
                    "attendees": event.get("attendees"),
                    "location": event.get("location"),
                    "hangoutLink": event.get("hangoutLink"),
                    "conferenceData": event.get("conferenceData"),
                    "recurringEventId": event.get("recurringEventId"),
                }
                processed_events.append(processed_event)

            return processed_events

        except Exception as e:
            logging.error(f"Error retrieving calendar events: {str(e)}")
            logging.error(traceback.format_exc())
            raise e

    def create_event(
        self,
        summary: str,
        start_time: str,
        end_time: str,
        location: str | None = None,
        description: str | None = None,
        attendees: list | None = None,
        send_notifications: bool = True,
        timezone: str | None = None,
        calendar_id: str = "primary",
    ) -> dict | None:
        """
        Create a new calendar event.

        Args:
            summary (str): Title of the event
            start_time (str): Start time in RFC3339 format
            end_time (str): End time in RFC3339 format
            location (str, optional): Location of the event
            description (str, optional): Description of the event
            attendees (list, optional): List of attendee email addresses
            send_notifications (bool): Whether to send notifications to attendees
            timezone (str, optional): Timezone for the event (e.g. 'America/New_York')

        Returns:
            dict: Created event data or None if creation fails
        """
        try:
            # Prepare event data
            event = {
                "summary": summary,
                "start": {
                    "dateTime": start_time,
                    "timeZone": timezone or "UTC",
                },
                "end": {
                    "dateTime": end_time,
                    "timeZone": timezone or "UTC",
                },
            }

            # Add optional fields if provided
            if location:
                event["location"] = location
            if description:
                event["description"] = description
            if attendees:
                event["attendees"] = [{"email": email} for email in attendees]

            # Create the event
            created_event = (
                self.service.events()
                .insert(
                    calendarId=calendar_id,
                    body=event,
                    sendNotifications=send_notifications,
                )
                .execute()
            )

            return created_event

        except Exception as e:
            logging.error(f"Error creating calendar event: {str(e)}")
            logging.error(traceback.format_exc())
            return None

    def delete_event(
        self,
        event_id: str,
        send_notifications: bool = True,
        calendar_id: str = "primary",
    ) -> bool:
        """
        Delete a calendar event by its ID.

        Args:
            event_id (str): The ID of the event to delete
            send_notifications (bool): Whether to send cancellation notifications to attendees

        Returns:
            bool: True if deletion was successful, False otherwise
        """
        try:
            self.service.events().delete(
                calendarId=calendar_id,
                eventId=event_id,
                sendNotifications=send_notifications,
            ).execute()
            return True

        except Exception as e:
            logging.error(f"Error deleting calendar event {event_id}: {str(e)}")
            logging.error(traceback.format_exc())
            return False

    def update_event(
        self,
        event_id: str,
        summary: str | None = None,
        start_time: str | None = None,
        end_time: str | None = None,
        location: str | None = None,
        description: str | None = None,
        attendees: list | None = None,
        send_notifications: bool = True,
        timezone: str | None = None,
        calendar_id: str = "primary",
    ) -> dict | None:
        """
        Update an existing calendar event.

        Args:
            event_id (str): The ID of the event to update.
            summary (str, optional): New title of the event.
            start_time (str, optional): New start time in RFC3339 format.
            end_time (str, optional): New end time in RFC3339 format.
            location (str, optional): New location of the event.
            description (str, optional): New description of the event.
            attendees (list, optional): New list of attendee email addresses.
            send_notifications (bool): Whether to send notifications to attendees.
            timezone (str, optional): New timezone for the event (e.g. 'America/New_York').
            calendar_id (str): Calendar identifier. Defaults to 'primary'.

        Returns:
            dict: Updated event data or None if update fails.
        """
        try:
            # First, get the existing event to preserve fields not being updated
            existing_event = (
                self.service.events()
                .get(calendarId=calendar_id, eventId=event_id)
                .execute()
            )
            if not existing_event:
                logging.error(f"Event with ID {event_id} not found.")
                return None

            # Prepare event data with updated fields
            event_update_body = {}

            if summary is not None:
                event_update_body["summary"] = summary
            if start_time is not None:
                event_update_body["start"] = existing_event.get("start", {})
                event_update_body["start"]["dateTime"] = start_time
                if timezone:
                    event_update_body["start"]["timeZone"] = timezone
                elif "timeZone" not in event_update_body["start"]:
                    event_update_body["start"]["timeZone"] = "UTC"  # Default if not set
            if end_time is not None:
                event_update_body["end"] = existing_event.get("end", {})
                event_update_body["end"]["dateTime"] = end_time
                if timezone:
                    event_update_body["end"]["timeZone"] = timezone
                elif "timeZone" not in event_update_body["end"]:
                    event_update_body["end"]["timeZone"] = "UTC"  # Default if not set
            if location is not None:
                event_update_body["location"] = location
            if description is not None:
                event_update_body["description"] = description
            if attendees is not None:
                event_update_body["attendees"] = [
                    {"email": email} for email in attendees
                ]

            # If no fields are provided for update, return the existing event
            if not event_update_body:
                logging.info(f"No fields provided to update for event {event_id}.")
                return existing_event

            # Update the event
            updated_event = (
                self.service.events()
                .update(
                    calendarId=calendar_id,
                    eventId=event_id,
                    body=event_update_body,
                    sendNotifications=send_notifications,
                )
                .execute()
            )

            return updated_event

        except Exception as e:
            logging.error(f"Error updating calendar event {event_id}: {str(e)}")
            logging.error(traceback.format_exc())
            return None
