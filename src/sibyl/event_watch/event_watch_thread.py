from threading import Thread, Event
from time import time
from kubernetes import client, config, watch
from kubernetes.client.models import CoreV1Event
import logging
from queue import Queue
import time

from sibyl.event_watch.event_watch import EventWatch
from sibyl.models.events.k8_event import K8Event
from sibyl.models.events.k8_event_involved_object import K8EventInvolvedObject
from sibyl.models.events.k8_event_metadata import K8EventMetadata
from sibyl.models.events.k8_event_source import K8EventSource

class EventWatchThread(Thread):

    ERROR_TYPES = ["Warning", "Error", "Failed", "Evicted", "Unhealthy", "BackOff", "FailedScheduling"]


    def __init__(self, event_queue: Queue):
        super().__init__(daemon=True)
        self._logger = logging.getLogger(self.__class__.__name__)
        self.event_queue: Queue = event_queue
        self._stop_event: Event = Event()

        try:
            config.load_incluster_config()
            self.core_v1_client = client.CoreV1Api()
            self._logger.debug("Loading K8s Configuration Successful")
        except Exception as e:
            self._logger.error("Exception Thrown Loading K8s In Cluster Configuration", exc_info=e)
            self._logger.error("Is External Secrets Reloader Running Inside Of A Kubernetes Cluster ?")

            self.core_v1_client = None
            self._stop_event.set()

            raise e
        
    def stop(self):
        self._logger.info("Stopping Event Watch Thread")
        self._stop_event.set()

    def run(self):
        
        if not self.core_v1_client:
            self._logger.error("K8s CoreV1Api Client Not Initialized. Exiting Event Watch Thread.")
            return
        
        def k8s_v1event_handler(k8s_event: CoreV1Event):
            if k8s_event.type in self.ERROR_TYPES:
                self._logger.debug(f"Detected K8s Event: {k8s_event.reason} - {k8s_event.message}")
                self.event_queue.put(self._format_event(k8s_event))
            else:
                self._logger.debug(f"Ignoring Non-Error K8s Event: {k8s_event.reason} - {k8s_event.message}")

        event_watch = EventWatch(self.core_v1_client, timeout_seconds=300)
        while not self._stop_event.is_set():
            try:

                event_watch.poll_for_event(callback=k8s_v1event_handler)
                
                # If the loop naturally finishes (e.g., due to timeout_seconds), reconnect
                self._logger.debug("Watcher stream timed out (reconnecting)...")

            except client.ApiException as e:
                # Log API errors and wait before attempting to reconnect
                self._logger.error(f"Kubernetes API Error in Watcher: {e}. Retrying in 10s...")
                time.sleep(10)
            except Exception as e:
                self._logger.error(f"Unexpected error in Watcher: {e}. Retrying in 10s...")
                time.sleep(10)

    def _format_event(self, k8s_event: CoreV1Event) -> K8Event:
        """Formats the CoreV1Event object into a simple dictionary for the queue."""

        k8_event_source = K8EventSource(
            component=k8s_event.source.component,
            host=k8s_event.source.host
        )
        k8_event_metadata = K8EventMetadata(
            name=k8s_event.metadata.name,
            namespace=k8s_event.metadata.namespace,
            creation_timestamp=k8s_event.metadata.creation_timestamp.isoformat() if k8s_event.metadata.creation_timestamp else None,
            deletion_timestamp=k8s_event.metadata.deletion_timestamp.isoformat() if k8s_event.metadata.deletion_timestamp else None
        )
        k8_event_involved_object = K8EventInvolvedObject(
            kind=k8s_event.involved_object.kind,
            name=k8s_event.involved_object.name,
            namespace=k8s_event.involved_object.namespace
        )

        return K8Event(
            kind=k8s_event.kind,
            source=k8_event_source,
            action=k8s_event.action,
            type=k8s_event.type,
            namespace=k8s_event.metadata.namespace,
            name=k8s_event.metadata.name,
            reason=k8s_event.reason,
            message=k8s_event.message,
            metadata=k8_event_metadata,
            involved_object=k8_event_involved_object,
            timestamp=k8s_event.last_timestamp.isoformat() if k8s_event.last_timestamp else "N/A"
        )