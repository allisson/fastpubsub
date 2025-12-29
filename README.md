# fastpubsub

A simple, reliable, and scalable pub/sub (publish-subscribe) messaging system built with FastAPI and PostgreSQL.

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Database Setup](#database-setup)
- [Running the Server](#running-the-server)
- [API Documentation](#api-documentation)
- [Usage Examples](#usage-examples)
- [Maintenance Operations](#maintenance-operations)
- [Development](#development)
- [Testing](#testing)
- [Docker Deployment](#docker-deployment)
- [License](#license)

## Overview

fastpubsub is a lightweight pub/sub messaging system that leverages PostgreSQL for reliable message storage and delivery. It provides a RESTful API built with FastAPI, making it easy to integrate into your applications.

The system supports:
- **Topics**: Channels for publishing messages
- **Subscriptions**: Consumers that receive messages from topics
- **Message filtering**: Route messages based on payload attributes
- **Delivery guarantees**: At-least-once delivery with configurable retry logic
- **Dead Letter Queue (DLQ)**: Handle messages that fail processing
- **Message acknowledgment**: ACK/NACK support with exponential backoff

## Features

- 🚀 **Fast and Async**: Built on FastAPI with high-performance async operations
- 🔒 **Reliable**: PostgreSQL-backed storage ensures message durability
- 🎯 **Message Filtering**: Subscribe to specific messages based on payload attributes
- 🔄 **Retry Logic**: Configurable delivery attempts with exponential backoff
- 💀 **Dead Letter Queue**: Isolate and reprocess failed messages
- 📊 **Metrics**: Track message states (available, delivered, acked, dlq)
- 🔐 **Concurrency Safe**: Uses PostgreSQL's `SELECT FOR UPDATE SKIP LOCKED` for safe concurrent message consumption
- 🐳 **Docker Ready**: Includes Dockerfile for easy deployment
- 🧹 **Cleanup Operations**: Built-in commands for message cleanup and maintenance

## Architecture

### Core Components

1. **Topics**: Named channels where messages are published
2. **Subscriptions**: Link between topics and consumers with filtering rules
3. **Messages**: JSON payloads distributed to subscriptions
4. **Consumers**: Applications that pull messages from subscriptions

### Message Flow

```
Publisher → Topic → Subscription(s) → Consumer(s) → ACK/NACK
                         ↓
                    (filtered messages)
                         ↓
                    Message Queue
                         ↓
                   Consumer pulls → Process → ACK (success) / NACK (retry)
                         ↓
                    (after max retries)
                         ↓
                  Dead Letter Queue (DLQ)
```

### Database Schema

The system uses three main tables:
- **topics**: Stores topic definitions
- **subscriptions**: Maps topics to consumers with filtering and retry settings
- **subscription_messages**: Holds messages with delivery state and metadata

PostgreSQL stored procedures handle:
- `publish_messages`: Distribute messages to subscriptions with filtering
- `consume_messages`: Atomically lock and deliver messages to consumers
- `ack_messages`: Mark messages as successfully processed
- `nack_messages`: Return messages to queue or move to DLQ
- `subscription_metrics`: Track message states per subscription

## Prerequisites

- **Python**: 3.14 or higher
- **PostgreSQL**: 14 or higher
- **uv**: Python package manager (recommended) or pip

## Installation

### Using uv (Recommended)

```bash
# Clone the repository
git clone https://github.com/allisson/fastpubsub.git
cd fastpubsub

# Install dependencies
uv sync

# Or for development
uv sync --all-groups
```

### Using pip

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -e .
```

## Configuration

fastpubsub uses environment variables for configuration. Copy the sample environment file:

```bash
cp env.sample .env
```

### Environment Variables

All variables use the `fastpubsub_` prefix:

#### Database Settings
```bash
fastpubsub_database_url='postgresql+psycopg://user:password@localhost:5432/dbname'
fastpubsub_database_echo='false'              # Log SQL queries
fastpubsub_database_pool_size='5'             # Connection pool size
fastpubsub_database_max_overflow='10'         # Max overflow connections
fastpubsub_database_pool_pre_ping='true'      # Verify connections
```

#### API Settings
```bash
fastpubsub_api_debug='false'                  # Debug mode
fastpubsub_api_host='0.0.0.0'                 # Listen address
fastpubsub_api_port='8000'                    # Listen port
fastpubsub_api_num_workers='1'                # Gunicorn workers
```

#### Subscription Defaults
```bash
fastpubsub_subscription_max_attempts='5'              # Max delivery attempts before DLQ
fastpubsub_subscription_backoff_min_seconds='5'       # Initial backoff
fastpubsub_subscription_backoff_max_seconds='300'     # Max backoff (5 min)
```

#### Cleanup Settings
```bash
fastpubsub_cleanup_acked_messages_older_than_seconds='3600'     # Clean acked messages after 1 hour
fastpubsub_cleanup_stuck_messages_lock_timeout_seconds='60'     # Release stuck messages after 60s
```

#### Logging
```bash
fastpubsub_log_level='info'                   # Log level: debug, info, warning, error
```

## Database Setup

### Start PostgreSQL (Docker)

```bash
make start-postgresql
```

This starts a PostgreSQL container with default credentials.

### Run Migrations

```bash
make run-db-migrate
```

Or using the CLI directly:
```bash
uv run python fastpubsub/main.py db-migrate
```

### Stop PostgreSQL

```bash
make remove-postgresql
```

## Running the Server

### Using Make

```bash
make run-server
```

### Using CLI

```bash
uv run python fastpubsub/main.py server
```

The API will be available at `http://localhost:8000` (or your configured host/port).

### API Documentation

Once the server is running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## API Documentation

### Topics

#### Create Topic
```http
POST /topics
Content-Type: application/json

{
  "id": "my-topic"
}
```

#### Get Topic
```http
GET /topics/{id}
```

#### List Topics
```http
GET /topics?offset=0&limit=10
```

#### Delete Topic
```http
DELETE /topics/{id}
```

#### Publish Messages
```http
POST /topics/{id}/messages
Content-Type: application/json

[
  {"key": "value", "data": "message1"},
  {"key": "value", "data": "message2"}
]
```

### Subscriptions

#### Create Subscription
```http
POST /subscriptions
Content-Type: application/json

{
  "id": "my-subscription",
  "topic_id": "my-topic",
  "filter": {
    "event_type": ["order.created", "order.updated"]
  },
  "max_delivery_attempts": 5,
  "backoff_min_seconds": 5,
  "backoff_max_seconds": 300
}
```

**Filter Format**: The filter is a JSON object where keys are payload fields and values are arrays of allowed values. Messages are only delivered if all filter criteria match.

#### Get Subscription
```http
GET /subscriptions/{id}
```

#### List Subscriptions
```http
GET /subscriptions?offset=0&limit=10
```

#### Delete Subscription
```http
DELETE /subscriptions/{id}
```

#### Consume Messages
```http
GET /subscriptions/{id}/messages?consumer_id=consumer-1&batch_size=10
```

Returns messages locked to the consumer. The consumer must ACK or NACK each message.

#### Acknowledge Messages (ACK)
```http
POST /subscriptions/{id}/acks
Content-Type: application/json

[
  "message-uuid-1",
  "message-uuid-2"
]
```

#### Negative Acknowledge (NACK)
```http
POST /subscriptions/{id}/nacks
Content-Type: application/json

[
  "message-uuid-1",
  "message-uuid-2"
]
```

Messages will be retried with exponential backoff or moved to DLQ after max attempts.

#### List Dead Letter Queue
```http
GET /subscriptions/{id}/dlq?offset=0&limit=10
```

#### Reprocess DLQ Messages
```http
POST /subscriptions/{id}/dlq/reprocess
Content-Type: application/json

[
  "message-uuid-1",
  "message-uuid-2"
]
```

#### Get Subscription Metrics
```http
GET /subscriptions/{id}/metrics
```

Returns:
```json
{
  "subscription_id": "my-subscription",
  "available": 100,
  "delivered": 5,
  "acked": 1000,
  "dlq": 2
}
```

## Usage Examples

### Example 1: Basic Pub/Sub

```bash
# Create a topic
curl -X POST http://localhost:8000/topics \
  -H "Content-Type: application/json" \
  -d '{"id": "orders"}'

# Create a subscription
curl -X POST http://localhost:8000/subscriptions \
  -H "Content-Type: application/json" \
  -d '{
    "id": "order-processor",
    "topic_id": "orders"
  }'

# Publish messages
curl -X POST http://localhost:8000/topics/orders/messages \
  -H "Content-Type: application/json" \
  -d '[
    {"order_id": "1001", "amount": 99.99},
    {"order_id": "1002", "amount": 149.99}
  ]'

# Consume messages
curl "http://localhost:8000/subscriptions/order-processor/messages?consumer_id=worker-1&batch_size=10"

# Acknowledge messages (replace with actual UUIDs from consume response)
curl -X POST http://localhost:8000/subscriptions/order-processor/acks \
  -H "Content-Type: application/json" \
  -d '["uuid-1", "uuid-2"]'
```

### Example 2: Filtered Subscription

```bash
# Create topic
curl -X POST http://localhost:8000/topics \
  -H "Content-Type: application/json" \
  -d '{"id": "events"}'

# Create filtered subscription (only receive specific event types)
curl -X POST http://localhost:8000/subscriptions \
  -H "Content-Type: application/json" \
  -d '{
    "id": "payment-events",
    "topic_id": "events",
    "filter": {
      "event_type": ["payment.succeeded", "payment.failed"]
    }
  }'

# Publish various events
curl -X POST http://localhost:8000/topics/events/messages \
  -H "Content-Type: application/json" \
  -d '[
    {"event_type": "payment.succeeded", "amount": 100},
    {"event_type": "user.login", "user_id": "123"},
    {"event_type": "payment.failed", "reason": "insufficient_funds"}
  ]'

# Only payment events will be delivered to payment-events subscription
```

### Example 3: Handling DLQ

```bash
# List messages in DLQ
curl "http://localhost:8000/subscriptions/order-processor/dlq?limit=10"

# Reprocess specific DLQ messages
curl -X POST http://localhost:8000/subscriptions/order-processor/dlq/reprocess \
  -H "Content-Type: application/json" \
  -d '["uuid-1", "uuid-2"]'

# Check metrics
curl "http://localhost:8000/subscriptions/order-processor/metrics"
```

## Maintenance Operations

### Cleanup Acknowledged Messages

Remove old acknowledged messages to free database space:

```bash
uv run python fastpubsub/main.py cleanup_acked_messages
```

This deletes messages acknowledged more than 1 hour ago (configurable).

### Cleanup Stuck Messages

Release messages that have been locked too long (consumer crashed):

```bash
uv run python fastpubsub/main.py cleanup_stuck_messages
```

This unlocks messages locked for more than 60 seconds (configurable).

### Scheduling Cleanup

Run these commands periodically (e.g., via cron or Kubernetes CronJob):

```bash
# Example crontab
0 * * * * cd /path/to/fastpubsub && uv run python fastpubsub/main.py cleanup_acked_messages
*/5 * * * * cd /path/to/fastpubsub && uv run python fastpubsub/main.py cleanup_stuck_messages
```

## Development

### Setup Development Environment

```bash
# Install with dev dependencies
uv sync --all-groups

# Install pre-commit hooks
uv run pre-commit install
```

### Code Quality

```bash
# Run linter
make lint

# Auto-fix issues
uv run pre-commit run --all-files
```

### Project Structure

```
fastpubsub/
├── fastpubsub/
│   ├── __init__.py
│   ├── api.py              # FastAPI routes and app
│   ├── config.py           # Configuration settings
│   ├── database.py         # SQLAlchemy models and session
│   ├── exceptions.py       # Custom exceptions
│   ├── logger.py           # Logging configuration
│   ├── main.py             # CLI entry point
│   ├── models.py           # Pydantic models
│   └── services.py         # Business logic
├── migrations/             # Alembic database migrations
├── tests/                  # Test suite
├── Dockerfile              # Container image
├── Makefile                # Common commands
├── pyproject.toml          # Project metadata and dependencies
└── README.md               # This file
```

## Testing

### Run All Tests

```bash
make test
```

Or with coverage:
```bash
uv run pytest -v --cov=fastpubsub --cov-report=term-missing
```

### Run Specific Tests

```bash
# Test API endpoints
uv run pytest tests/test_api.py -v

# Test services
uv run pytest tests/test_services.py -v
```

### Test Requirements

Tests require a running PostgreSQL database. The test suite uses the database configuration from your `.env` file.

## Docker Deployment

### Build Image

```bash
make docker-build
```

Or:
```bash
docker build -t fastpubsub .
```

### Run with Docker Compose

Create a `docker-compose.yml`:

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:14-alpine
    environment:
      POSTGRES_DB: fastpubsub
      POSTGRES_USER: fastpubsub
      POSTGRES_PASSWORD: fastpubsub
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  fastpubsub:
    image: fastpubsub
    command: server
    environment:
      fastpubsub_database_url: postgresql+psycopg://fastpubsub:fastpubsub@postgres:5432/fastpubsub
      fastpubsub_api_host: 0.0.0.0
      fastpubsub_api_port: 8000
    ports:
      - "8000:8000"
    depends_on:
      - postgres

  # Run migrations
  fastpubsub-migrate:
    image: fastpubsub
    command: db-migrate
    environment:
      fastpubsub_database_url: postgresql+psycopg://fastpubsub:fastpubsub@postgres:5432/fastpubsub
    depends_on:
      - postgres

volumes:
  postgres_data:
```

Run:
```bash
docker-compose up -d
```

### Production Deployment

For production:
1. Use PostgreSQL with proper backups and replication
2. Set `fastpubsub_api_num_workers` based on CPU cores
3. Configure connection pooling appropriately
4. Set up monitoring and alerting
5. Schedule cleanup operations
6. Use a reverse proxy (nginx, traefik) for TLS termination

## License

This project is licensed under the MIT License - see the LICENSE file for details.
