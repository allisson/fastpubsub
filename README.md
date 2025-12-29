# 🚀 fastpubsub

> Simple, reliable, and scalable pub/sub system based on FastAPI and PostgreSQL

[![Docker](https://img.shields.io/badge/docker-hub-blue)](https://hub.docker.com/r/allisson/fastpubsub)

## 📖 Overview

**fastpubsub** is a lightweight publish-subscribe messaging system built with FastAPI and PostgreSQL. It provides a simple HTTP API for message publishing and subscription management with powerful features like message filtering, delivery guarantees, dead-letter queues, and automatic retries with exponential backoff.

### ✨ Key Features

- 🎯 **Topic-based messaging** - Organize messages by topics
- 🔍 **Message filtering** - Subscribe to specific messages using JSON-based filters
- 🔄 **Automatic retries** - Configurable retry logic with exponential backoff
- 💀 **Dead Letter Queue (DLQ)** - Handle failed messages gracefully
- 📊 **Metrics & Monitoring** - Built-in subscription metrics
- 🐳 **Docker-ready** - Easy deployment with Docker
- 🔒 **Reliable delivery** - Acknowledgment and negative-acknowledgment support
- 🧹 **Automatic cleanup** - Background jobs for message maintenance

## 🏗️ Architecture

fastpubsub uses PostgreSQL as its backend, leveraging stored procedures and JSONB capabilities for high-performance message routing and filtering. The system consists of:

- **API Server**: RESTful HTTP API for all operations
- **Database**: PostgreSQL with custom functions for message management
- **Cleanup Workers**: Background jobs for message maintenance

## 🐳 Quick Start with Docker

All commands use the official Docker image from [Docker Hub](https://hub.docker.com/r/allisson/fastpubsub).

### 1️⃣ Prerequisites

- Docker installed
- PostgreSQL database (can also run in Docker)

### 2️⃣ Database Setup

First, you need to run database migrations:

```bash
docker run --rm \
  -e FASTPUBSUB_DATABASE_URL='postgresql+psycopg://YOUR_USER:YOUR_PASSWORD@YOUR_HOST:5432/YOUR_DATABASE' \
  allisson/fastpubsub db-migrate
```

### 3️⃣ Start the Server

Run the API server:

```bash
docker run -p 8000:8000 \
  -e FASTPUBSUB_DATABASE_URL='postgresql+psycopg://YOUR_USER:YOUR_PASSWORD@YOUR_HOST:5432/YOUR_DATABASE' \
  allisson/fastpubsub server
```

The API will be available at `http://localhost:8000`. You can access the interactive API documentation at `http://localhost:8000/docs`.

## 🎮 Docker Commands

### 🗄️ Database Migration

Apply database migrations to set up or upgrade the schema:

```bash
docker run --rm \
  -e FASTPUBSUB_DATABASE_URL='postgresql+psycopg://YOUR_USER:YOUR_PASSWORD@YOUR_HOST:5432/YOUR_DATABASE' \
  allisson/fastpubsub db-migrate
```

This command creates all necessary tables, indexes, and stored procedures.

### 🌐 API Server

Start the HTTP API server:

```bash
docker run -p 8000:8000 \
  -e FASTPUBSUB_DATABASE_URL='postgresql+psycopg://YOUR_USER:YOUR_PASSWORD@YOUR_HOST:5432/YOUR_DATABASE' \
  allisson/fastpubsub server
```

The server runs with Gunicorn and Uvicorn workers for production-grade performance.

### 🧹 Cleanup Acked Messages

Remove acknowledged messages older than a specified threshold:

```bash
docker run --rm \
  -e FASTPUBSUB_DATABASE_URL='postgresql+psycopg://YOUR_USER:YOUR_PASSWORD@YOUR_HOST:5432/YOUR_DATABASE' \
  allisson/fastpubsub cleanup_acked_messages
```

This removes acked messages to prevent database bloat. By default, messages older than 1 hour (3600 seconds) are deleted.

### 🔓 Cleanup Stuck Messages

Release messages that are stuck in "delivered" state (locked but not acked/nacked):

```bash
docker run --rm \
  -e FASTPUBSUB_DATABASE_URL='postgresql+psycopg://YOUR_USER:YOUR_PASSWORD@YOUR_HOST:5432/YOUR_DATABASE' \
  allisson/fastpubsub cleanup_stuck_messages
```

This handles cases where a consumer crashed without acknowledging messages. By default, messages locked for more than 60 seconds are released.

### 💡 Running as Cron Jobs

It's recommended to run cleanup commands periodically using cron or a scheduler like Kubernetes CronJob:

```bash
# Example: Run cleanup_acked_messages every hour
0 * * * * docker run --rm -e FASTPUBSUB_DATABASE_URL='postgresql+psycopg://YOUR_USER:YOUR_PASSWORD@YOUR_HOST:5432/YOUR_DATABASE' allisson/fastpubsub cleanup_acked_messages

# Example: Run cleanup_stuck_messages every 5 minutes
*/5 * * * * docker run --rm -e FASTPUBSUB_DATABASE_URL='postgresql+psycopg://YOUR_USER:YOUR_PASSWORD@YOUR_HOST:5432/YOUR_DATABASE' allisson/fastpubsub cleanup_stuck_messages
```

## ⚙️ Configuration

Configure fastpubsub using environment variables. All variables are prefixed with `FASTPUBSUB_`.

### 🗄️ Database Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `FASTPUBSUB_DATABASE_URL` | PostgreSQL connection URL (required) | - |
| `FASTPUBSUB_DATABASE_ECHO` | Enable SQLAlchemy query logging | `false` |
| `FASTPUBSUB_DATABASE_POOL_SIZE` | Connection pool size | `5` |
| `FASTPUBSUB_DATABASE_MAX_OVERFLOW` | Max overflow connections | `10` |
| `FASTPUBSUB_DATABASE_POOL_PRE_PING` | Test connections before use | `true` |

### 📝 Logging Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `FASTPUBSUB_LOG_LEVEL` | Log level (debug, info, warning, error) | `info` |
| `FASTPUBSUB_LOG_FORMATTER` | Log format string | See below |

Default log format:
```
asctime=%(asctime)s level=%(levelname)s pathname=%(pathname)s line=%(lineno)s message=%(message)s
```

### 🔔 Subscription Defaults

| Variable | Description | Default |
|----------|-------------|---------|
| `FASTPUBSUB_SUBSCRIPTION_MAX_ATTEMPTS` | Maximum delivery attempts before DLQ | `5` |
| `FASTPUBSUB_SUBSCRIPTION_BACKOFF_MIN_SECONDS` | Minimum retry delay | `5` |
| `FASTPUBSUB_SUBSCRIPTION_BACKOFF_MAX_SECONDS` | Maximum retry delay | `300` |

### 🌐 API Server Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `FASTPUBSUB_API_DEBUG` | Enable debug mode | `false` |
| `FASTPUBSUB_API_HOST` | Server bind host | `0.0.0.0` |
| `FASTPUBSUB_API_PORT` | Server port | `8000` |
| `FASTPUBSUB_API_NUM_WORKERS` | Number of Gunicorn workers | `1` |

### 🧹 Cleanup Workers Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `FASTPUBSUB_CLEANUP_ACKED_MESSAGES_OLDER_THAN_SECONDS` | Delete acked messages older than (seconds) | `3600` |
| `FASTPUBSUB_CLEANUP_STUCK_MESSAGES_LOCK_TIMEOUT_SECONDS` | Release messages locked longer than (seconds) | `60` |

### 📋 Example Docker Run with Configuration

```bash
docker run -p 8000:8000 \
  -e FASTPUBSUB_DATABASE_URL='postgresql+psycopg://YOUR_USER:YOUR_PASSWORD@YOUR_HOST:5432/YOUR_DATABASE' \
  -e FASTPUBSUB_LOG_LEVEL='info' \
  -e FASTPUBSUB_API_NUM_WORKERS='4' \
  -e FASTPUBSUB_SUBSCRIPTION_MAX_ATTEMPTS='10' \
  allisson/fastpubsub server
```

## 📡 API Reference

### 🎯 Topics

Topics are channels where messages are published.

#### Create a Topic

```http
POST /topics
```

**Request Body:**
```json
{
  "id": "user-events"
}
```

**Response:** `201 Created`
```json
{
  "id": "user-events",
  "created_at": "2025-12-29T15:30:00Z"
}
```

#### Get a Topic

```http
GET /topics/{id}
```

**Response:** `200 OK`

#### List Topics

```http
GET /topics?offset=0&limit=10
```

**Response:** `200 OK`
```json
{
  "data": [
    {
      "id": "user-events",
      "created_at": "2025-12-29T15:30:00Z"
    }
  ]
}
```

#### Delete a Topic

```http
DELETE /topics/{id}
```

**Response:** `204 No Content`

#### Publish Messages

```http
POST /topics/{id}/messages
```

**Request Body:**
```json
[
  {
    "event": "user.created",
    "user_id": "123",
    "country": "BR"
  },
  {
    "event": "user.updated",
    "user_id": "456",
    "country": "US"
  }
]
```

**Response:** `204 No Content`

### 📬 Subscriptions

Subscriptions receive messages from topics, optionally filtered.

#### Create a Subscription

```http
POST /subscriptions
```

**Request Body:**
```json
{
  "id": "user-processor",
  "topic_id": "user-events",
  "filter": {"country": ["BR", "US"]},
  "max_delivery_attempts": 5,
  "backoff_min_seconds": 5,
  "backoff_max_seconds": 300
}
```

**Response:** `201 Created`

**Filter Examples:**
- `{"country": ["BR", "US"]}` - Messages where country is BR or US
- `{"event": ["user.created"]}` - Only user.created events
- `{"premium": [true]}` - Only premium users
- `{}` or `null` - No filtering, receive all messages

#### Get a Subscription

```http
GET /subscriptions/{id}
```

**Response:** `200 OK`

#### List Subscriptions

```http
GET /subscriptions?offset=0&limit=10
```

**Response:** `200 OK`

#### Delete a Subscription

```http
DELETE /subscriptions/{id}
```

**Response:** `204 No Content`

### 📨 Consuming Messages

#### Consume Messages

Retrieve messages from a subscription:

```http
GET /subscriptions/{id}/messages?consumer_id=worker-1&batch_size=10
```

**Response:** `200 OK`
```json
{
  "data": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "subscription_id": "user-processor",
      "payload": {
        "event": "user.created",
        "user_id": "123",
        "country": "BR"
      },
      "delivery_attempts": 1,
      "created_at": "2025-12-29T15:30:00Z"
    }
  ]
}
```

**Parameters:**
- `consumer_id`: Unique identifier for the consumer (required)
- `batch_size`: Number of messages to retrieve (default: 10, max: 100)

### ✅ Acknowledging Messages

#### Acknowledge (ACK) Messages

Mark messages as successfully processed:

```http
POST /subscriptions/{id}/acks
```

**Request Body:**
```json
[
  "550e8400-e29b-41d4-a716-446655440000",
  "660e8400-e29b-41d4-a716-446655440001"
]
```

**Response:** `204 No Content`

#### Negative Acknowledge (NACK) Messages

Mark messages for retry:

```http
POST /subscriptions/{id}/nacks
```

**Request Body:**
```json
[
  "550e8400-e29b-41d4-a716-446655440000"
]
```

**Response:** `204 No Content`

NACKed messages will be retried with exponential backoff until `max_delivery_attempts` is reached.

### 💀 Dead Letter Queue (DLQ)

Messages that exceed `max_delivery_attempts` are moved to the DLQ.

#### List DLQ Messages

```http
GET /subscriptions/{id}/dlq?offset=0&limit=10
```

**Response:** `200 OK`

#### Reprocess DLQ Messages

Move messages back to the subscription queue for reprocessing:

```http
POST /subscriptions/{id}/dlq/reprocess
```

**Request Body:**
```json
[
  "550e8400-e29b-41d4-a716-446655440000"
]
```

**Response:** `204 No Content`

### 📊 Metrics

#### Get Subscription Metrics

```http
GET /subscriptions/{id}/metrics
```

**Response:** `200 OK`
```json
{
  "subscription_id": "user-processor",
  "available": 150,
  "delivered": 25,
  "acked": 1000,
  "dlq": 5
}
```

**Metrics:**
- `available`: Messages ready to be consumed
- `delivered`: Messages currently locked by consumers
- `acked`: Total acknowledged messages
- `dlq`: Messages in the dead letter queue

### 🏥 Health Checks

Health check endpoints are useful for monitoring and orchestration systems like Kubernetes.

#### Liveness Probe

Check if the application is alive:

```http
GET /liveness
```

**Response:** `200 OK`
```json
{
  "status": "alive"
}
```

The liveness endpoint always returns a successful response if the application is running. Use this endpoint to determine if the application needs to be restarted.

#### Readiness Probe

Check if the application is ready to handle requests:

```http
GET /readiness
```

**Response:** `200 OK`
```json
{
  "status": "ready"
}
```

**Error Response:** `503 Service Unavailable`
```json
{
  "detail": "database is down"
}
```

The readiness endpoint checks if the database connection is healthy. Use this endpoint to determine if the application should receive traffic.

## 💡 Usage Examples

### Example 1: Simple Pub/Sub

```bash
# 1. Create a topic
curl -X POST http://localhost:8000/topics \
  -H "Content-Type: application/json" \
  -d '{"id": "notifications"}'

# 2. Create a subscription
curl -X POST http://localhost:8000/subscriptions \
  -H "Content-Type: application/json" \
  -d '{
    "id": "email-sender",
    "topic_id": "notifications"
  }'

# 3. Publish messages
curl -X POST http://localhost:8000/topics/notifications/messages \
  -H "Content-Type: application/json" \
  -d '[
    {"type": "email", "to": "user@example.com", "subject": "Welcome!"}
  ]'

# 4. Consume messages
curl "http://localhost:8000/subscriptions/email-sender/messages?consumer_id=worker-1&batch_size=10"

# 5. Acknowledge messages
curl -X POST http://localhost:8000/subscriptions/email-sender/acks \
  -H "Content-Type: application/json" \
  -d '["550e8400-e29b-41d4-a716-446655440000"]'
```

### Example 2: Filtered Subscription

```bash
# Create a subscription that only receives messages from BR and US
curl -X POST http://localhost:8000/subscriptions \
  -H "Content-Type: application/json" \
  -d '{
    "id": "regional-processor",
    "topic_id": "user-events",
    "filter": {"country": ["BR", "US"]}
  }'

# Publish messages - only BR/US messages will be routed to this subscription
curl -X POST http://localhost:8000/topics/user-events/messages \
  -H "Content-Type: application/json" \
  -d '[
    {"event": "user.login", "user_id": "1", "country": "BR"},
    {"event": "user.login", "user_id": "2", "country": "JP"},
    {"event": "user.login", "user_id": "3", "country": "US"}
  ]'
```

The subscription will only receive messages with `country` set to "BR" or "US" (messages for user 1 and 3, not user 2).

### Example 3: Complex Filter

The filter feature uses a simple JSON style where keys are field names and values are arrays of acceptable values:

```json
{
  "filter": {
    "event_type": ["order.created", "order.updated"],
    "priority": ["high", "critical"],
    "region": ["us-east", "us-west"]
  }
}
```

This filter matches messages that have:
- `event_type` equal to "order.created" OR "order.updated"
- AND `priority` equal to "high" OR "critical"
- AND `region` equal to "us-east" OR "us-west"

### Example 4: Handling Failed Messages

```bash
# Check metrics to see if there are DLQ messages
curl "http://localhost:8000/subscriptions/email-sender/metrics"

# List DLQ messages
curl "http://localhost:8000/subscriptions/email-sender/dlq"

# Reprocess DLQ messages after fixing the issue
curl -X POST http://localhost:8000/subscriptions/email-sender/dlq/reprocess \
  -H "Content-Type: application/json" \
  -d '["550e8400-e29b-41d4-a716-446655440000"]'
```

### Example 5: Health Check Monitoring

```bash
# Check if the application is alive (for restart decisions)
curl "http://localhost:8000/liveness"

# Check if the application is ready to serve traffic
curl "http://localhost:8000/readiness"
```

**Kubernetes example configuration:**

```yaml
livenessProbe:
  httpGet:
    path: /liveness
    port: 8000
  initialDelaySeconds: 30
  periodSeconds: 10

readinessProbe:
  httpGet:
    path: /readiness
    port: 8000
  initialDelaySeconds: 10
  periodSeconds: 5
```

## 🔄 Message Flow

1. **Publish**: Messages are published to a topic
2. **Route**: Messages are routed to all subscriptions for that topic
3. **Filter**: Subscriptions with filters only receive matching messages
4. **Consume**: Consumers fetch messages in batches
5. **Process**: Consumer processes the message
6. **ACK/NACK**: Consumer acknowledges success or requests retry
7. **Retry**: Failed messages are retried with exponential backoff
8. **DLQ**: Messages exceeding max attempts move to the dead letter queue

## 🎯 Best Practices

### 🔧 Consumer Implementation

- **Always acknowledge messages**: Use ACK for success, NACK for retriable failures
- **Use unique consumer IDs**: Helps with debugging and metrics
- **Handle idempotency**: Messages may be delivered more than once
- **Implement timeouts**: Don't let message processing hang indefinitely
- **Monitor DLQ**: Regularly check and handle dead-letter messages

### 🏃 Performance Tips

- **Batch consumption**: Use appropriate `batch_size` for your workload
- **Multiple workers**: Run multiple consumers with different `consumer_id`
- **Optimize filters**: More specific filters reduce unnecessary message delivery
- **Regular cleanup**: Schedule cleanup jobs to maintain database performance
- **Connection pooling**: Configure appropriate pool sizes for your load

### 🔒 Reliability

- **Run cleanup workers**: Essential for production deployments
- **Monitor metrics**: Track available, delivered, acked, and DLQ counts
- **Set appropriate timeouts**: Configure backoff settings based on your use case
- **Database backups**: Regular PostgreSQL backups are crucial

## 📚 API Documentation

Once the server is running, you can access the interactive API documentation:

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit issues and pull requests.

## 🐛 Troubleshooting

### Connection Issues

If you're having trouble connecting to the database from Docker:
- Use `host.docker.internal` instead of `localhost` when running on Docker Desktop
- Ensure your PostgreSQL allows connections from Docker networks
- Check firewall rules if using a remote database

### Messages Not Being Consumed

- Verify the subscription exists and is properly configured
- Check if filters are too restrictive
- Look at metrics to see message counts
- Ensure cleanup_stuck_messages is running if consumers crashed

### High Message Latency

- Increase the number of API workers (`FASTPUBSUB_API_NUM_WORKERS`)
- Run multiple consumer instances
- Check database connection pool settings
- Review and optimize your subscription filters

---

Made with ❤️ using FastAPI and PostgreSQL
