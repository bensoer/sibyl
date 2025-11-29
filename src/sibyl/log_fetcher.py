

import logging
from kubernetes import client, config


class LogFetcher():

    PREVIOUS_LOG_REASONS = [
        "BackOff",          # Container failed and is restarting
        #"Evicted",          # Pod was removed (logs may still exist from prior state)
        "Unhealthy",        # Liveness/Readiness failed, often leading to restart/kill
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

    def _get_pod_details(self, event_data: dict) -> tuple[str, str, str]:
        """Helper to extract necessary details from the event_data."""
        namespace = event_data['namespace']
        pod_name = event_data['involved_object']["name"]
        reason = event_data.get('reason', '')
        return namespace, pod_name, reason
    

    def fetch_current_pod_logs_from_event(self, k8s_event: dict, tail_lines: int = 100) -> str:


        namespace, pod_name, _ = self._get_pod_details(k8s_event)

        try:
            log_response = self.core_v1_client.read_namespaced_pod_log(
                name=pod_name,
                namespace=namespace,
                tail_lines=tail_lines,
                previous=False,
                _preload_content=False
            )
            self._logger.debug(f"Fetched current logs for Pod: {pod_name} in Namespace: {namespace}")
            return log_response
        
        except client.ApiException as e:
            self._logger.error(f"Failed to fetch current logs for Pod: {pod_name} in Namespace: {namespace}", exc_info=e)
            raise e

    def fetch_previous_pod_logs_from_event(self, k8s_event: dict, tail_lines: int = 100) -> str:

        namespace, pod_name, _ = self._get_pod_details(k8s_event)

        try:
            log_response = self.core_v1_client.read_namespaced_pod_log(
                name=pod_name,
                namespace=namespace,
                tail_lines=tail_lines,
                previous=True,
                _preload_content=False
            )
            self._logger.debug(f"Fetched previous logs for Pod: {pod_name} in Namespace: {namespace}")
            return log_response
        except client.ApiException as e:

            if e.status == 404: # 404 means the previous pod simply does not exist
                self._logger.debug(f"Logs Not Found. Pod May Have Restarted or Been Evicted. Pod: {pod_name} in Namespace: {namespace}")
                return f"Logs Not Found. Pod May Have Restarted or Been Evicted. {pod_name} in Namespace: {namespace}"


            self._logger.error(f"Failed to fetch previous logs for Pod: {pod_name} in Namespace: {namespace}", exc_info=e)
            raise e


    def fetch_pod_logs_from_event(self, k8s_event: dict, tail_lines: int = 100) -> str:

        namespace, pod_name, reason = self._get_pod_details(k8s_event)
        fetch_previous = reason in self.PREVIOUS_LOG_REASONS

        # try:
            #if fetch_previous:
            #    return self.fetch_previous_pod_logs_from_event(k8s_event, tail_lines)
            #return self.fetch_current_pod_logs_from_event(k8s_event, tail_lines)
        
        previous_logs = self.fetch_previous_pod_logs_from_event(k8s_event, tail_lines)
        current_logs = self.fetch_current_pod_logs_from_event(k8s_event, tail_lines)

        if len(previous_logs.strip()) == 0 and len(current_logs.strip()) == 0:
            return "No logs found for either current or previous container instances."
        
        return f"--- Previous Logs ---\n{previous_logs}\n\n--- Current Logs ---\n{current_logs}"

        # except client.ApiException as e:
            
        #     if e.status == 400 and fetch_previous:
        #         self._logger.debug(f"Attempting To Fetch Current Logs Due To Previous Not Being Ready. Attempting to fetch current logs as fallback for Pod: {pod_name} in Namespace: {namespace}")
        #         try:
        #             return self.fetch_current_pod_logs_from_event(k8s_event, tail_lines)
        #         except client.ApiException as inner_e:
        #             self._logger.error(f"Fetching Previous failed. And We've now failed to fetch current logs of pod: {pod_name} in namespace: {namespace}", exc_info=inner_e)
        #             raise e from inner_e


        #     self._logger.error(f"Failed to fetch {'Previous' if fetch_previous else 'Current'} logs for Pod: {pod_name} in Namespace: {namespace}", exc_info=e)
        #     # if the above IF doesn't get anywhere then we throw our original exception
        #     raise e
            
