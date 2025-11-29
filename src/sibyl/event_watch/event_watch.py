from typing import Callable, Optional
import logging
from kubernetes import client, watch
from kubernetes.client import CoreV1Event, CoreV1Api

class EventWatch():

    def __init__(self, core_v1_client: CoreV1Api, timeout_seconds: Optional[int] = 300):
        self._logger = logging.getLogger(self.__class__.__name__)
        self.core_v1_client = core_v1_client
        self.timeout_seconds = timeout_seconds

    def poll_for_event(self, callback: Callable[[CoreV1Event], None]) -> None:
        self._logger.debug("Starting K8s Event Watcher Polling Loop")
        w = watch.Watch()

        try:
            # Use stream() which handles the continuous API connection
            event_stream = w.stream(
                func=self.core_v1_client.list_event_for_all_namespaces,
                timeout_seconds=self.timeout_seconds # Reconnect based on the timeout_seconds parameter
            )
            self._logger.debug("K8s Event Watcher Stream Established")
            for event in event_stream:
                self._logger.debug("K8s Event Received from Watcher Stream")
                k8s_event = event['object']
                callback(k8s_event)

        except client.ApiException as e:
            # Log API errors and wait before attempting to reconnect
            self._logger.error(f"Kubernetes API Error in Watcher: {e}")
            raise e
        except Exception as e:
            self._logger.error(f"Unexpected error in Watcher: {e}")
            raise e