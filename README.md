# fastpubsub

A simple, yet powerful pub/sub (publish-subscribe) messaging system built with FastAPI and PostgreSQL. fastpubsub provides a RESTful API for managing topics, subscriptions, and messages with features like dead-letter queues (DLQ), message acknowledgments, and automatic cleanup.

## Features

- **Topics & Subscriptions**: Create and manage topics and subscriptions with ease
- **Message Publishing**: Publish messages to topics that are automatically distributed to subscriptions
- **Message Consumption**: Pull messages from subscriptions with consumer tracking
- **Message Acknowledgment**: Support for ACK/NACK operations to control message delivery
- **Dead Letter Queue (DLQ)**: Automatic handling of failed messages with reprocessing capabilities
- **Message Filtering**: Filter messages at subscription level
- **Delivery Guarantees**: Configurable retry logic with exponential backoff
- **Metrics**: Real-time subscription metrics
- **Automatic Cleanup**: Background tasks to clean up acknowledged and stuck messages
- **RESTful API**: Easy-to-use HTTP API with automatic documentation

## Docker Hub

This service is available as a Docker image on Docker Hub:

**Image**: [allisson/fastpubsub](https://hub.docker.com/r/allisson/fastpubsub)

```bash
docker pull allisson/fastpubsub
```

## Prerequisites

- Docker
- PostgreSQL database (version 12 or higher recommended)

## Configuration

fastpubsub is configured using environment variables. All configuration variables are prefixed with `fastpubsub_`.

### Required Configuration

| Variable | Description | Example |
|----------|-------------|---------|
| `fastpubsub_database_url` | PostgreSQL connection string | `postgresql+psycopg://user:password@host:5432/dbname` |

### Optional Configuration

#### Database Settings

| Variable | Description | Default |
|----------|-------------|---------|
| `fastpubsub_database_echo` | Enable SQL query logging | `false` |
| `fastpubsub_database_pool_size` | Database connection pool size | `5` |
| `fastpubsub_database_max_overflow` | Max overflow connections | `10` |
| `fastpubsub_database_pool_pre_ping` | Test connections before use | `true` |

#### Logging Settings

| Variable | Description | Default |
|----------|-------------|---------|
| `fastpubsub_log_level` | Logging level (debug, info, warning, error) | `info` |
| `fastpubsub_log_formatter` | Log format string | `asctime=%(asctime)s level=%(levelname)s pathname=%(pathname)s line=%(lineno)s message=%(message)s` |

#### API Server Settings

| Variable | Description | Default |
|----------|-------------|---------|
| `fastpubsub_api_debug` | Enable debug mode | `false` |
| `fastpubsub_api_host` | API server host | `0.0.0.0` |
| `fastpubsub_api_port` | API server port | `8000` |
| `fastpubsub_api_num_workers` | Number of worker processes | `1` |

#### Subscription Defaults

| Variable | Description | Default |
|----------|-------------|---------|
| `fastpubsub_subscription_max_attempts` | Maximum delivery attempts before DLQ | `5` |
| `fastpubsub_subscription_backoff_min_seconds` | Minimum backoff time between retries | `5` |
| `fastpubsub_subscription_backoff_max_seconds` | Maximum backoff time between retries | `300` |

#### Cleanup Settings

| Variable | Description | Default |
|----------|-------------|---------|
| `fastpubsub_cleanup_acked_messages_older_than_seconds` | Age threshold for cleaning acknowledged messages | `3600` (1 hour) |
| `fastpubsub_cleanup_stuck_messages_lock_timeout_seconds` | Timeout for stuck message locks | `60` |

## Running with Docker

### 1. Database Migration

Run database migrations to set up the required tables and functions:

```bash
docker run --rm \
  -e fastpubsub_database_url='postgresql+psycopg://user:password@host:5432/dbname' \
  allisson/fastpubsub db-migrate
```

### 2. Start the API Server

Run the API server to handle HTTP requests:

```bash
docker run -d \
  --name fastpubsub-server \
  -p 8000:8000 \
  -e fastpubsub_database_url='postgresql+psycopg://user:password@host:5432/dbname' \
  allisson/fastpubsub server
```

The API will be available at `http://localhost:8000`. API documentation is automatically generated and available at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### 3. Cleanup Acknowledged Messages

Run as a scheduled job (e.g., via cron) to remove old acknowledged messages:

```bash
docker run --rm \
  -e fastpubsub_database_url='postgresql+psycopg://user:password@host:5432/dbname' \
  -e fastpubsub_cleanup_acked_messages_older_than_seconds=3600 \
  allisson/fastpubsub cleanup_acked_messages
```

### 4. Cleanup Stuck Messages

Run as a scheduled job to release messages that have been locked for too long:

```bash
docker run --rm \
  -e fastpubsub_database_url='postgresql+psycopg://user:password@host:5432/dbname' \
  -e fastpubsub_cleanup_stuck_messages_lock_timeout_seconds=60 \
  allisson/fastpubsub cleanup_stuck_messages
```

## API Endpoints

### Topics

- **POST /topics** - Create a new topic
- **GET /topics** - List all topics (with pagination)
- **GET /topics/{id}** - Get a specific topic
- **DELETE /topics/{id}** - Delete a topic
- **POST /topics/{id}/messages** - Publish messages to a topic

### Subscriptions

- **POST /subscriptions** - Create a new subscription
- **GET /subscriptions** - List all subscriptions (with pagination)
- **GET /subscriptions/{id}** - Get a specific subscription
- **DELETE /subscriptions/{id}** - Delete a subscription
- **GET /subscriptions/{id}/messages** - Consume messages from a subscription
- **POST /subscriptions/{id}/acks** - Acknowledge messages
- **POST /subscriptions/{id}/nacks** - Negative acknowledge messages (retry)
- **GET /subscriptions/{id}/dlq** - List dead-letter queue messages
- **POST /subscriptions/{id}/dlq/reprocess** - Reprocess messages from DLQ
- **GET /subscriptions/{id}/metrics** - Get subscription metrics

## Usage Examples

### 1. Create a Topic

```bash
curl -X POST http://localhost:8000/topics \
  -H "Content-Type: application/json" \
  -d '{"id": "orders"}'
```

### 2. Create a Subscription

```bash
curl -X POST http://localhost:8000/subscriptions \
  -H "Content-Type: application/json" \
  -d '{
    "id": "order-processor",
    "topic_id": "orders",
    "max_delivery_attempts": 5,
    "backoff_min_seconds": 5,
    "backoff_max_seconds": 300
  }'
```

### 3. Publish Messages

```bash
curl -X POST http://localhost:8000/topics/orders/messages \
  -H "Content-Type: application/json" \
  -d '[
    {"order_id": "123", "amount": 99.99},
    {"order_id": "124", "amount": 149.99}
  ]'
```

### 4. Consume Messages

```bash
curl -X GET "http://localhost:8000/subscriptions/order-processor/messages?consumer_id=worker-1&batch_size=10"
```

### 5. Acknowledge Messages

```bash
curl -X POST http://localhost:8000/subscriptions/order-processor/acks \
  -H "Content-Type: application/json" \
  -d '["message-uuid-1", "message-uuid-2"]'
```

### 6. Get Subscription Metrics

```bash
curl -X GET http://localhost:8000/subscriptions/order-processor/metrics
```

## Architecture

fastpubsub uses PostgreSQL as both the data store and message queue, leveraging:
- **Tables**: For storing topics, subscriptions, and messages
- **Stored Procedures**: For atomic operations like message publishing and consumption
- **Row Locking**: For ensuring message delivery guarantees
- **Indexes**: For efficient message lookup and filtering

This approach provides:
- ACID guarantees for message delivery
- No additional infrastructure required beyond PostgreSQL
- Simplified deployment and operations
- Built-in persistence and durability

## License

This project is licensed under the MIT License - see the LICENSE file for details.
