

import logging
from queue import Queue, Empty
import signal
from sys import exit, stdout
from typing import Optional
from pythonjsonlogger import jsonlogger

from sibyl.event_watch.event_watch_thread import EventWatchThread
from sibyl.health_check.health_status_thread import HealthStatusThread
from sibyl.log_fetcher import LogFetcher
from sibyl.settings import Settings

print("==== Starting Application ====")

# .env file or environment variable parsing all out into a single object
settings = Settings()

print("==== Environment Settings Parsed ====")

# Logging configuration, allows for global control of logging level and
# configures logging across dependencies. Keeps dependencies quiet
# unless it is WARN or higher, unless LOG_LEVEL from the settings are
# set to DEBUG, then also sets depdnencies levels to INFO

logging_levels = {
    'ERROR': logging.ERROR,
    'WARN': logging.WARN,
    'INFO': logging.INFO,
    'DEBUG': logging.DEBUG,
}
#logging_level_int = logging_levels.get(settings.LOG_LEVEL, logging.INFO)
logging_level_int = logging.DEBUG

rootLogger = logging.getLogger()
rootLogger.setLevel(logging_level_int)

# Simple json output when we are not in DEBUG mode
json_format = '%(levelname)s %(name)s %(message)s'
if logging_level_int == logging.DEBUG:
    # More verbose and detailed logging info when we are in DEBUG mode
    json_format = '%(levelno)s %(levelname)s %(name)s %(module)s %(funcName)s %(lineno)d %(message)s'

formatter = jsonlogger.JsonFormatter(
    json_format, 
    datefmt='%Y-%m-%d %H:%M:%S',
    json_ensure_ascii=False,
    timestamp=True
)

handler = logging.StreamHandler(stdout)
handler.setFormatter(formatter)

if rootLogger.hasHandlers():
    rootLogger.handlers.clear()
rootLogger.addHandler(handler)


# Suppress verbose logging from third-party libraries
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("werkzeug").setLevel(logging.WARNING if logging_level_int != logging.DEBUG else logging.INFO)

# This is our logger for this main bootstrapping code here. Classes all log using a class logger
# that inherits configuration from the rootLogger
logger = logging.getLogger("sibyl")

print("==== Logging Registered ====")

# SIGINT and SIGTERM Handling. Gracefully stop things when we receive any of those
# SIGTERM - Kuberentes sends this as a warning when it wants to shut the pod down
# SIGINT - Generally CTRL+C events send this to the process

CONTINUE_PROCESSING = True
def signal_handler(sig, frame):
    global CONTINUE_PROCESSING

    """
    Custom handler function for signals.
    """
    if sig == signal.SIGINT:
        logger.info('Received SIGINT (Ctrl+C). Starting graceful shutdown...')
    elif sig == signal.SIGTERM:
        logger.info('Received SIGTERM. Starting graceful shutdown...')
    else:
        logger.info(f'Received signal {sig}. Performing graceful shutdown...')

    CONTINUE_PROCESSING = False
    return


signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

print("==== SIG Handlers Registered ====")

def main() -> None:
    global CONTINUE_PROCESSING

    startup_message = """
======================================================
 ________  ___  ________      ___    ___ ___          
|\   ____\|\  \|\   __  \    |\  \  /  /|\  \         
\ \  \___|\ \  \ \  \|\ /_   \ \  \/  / | \  \        
 \ \_____  \ \  \ \   __  \   \ \    / / \ \  \       
  \|____|\  \ \  \ \  \|\  \   \/  /  /   \ \  \____  
    ____\_\  \ \__\ \_______\__/  / /      \ \_______\\
   |\_________\|__|\|_______|\___/ /        \|_______|
   \|_________|             \|___|/                   
                                                      
======================================================
           Created By Ben Soer (@bensoer)             """

    print(startup_message + "\n\n")

    # Start health check server for Kubernetes probes
    logger.info("Starting Health Check Endpoints")
    hst = HealthStatusThread()
    hst.start(port=settings.HEALTH_CHECK_PORT, debug=(logging_level_int == logging.DEBUG))
    # Get the health status object to update during initialization
    health_status = hst.get_health_status()
    health_status.set_ready(False)  # Mark as not ready during initialization
    logger.debug("Health Check Endpoints Started")

    logger.info("Initializing Components")
    event_queue = Queue()
    event_watch_thread: Optional[EventWatchThread] = None
    log_fetcher: Optional[LogFetcher] = None


    logger.info("Starting Kubernetes Event Watcher Thread")
    
    try:
        event_watch_thread = EventWatchThread(event_queue)
        event_watch_thread.start()
    except Exception as e:
        logger.error(f"Failed to start Kubernetes Event Watcher Thread")
        event_watch_thread = None
        exit(1)

    try:
        log_fetcher = LogFetcher()
    except Exception as e:
        logger.error(f"Failed to initialize LogFetcher")
        log_fetcher = None
        exit(1)

    logger.debug("Kubernetes Event Watcher Thread Started")


    health_status.set_healthy(True)
    health_status.set_ready(True)

    logger.debug("Application Initialization Complete. Entering Main Processing Loop")
    while CONTINUE_PROCESSING:
        # Main loop can process events from the event_queue here
        try:
            event = event_queue.get(block=True, timeout=1)  # Wait for an event for up to 1 second
            logs = log_fetcher.fetch_pod_logs_from_event(event, tail_lines=10)
            
            logger.debug(f"Fetched logs for event: {logs.decode('utf-8')}")
            logger.info(f"Processing event: {event}")
            # Process the event here
        except Empty:
            # Timeout occurred, no event received, continue the loop
            continue
        except Exception as e:
            logger.error(f"Error processing event: {e}", exc_info=e)
            # Timeout occurred, no event received, continue the loop
            continue


    logger.info("Processing Has Stopped As We Are Shutting Down. Goodbye!")