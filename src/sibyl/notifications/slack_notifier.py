

import logging
from typing import Optional

import requests
from slack_sdk.webhook import WebhookClient

from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

from sibyl.models.events.k8_event import K8Event
from sibyl.notifications.notifiable import Notifiable


class SlackNotifier(Notifiable):
    
    def __init__(self, bot_token: str, channel: str):
        self._logger = logging.getLogger(self.__class__.__name__)
        self.client = WebClient(token=bot_token)
        self.channel = channel

    def _create_timestamp_table(self, event_data: K8Event) -> dict:
        return {
            "type": "table",
            "rows": [
                self._create_timestamp_table_headers(),
                self._create_timestamp_table_row("Event Timestamp", event_data.timestamp),
                self._create_timestamp_table_row("Involved Object Creation Timestamp", event_data.metadata.creation_timestamp or "N/A"),
                self._create_timestamp_table_row("Involved Object Deletion Timestamp", event_data.metadata.deletion_timestamp or "N/A")
            ]
        }

    def _create_timestamp_table_headers(self) -> list:
        return [
            {
                "type": "rich_text",
                "elements": [
                    {
                        "type": "rich_text_section",
                        "elements": [
                            {
                                "type": "text",
                                "text": "Type",
                                "style": {
                                    "bold": True
                                }
                            }
                        ]
                    }
                ]
            },
            {
                "type": "rich_text",
                "elements": [
                    {
                        "type": "rich_text_section",
                        "elements": [
                            {
                                "type": "text",
                                "text": "Timestamp",
                                "style": {
                                    "bold": True
                                }
                            }
                        ]
                    }
                ]
            }
        ]

    def _create_timestamp_table_row(self, timestamp_type: str, timestamp: str) -> list:
        return [
                {
                    "type": "rich_text",
                    "elements": [
                        {
                            "type": "rich_text_section",
                            "elements": [
                                {
                                    "type": "text",
                                    "text": timestamp_type
                                }
                            ]
                        }
                    ]
                },
                {
                    "type": "rich_text",
                    "elements": [
                        {
                            "type": "rich_text_section",
                            "elements": [
                                {
                                    "type": "text",
                                    "text": timestamp
                                }
                            ]
                        }
                    ]
                }
            ]

    def notify(self, event_data: K8Event, logs: Optional[str] = None) -> None:
        self._logger.info(f"Sending Slack notification for event: {event_data.name} in namespace: {event_data.namespace}")

        color = "#f2c744" if event_data.type == "Warning" else "#3641a6"
        
        # Notify slack of the event
        postMessage_response = self.client.chat_postMessage(
            channel=self.channel,
            text=f"*Kubernetes Ev[ent Notification*\n*Reason:* {event_data.reason}\n*Message:* {event_data.message}\n*Namespace:* {event_data.namespace}\n*Involved Object:* {event_data.involved_object.kind} / {event_data.involved_object.name}\n*Timestamp:* {event_data.timestamp}\n\n*Logs:*\n```{logs}```" if logs else "",
            blocks=[
                {
                    "type" : "section",
                    "text": {
                        "type":"mrkdwn",
                        "text": f"*{event_data.type}:* {event_data.involved_object.kind} {event_data.involved_object.namespace}/{event_data.involved_object.name} -> {event_data.reason} "
                    }
                },
                
                {
                    "type": "section",
                    "fields": [
                        {
                            "type": "mrkdwn",
                            "text": f"*Involved Object:*\n{event_data.involved_object.name}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Namespace:*\n{event_data.involved_object.namespace}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Kind:*\n{event_data.involved_object.kind}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Reason:*\n{event_data.reason}"
                        }
                    ]
                },
                {
                    "type": "divider"
                },
                {
                    "type": "rich_text",
                    "elements": [
                        {
                            "type": "rich_text_preformatted",
                            "elements": [
                                {
                                    "type": "text",
                                    "text": event_data.message
                                }
                            ]
                        }
                    ]
                },
                # {
                #     "type": "rich_text",
                #     "elements": [
                #         {
                #             "type": "rich_text_section",
                #             "elements": [
                #                 {
                #                     "type": "text",
                #                     "text": "Timeline",
                #                     "style": {
                #                         "bold": True
                #                     }
                #                 }
                #             ]
                #         }
                #     ]
                # },
                self._create_timestamp_table(event_data),
            ]
        )

        # Check the notification was successful
        ok = postMessage_response.get("ok", False)
        if not ok:
            error = postMessage_response.get("error")
            if error:
                self._logger.error(f"Failed to post slack notification for event {event_data.involved_object.namespace}/{event_data.involved_object.name} to Slack: {error}")
            return

        # IF we have logs, then upload them and include them in a thread of the post
        if logs:
            message_ts = postMessage_response.get('ts')
            channel_id = postMessage_response.get('channel')

            # Allocate upload space on Slack
            getUploadURLExternal_response = self.client.files_getUploadURLExternal(
                filename=f"logs_{event_data.involved_object.kind}_{event_data.involved_object.namespace}_{event_data.involved_object.name}.txt",
                length=len(logs),
                snippet_type="text",
                alt_txt=f"Log File For K8s Event Involving {event_data.involved_object.namespace}/{event_data.involved_object.name}"
            )

            # Check allocation was successful
            ok = getUploadURLExternal_response.get("ok", False)
            if not ok:
                error = getUploadURLExternal_response.get("error")
                if error:
                    self._logger.error(f"Slack files.getUploadURLExternal Failed for event {event_data.involved_object.namespace}/{event_data.involved_object.name} to Slack: {error}")
                return


            upload_url = getUploadURLExternal_response.get("upload_url")
            file_id = getUploadURLExternal_response.get("file_id")


            # Upload the actual log/file contents
            try:
                headers = {
                    # This header tells the server we are sending raw bytes
                    'Content-Type': 'application/octet-stream'
                }
                upload_response = requests.post(
                    upload_url, 
                    headers=headers, 
                    data=logs.encode('utf-8'),
                    
                )
                upload_response.raise_for_status()
            except Exception as e:
                self._logger.error(f"Failed to upload logs for event {event_data.involved_object.namespace}/{event_data.involved_object.name} to Slack", exc_info=e)
                return

            # Complete the upload process, posting the logs as a thread to the original message
            completeUploadExternal_response = self.client.files_completeUploadExternal(
                upload_url=upload_url,
                channel_id=channel_id,
                channels=channel_id,
                #thread_ts=message_ts,
                initial_comment="Attached logs for the Kubernetes event:",
                files=[
                    {
                        "id": file_id,
                        "title": f"logs_{event_data.involved_object.kind}_{event_data.involved_object.namespace}_{event_data.involved_object.name}.txt",
                    }
                ]
            )



            # Check completion was successful
            ok = completeUploadExternal_response.get("ok", False)
            self._logger.debug(completeUploadExternal_response)
            if not ok:
                error = completeUploadExternal_response.get("error")
                if error:
                    self._logger.error(f"Slack files.completeUploadExternal Failed for event {event_data.involved_object.namespace}/{event_data.involved_object.name} to Slack: {error}")
                return


