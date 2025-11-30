# Project: Sibyl - Kubernetes Event Monitor

This `GEMINI.md` file serves as a quick reference guide to understand the context, structure, and goals of the Sibyl project. It is intended to help the Gemini agent work more efficiently by providing essential information at a glance.

## Project Goal

The primary goal of the Sibyl project is to provide a Python application that runs within a Kubernetes cluster to monitor its event log. Upon detecting relevant Kubernetes events, the application fetches associated pod logs and then posts this information to a configured Slack channel, providing real-time operational insights and alerts.

## Key Technologies and Libraries

*   **Language:** Python 3.11+
*   **Package Manager:** `uv`
*   **Kubernetes Interaction:** `kubernetes` client library
*   **Web Framework (Health Checks):** `Flask`
*   **Configuration:** `Pydantic-settings`
*   **Logging:** `python-json-logger`
*   **Notifications:** `slack-sdk`
*   **Testing:** `pytest`, `pytest-cov`, `pytest-mock`

## Project Structure and Core Components

The application's Python source code is located in the `src/sibyl/` directory.

### `src/sibyl/main.py`
The main entry point of the application. It orchestrates the startup and management of various components:
*   Initializes logging and signal handlers (`SIGINT`, `SIGTERM`).
*   Loads application settings using `sibyl.settings.Settings`.
*   Starts the `HealthStatusThread` for liveness and readiness probes.
*   Initializes and starts the `EventWatchThread` to monitor Kubernetes events.
*   Initializes `LogFetcher` for retrieving pod logs.
*   Initializes `SlackNotifier` for sending notifications.
*   Contains the main event processing loop, which consumes events from a queue, fetches logs if relevant, and sends notifications.

### `src/sibyl/settings.py`
Defines the `Settings` class using Pydantic's `BaseSettings` for managing application configuration. It loads environment variables such as `SLACK_BOT_TOKEN`, `SLACK_CHANNEL`, `HEALTH_CHECK_PORT`, `LOG_LEVEL`, `CLUSTER_NAME`, and `POD_LOG_TAIL_LINES`.

### `src/sibyl/health_check/`
Manages the application's health and readiness status.
*   **`health_status.py`**: A simple class (`HealthStatus`) to maintain the current health and readiness state, using threading locks for thread-safety.
*   **`health_status_thread.py`**: Runs a `Flask` web server in a separate thread, exposing `/health` (liveness) and `/ready` (readiness) HTTP endpoints. These endpoints reflect the status managed by `HealthStatus`.

### `src/sibyl/event_watch/`
Responsible for monitoring Kubernetes API for events.
*   **`event_watch.py`**: The `EventWatch` class utilizes the `kubernetes` client's `watch` API to continuously poll for events across all namespaces. It processes these events and passes them to a callback function.
*   **`event_watch_thread.py`**: A `Thread` subclass (`EventWatchThread`) that encapsulates an `EventWatch` instance. It runs the event monitoring loop in a background thread, filters for "error" type events, formats them, and places them into a `Queue` for further processing by the main application loop. It handles Kubernetes API client configuration.

### `src/sibyl/log_fetcher.py`
Handles fetching logs from Kubernetes pods.
*   The `LogFetcher` class provides methods to retrieve current or previous logs for a given pod involved in a Kubernetes event.
*   It includes logic to decide whether to fetch previous logs based on the event reason (e.g., `BackOff`, `Unhealthy` with specific messages).

### `src/sibyl/notifications/`
Manages sending notifications to external systems.
*   **`notifiable.py`**: Defines an abstract base class `Notifiable` with an `abstractmethod` `notify()`, serving as an interface for notification mechanisms.
*   **`slack_notifier.py`**: Implements the `Notifiable` interface for sending rich notifications to Slack. It constructs Slack blocks and handles both basic messages and uploading log files to threads.

### `src/sibyl/models/events/`
Contains Python `dataclass`es representing various Kubernetes event structures.
*   **`k8_event.py`**: The main `K8Event` dataclass.
*   **`k8_event_involved_object.py`**: Details about the object involved in the event.
*   **`k8_event_metadata.py`**: Metadata about the event itself.
*   **`k8_event_source.py`**: Information about the source of the event.

## Development and Testing Workflow

*   **Dependency Management:** `uv` is used for managing Python dependencies.
*   **Testing Framework:** `pytest` is used for writing and running unit tests.
*   **Test Execution:** Tests can be run using the command `uv run pytest`.
*   **Code Coverage:** `pytest-cov` is configured to report code coverage. Use `uv run pytest --cov=src --cov-report=term-missing` to view coverage.
*   **Mocking:** `pytest-mock` is used extensively for mocking external dependencies (e.g., Kubernetes API, Slack API, `requests`).

## Important Notes for Gemini Agent

*   **Logging:** The application uses structured JSON logging configured via `python-json-logger`.
*   **Error Handling:** Components often include `try-except` blocks to handle Kubernetes API errors and general exceptions gracefully, often with retry mechanisms or logging.
*   **Concurrency:** Multiple parts of the application (event watching, health checks) run in separate Python `Thread`s. Special attention was given to testing these concurrent components.
*   **Kubernetes Context:** The application expects to run within a Kubernetes cluster (`config.load_incluster_config()`) for its primary functionality.
*   **Pydantic Settings:** Configuration is handled strictly by Pydantic, meaning required environment variables must be set for the application to initialize correctly. During testing, these were mocked or dummy environment variables were set.
*   **Test Architecture:** Test files are mirrored under the `tests/` directory (e.g., `src/sibyl/module.py` has tests in `tests/test_module.py` or `tests/module/test_file.py` for subdirectories).

This `GEMINI.md` should provide sufficient context to begin working on the Sibyl project effectively.