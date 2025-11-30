

import logging
from typing import Optional
from kubernetes import client, config

from sibyl.models.events.k8_event import K8Event


class LogFetcher():

    PREVIOUS_LOG_REASONS = [
        "BackOff",          # Container failed and is restarting
        #"Evicted",          # Pod was removed (logs may still exist from prior state)
        #"Unhealthy",        # Liveness/Readiness failed, often leading to restart/kill
        "Failed"            # 'Failed' events often point directly to a container termination
    ]

    def __init__(self):
        self._logger = logging.getLogger(self.__class__.__name__)

        try:
            config.load_incluster_config()
            self.core_v1_client = client.CoreV1Api()
            self._logger.debug("Loading K8s Configuration Successful")
        except Exception as e:
            self._logger.error("Exception Thrown Loading K8s In Cluster Configuration", exc_info=e)
            self._logger.error("Is External Secrets Reloader Running Inside Of A Kubernetes Cluster ?")

    def _get_pod_details(self, event_data: K8Event) -> tuple[str, str, str]:
        """Helper to extract necessary details from the event_data."""
        namespace = event_data.namespace
        pod_name = event_data.involved_object.name
        reason = event_data.reason
        return namespace, pod_name, reason
    

    def fetch_current_pod_logs_from_event(self, k8s_event: K8Event, tail_lines: int = 100) -> Optional[str]:


        namespace, pod_name, _ = self._get_pod_details(k8s_event)

        try:
            log_response = self.core_v1_client.read_namespaced_pod_log(
                name=pod_name,
                namespace=namespace,
                tail_lines=tail_lines,
                previous=False,
            )
            self._logger.debug(f"Fetched current logs for Pod: {namespace}/{pod_name}")
            return log_response
        
        except client.ApiException as e:
            if e.status == 404:
                self._logger.debug(f"Logs Not Found For CURRENT Pod Logs. Pod May Not Exist Anymore. {namespace}/{pod_name}")
                return None

            self._logger.error(f"Failed to fetch CURRENT logs for Pod: {namespace}/{pod_name}", exc_info=e)
            raise e

    def fetch_previous_pod_logs_from_event(self, k8s_event: K8Event, tail_lines: int = 100) -> Optional[str]:

        namespace, pod_name, _ = self._get_pod_details(k8s_event)

        try:
            log_response = self.core_v1_client.read_namespaced_pod_log(
                name=pod_name,
                namespace=namespace,
                tail_lines=tail_lines,
                previous=True,
            )
            self._logger.debug(f"Fetched previous logs for Pod: {namespace}/{pod_name}")
            return log_response
        except client.ApiException as e:

            if e.status == 404: # 404 means the previous pod simply does not exist
                self._logger.debug(f"Logs Not Found For PREVIOUS Pod Logs. Pod May Not Exist Anymore. {namespace}/{pod_name}")
                return None


            self._logger.error(f"Failed to fetch PREVIOUS logs for Pod: {namespace}/{pod_name}", exc_info=e)
            raise e


    def fetch_pod_logs_from_event(self, k8s_event: K8Event, tail_lines: int = 100) -> Optional[str]:

        namespace, pod_name, reason = self._get_pod_details(k8s_event)
        fetch_previous = reason in self.PREVIOUS_LOG_REASONS

        # If its specifically an Unhealthy event due to Liveness probe, we want previous logs
        # Otherwise Unhealthy does not likely mean the container has restarted yet
        if reason == "Unhealthy" and "Liveness probe failed" in k8s_event.message:
            fetch_previous = True

        try:
            if fetch_previous:
               result = self.fetch_previous_pod_logs_from_event(k8s_event, tail_lines)
               # If it returned None without an exception that means it was a 404 or some expected possible outcome
               if result is None:
                   self._logger.debug(f"PREVIOUS logs not found for Pod: {namespace}/{pod_name}. Falling back to CURRENT logs.")
                   # We should check the current logs as well as a fallback for this
                   return self.fetch_current_pod_logs_from_event(k8s_event, tail_lines)
                   
            return self.fetch_current_pod_logs_from_event(k8s_event, tail_lines)
        
        except client.ApiException as e:
            self._logger.error(f"Failed to fetch {'PREVIOUS' if fetch_previous else 'CURRENT'} logs for Pod: {namespace}/{pod_name}", exc_info=e)
            # if the above IF doesn't get anywhere then we throw our original exception
            raise e
            
