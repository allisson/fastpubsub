# fastpubsub

Simple pubsub system based on FastAPI and PostgreSQL.

## Overview

fastpubsub is a lightweight publish-subscribe messaging system built with FastAPI and PostgreSQL. It provides reliable message delivery with features like dead letter queues (DLQ), message acknowledgment, and automatic retry with exponential backoff.

## Docker Image

The project is available as a Docker image on Docker Hub:

```
docker pull allisson/fastpubsub
```

## Prerequisites

- Docker
- PostgreSQL database (version 12 or higher recommended)

## Configuration

The service is configured through environment variables. All environment variables use the `fastpubsub_` prefix.

### Required Environment Variables

- `fastpubsub_database_url`: PostgreSQL connection URL (e.g., `postgresql+psycopg://user:password@host:5432/dbname`)

### Optional Environment Variables

#### Database Configuration

- `fastpubsub_database_echo`: Enable SQL query logging (default: `false`)
- `fastpubsub_database_pool_size`: Database connection pool size (default: `5`)
- `fastpubsub_database_max_overflow`: Maximum overflow connections (default: `10`)
- `fastpubsub_database_pool_pre_ping`: Enable connection health checks (default: `true`)

#### Logging Configuration

- `fastpubsub_log_level`: Log level - `debug`, `info`, `warning`, `error` (default: `info`)
- `fastpubsub_log_formatter`: Log format string (default: `asctime=%(asctime)s level=%(levelname)s pathname=%(pathname)s line=%(lineno)s message=%(message)s`)

#### Subscription Defaults

- `fastpubsub_subscription_max_attempts`: Maximum delivery attempts before sending to DLQ (default: `5`)
- `fastpubsub_subscription_backoff_min_seconds`: Minimum backoff time between retries (default: `5`)
- `fastpubsub_subscription_backoff_max_seconds`: Maximum backoff time between retries (default: `300`)

#### API Configuration

- `fastpubsub_api_debug`: Enable FastAPI debug mode (default: `false`)
- `fastpubsub_api_host`: API server host (default: `0.0.0.0`)
- `fastpubsub_api_port`: API server port (default: `8000`)
- `fastpubsub_api_num_workers`: Number of worker processes (default: `1`)

#### Cleanup Configuration

- `fastpubsub_cleanup_acked_messages_older_than_seconds`: Age threshold for cleaning up acknowledged messages (default: `3600`)
- `fastpubsub_cleanup_stuck_messages_lock_timeout_seconds`: Timeout for releasing stuck messages (default: `60`)

## Usage

### 1. Database Migration

Before running the server, you need to initialize the database schema:

```bash
docker run \
  -e fastpubsub_database_url='postgresql+psycopg://user:password@host:5432/dbname' \
  allisson/fastpubsub db-migrate
```

This command creates all necessary tables, indexes, and stored procedures in your PostgreSQL database.

### 2. Running the API Server

Start the FastAPI server to expose the REST API:

```bash
docker run -p 8000:8000 \
  -e fastpubsub_database_url='postgresql+psycopg://user:password@host:5432/dbname' \
  allisson/fastpubsub server
```

The API will be accessible at `http://localhost:8000`. The interactive API documentation (Swagger UI) is available at `http://localhost:8000/docs`.

### 3. Cleanup Acknowledged Messages

Periodically remove acknowledged messages older than a specified threshold:

```bash
docker run \
  -e fastpubsub_database_url='postgresql+psycopg://user:password@host:5432/dbname' \
  -e fastpubsub_cleanup_acked_messages_older_than_seconds='3600' \
  allisson/fastpubsub cleanup_acked_messages
```

This should be run as a scheduled job (e.g., cron) to keep the database clean.

### 4. Cleanup Stuck Messages

Release messages that have been locked for too long without being acknowledged or rejected:

```bash
docker run \
  -e fastpubsub_database_url='postgresql+psycopg://user:password@host:5432/dbname' \
  -e fastpubsub_cleanup_stuck_messages_lock_timeout_seconds='60' \
  allisson/fastpubsub cleanup_stuck_messages
```

This should also be run as a scheduled job to handle edge cases where consumers crash while processing messages.

## API Endpoints

### Topics

- `POST /topics` - Create a new topic
- `GET /topics/{id}` - Get topic details
- `GET /topics` - List all topics
- `DELETE /topics/{id}` - Delete a topic
- `POST /topics/{id}/messages` - Publish messages to a topic

### Subscriptions

- `POST /subscriptions` - Create a new subscription
- `GET /subscriptions/{id}` - Get subscription details
- `GET /subscriptions` - List all subscriptions
- `DELETE /subscriptions/{id}` - Delete a subscription
- `GET /subscriptions/{id}/messages` - Consume messages from a subscription
- `POST /subscriptions/{id}/acks` - Acknowledge messages
- `POST /subscriptions/{id}/nacks` - Reject messages (retry later)
- `GET /subscriptions/{id}/dlq` - List dead letter queue messages
- `POST /subscriptions/{id}/dlq/reprocess` - Reprocess messages from DLQ
- `GET /subscriptions/{id}/metrics` - Get subscription metrics

## Example Workflow

### 1. Create a Topic

```bash
curl -X POST http://localhost:8000/topics \
  -H "Content-Type: application/json" \
  -d '{"id": "my-topic"}'
```

### 2. Create a Subscription

```bash
curl -X POST http://localhost:8000/subscriptions \
  -H "Content-Type: application/json" \
  -d '{
    "id": "my-subscription",
    "topic_id": "my-topic",
    "max_delivery_attempts": 5,
    "backoff_min_seconds": 5,
    "backoff_max_seconds": 300
  }'
```

### 3. Publish Messages

```bash
curl -X POST http://localhost:8000/topics/my-topic/messages \
  -H "Content-Type: application/json" \
  -d '[
    {"message": "Hello, World!"},
    {"message": "Another message", "priority": "high"}
  ]'
```

### 4. Consume Messages

```bash
curl -X GET "http://localhost:8000/subscriptions/my-subscription/messages?consumer_id=consumer-1&batch_size=10"
```

### 5. Acknowledge Messages

```bash
curl -X POST http://localhost:8000/subscriptions/my-subscription/acks \
  -H "Content-Type: application/json" \
  -d '["message-uuid-1", "message-uuid-2"]'
```

## Features

- **Reliable Message Delivery**: Messages are persisted in PostgreSQL and guaranteed to be delivered
- **Dead Letter Queue (DLQ)**: Messages that fail after max attempts are moved to DLQ for manual inspection
- **Exponential Backoff**: Automatic retry with configurable exponential backoff between attempts
- **Message Filtering**: Subscriptions can filter messages based on JSON attributes
- **Consumer Groups**: Multiple consumers can process messages from the same subscription
- **Metrics**: Track available, delivered, acknowledged, and DLQ message counts per subscription
- **Cleanup Jobs**: Automated cleanup of old acknowledged messages and stuck messages

## License

This project is licensed under the MIT License - see the LICENSE file for details.
