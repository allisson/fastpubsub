# 🚀 fastpubsub

> Simple, reliable, and scalable pub/sub system based on FastAPI and PostgreSQL

[![Docker](https://img.shields.io/badge/docker-hub-blue)](https://hub.docker.com/r/allisson/fastpubsub)

## 📖 Overview

**fastpubsub** is a lightweight publish-subscribe messaging system built with FastAPI and PostgreSQL. It provides a simple HTTP API for message publishing and subscription management with powerful features like message filtering, delivery guarantees, dead-letter queues, and automatic retries with exponential backoff. The system is built with asyncio for efficient concurrent operations and uses SQLAlchemy's async engine with psycopg's native async support.

### ✨ Key Features

- 🎯 **Topic-based messaging** - Organize messages by topics
- 🔍 **Message filtering** - Subscribe to specific messages using JSON-based filters
- 🔄 **Automatic retries** - Configurable retry logic with exponential backoff
- 💀 **Dead Letter Queue (DLQ)** - Handle failed messages gracefully
- 📊 **Metrics & Monitoring** - Built-in subscription metrics and Prometheus support
- 🐳 **Docker-ready** - Easy deployment with Docker
- 🔒 **Reliable delivery** - Acknowledgment and negative-acknowledgment support
- 🧹 **Automatic cleanup** - Background jobs for message maintenance

## 🏗️ Architecture

fastpubsub uses PostgreSQL as its backend, leveraging stored procedures and JSONB capabilities for high-performance message routing and filtering. The system is built with asyncio for efficient concurrent operations, using SQLAlchemy's async engine with psycopg's native async support. The architecture consists of:

- **API Server**: Asynchronous RESTful HTTP API for all operations
- **Database**: PostgreSQL with custom functions for message management, accessed via async SQLAlchemy
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

### 🔐 Authentication Commands

#### Generate Secret Key

Generate a secure random secret key for authentication:

```bash
docker run --rm allisson/fastpubsub generate_secret_key
```

**Output:**
```
new_secret=a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6
```

Use this secret key to set the `FASTPUBSUB_AUTH_SECRET_KEY` environment variable.

#### Create Client

Create a new client with API credentials:

```bash
docker run --rm \
  -e FASTPUBSUB_DATABASE_URL='postgresql+psycopg://YOUR_USER:YOUR_PASSWORD@YOUR_HOST:5432/YOUR_DATABASE' \
  -e FASTPUBSUB_AUTH_ENABLED='true' \
  -e FASTPUBSUB_AUTH_SECRET_KEY='your-secret-key' \
  allisson/fastpubsub create_client "My Application" "*" true
```

**Arguments:**
1. Client name (e.g., "My Application")
2. Scopes (e.g., "*" for admin, or "topics:create topics:read")
3. Is active flag (true or false)

**Output:**
```
client_id=550e8400-e29b-41d4-a716-446655440000
client_secret=a1b2c3d4e5f6g7h8
```

Save the `client_id` and `client_secret` securely - the secret cannot be retrieved later.

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

### 🔐 Authentication Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `FASTPUBSUB_AUTH_ENABLED` | Enable authentication | `false` |
| `FASTPUBSUB_AUTH_SECRET_KEY` | Secret key for JWT signing (required if auth enabled) | `None` |
| `FASTPUBSUB_AUTH_ALGORITHM` | JWT signing algorithm | `HS256` |
| `FASTPUBSUB_AUTH_ACCESS_TOKEN_EXPIRE_MINUTES` | Access token expiration time in minutes | `30` |

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

### 🔐 Authentication

fastpubsub supports optional JWT-based authentication to secure API access. When authentication is disabled (default), all API endpoints are accessible without credentials. When enabled, clients must authenticate using OAuth2 client credentials flow.

#### Scopes

Authentication uses a scope-based permission system. Scopes can be global or object-specific:

**Global Scopes:**
- `*` - Admin mode, full access to all resources and operations
- `topics:create` - Can create new topics
- `topics:read` - Can list or get topics
- `topics:delete` - Can delete topics
- `topics:publish` - Can publish messages to topics
- `subscriptions:create` - Can create new subscriptions
- `subscriptions:read` - Can list or get subscriptions
- `subscriptions:delete` - Can delete subscriptions
- `subscriptions:consume` - Can consume messages from subscriptions
- `clients:create` - Can create new clients
- `clients:update` - Can update clients
- `clients:read` - Can list or get clients
- `clients:delete` - Can delete clients

**Object-Specific Scopes:**

You can restrict access to specific resources by appending the resource ID to the scope:
- `topics:publish:my-topic-id` - Can only publish to the topic with ID "my-topic-id"
- `subscriptions:consume:my-subscription` - Can only consume from the subscription with ID "my-subscription"

Multiple scopes can be combined, separated by spaces: `topics:create topics:read subscriptions:read`

#### Obtaining an Access Token

**Request:**
```http
POST /oauth/token
Content-Type: application/json

{
  "client_id": "550e8400-e29b-41d4-a716-446655440000",
  "client_secret": "a1b2c3d4e5f6g7h8"
}
```

**Response:** `201 Created`
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "Bearer",
  "expires_in": 1800,
  "scope": "topics:create topics:read"
}
```

#### Using the Access Token

Include the access token in the `Authorization` header for authenticated requests:

```bash
curl -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  http://localhost:8000/topics
```

### 👥 Clients

Clients represent applications or services that access the API. Each client has credentials (client_id and client_secret) and a set of scopes that define their permissions.

#### Create a Client

```http
POST /clients
Authorization: Bearer <token>
```

**Request Body:**
```json
{
  "name": "My Application",
  "scopes": "topics:create topics:read subscriptions:consume",
  "is_active": true
}
```

**Response:** `201 Created`
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "secret": "a1b2c3d4e5f6g7h8"
}
```

**Note:** The client secret is only returned once during creation. Store it securely.

#### Get a Client

```http
GET /clients/{id}
Authorization: Bearer <token>
```

**Response:** `200 OK`
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "My Application",
  "scopes": "topics:create topics:read",
  "is_active": true,
  "token_version": 1,
  "created_at": "2025-12-29T15:30:00Z",
  "updated_at": "2025-12-29T15:30:00Z"
}
```

#### List Clients

```http
GET /clients?offset=0&limit=10
Authorization: Bearer <token>
```

**Response:** `200 OK`
```json
{
  "data": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "name": "My Application",
      "scopes": "topics:create topics:read",
      "is_active": true,
      "token_version": 1,
      "created_at": "2025-12-29T15:30:00Z",
      "updated_at": "2025-12-29T15:30:00Z"
    }
  ]
}
```

#### Update a Client

```http
PUT /clients/{id}
Authorization: Bearer <token>
```

**Request Body:**
```json
{
  "name": "Updated Application Name",
  "scopes": "topics:read subscriptions:read",
  "is_active": true
}
```

**Response:** `200 OK`

**Note:** Updating a client increments its `token_version`, which invalidates all existing access tokens for that client.

#### Delete a Client

```http
DELETE /clients/{id}
Authorization: Bearer <token>
```

**Response:** `204 No Content`

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

### 📊 Prometheus Metrics

Get Prometheus-compatible metrics for monitoring:

```http
GET /metrics
```

**Response:** `200 OK` (Prometheus text format)
```
# HELP http_requests_total Total number of requests by method, path and status
# TYPE http_requests_total counter
http_requests_total{method="GET",path="/topics",status="200"} 42.0
...
```

The metrics endpoint exposes application metrics in Prometheus format, including:
- HTTP request counts and latencies
- Request duration histograms
- Active requests gauge
- And other standard FastAPI metrics

You can configure Prometheus to scrape this endpoint for monitoring and alerting.

## 💡 Usage Examples

### Example 1: Setting Up Authentication

```bash
# 1. Generate a secret key
docker run --rm allisson/fastpubsub generate_secret_key
# Output: new_secret=a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6

# 2. Start the server with authentication enabled
docker run -p 8000:8000 \
  -e FASTPUBSUB_DATABASE_URL='postgresql+psycopg://YOUR_USER:YOUR_PASSWORD@YOUR_HOST:5432/YOUR_DATABASE' \
  -e FASTPUBSUB_AUTH_ENABLED='true' \
  -e FASTPUBSUB_AUTH_SECRET_KEY='a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6' \
  allisson/fastpubsub server

# 3. Create an admin client (requires initial client creation via CLI or direct DB access)
docker run --rm \
  -e FASTPUBSUB_DATABASE_URL='postgresql+psycopg://YOUR_USER:YOUR_PASSWORD@YOUR_HOST:5432/YOUR_DATABASE' \
  -e FASTPUBSUB_AUTH_ENABLED='true' \
  -e FASTPUBSUB_AUTH_SECRET_KEY='a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6' \
  allisson/fastpubsub create_client "Admin Client" "*" true
# Output:
# client_id=550e8400-e29b-41d4-a716-446655440000
# client_secret=a1b2c3d4e5f6g7h8

# 4. Get an access token
curl -X POST http://localhost:8000/oauth/token \
  -H "Content-Type: application/json" \
  -d '{
    "client_id": "550e8400-e29b-41d4-a716-446655440000",
    "client_secret": "a1b2c3d4e5f6g7h8"
  }'
# Output: {"access_token": "eyJhbGc...", "token_type": "Bearer", "expires_in": 1800, "scope": "*"}

# 5. Use the token to access protected endpoints
TOKEN="eyJhbGc..."
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/topics
```

### Example 2: Simple Pub/Sub

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

### Example 3: Creating Clients with Different Scopes

```bash
# Assuming you have an admin token
ADMIN_TOKEN="eyJhbGc..."

# 1. Create a client that can only publish to a specific topic
curl -X POST http://localhost:8000/clients \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Publisher Service",
    "scopes": "topics:publish:notifications",
    "is_active": true
  }'

# 2. Create a client that can only consume from a specific subscription
curl -X POST http://localhost:8000/clients \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Consumer Service",
    "scopes": "subscriptions:consume:email-sender",
    "is_active": true
  }'

# 3. Create a client with multiple permissions
curl -X POST http://localhost:8000/clients \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Multi-Purpose Service",
    "scopes": "topics:create topics:read topics:publish subscriptions:create subscriptions:read",
    "is_active": true
  }'
```

### Example 4: Filtered Subscription

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

### Example 5: Complex Filter

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

### Example 6: Handling Failed Messages

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

### Example 7: Health Check Monitoring

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

### Example 8: Monitoring with Prometheus

```bash
# Access Prometheus metrics
curl "http://localhost:8000/metrics"
```

**Prometheus scrape configuration:**

```yaml
scrape_configs:
  - job_name: 'fastpubsub'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/metrics'
    scrape_interval: 15s
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

### 🔐 Security

- **Enable authentication**: Set `FASTPUBSUB_AUTH_ENABLED=true` for production deployments
- **Secure secret keys**: Generate strong secret keys using the `generate_secret_key` command
- **Principle of least privilege**: Grant clients only the scopes they need
- **Rotate credentials**: Regularly update client secrets by recreating clients
- **Token management**: Access tokens expire after 30 minutes by default (configurable)
- **Revoke access**: Update a client to increment its `token_version` and invalidate all existing tokens

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

### Authentication Issues

**401 Unauthorized / Invalid Token:**
- Verify that `FASTPUBSUB_AUTH_ENABLED=true` is set on the server
- Ensure you're using a valid access token obtained from `/oauth/token`
- Check that the token hasn't expired (default: 30 minutes)
- Verify the client is still active and hasn't been deleted or disabled
- If the client was updated, old tokens are invalidated - request a new token

**403 Forbidden / Insufficient Scope:**
- Check that the client has the required scope for the operation
- For object-specific operations, ensure the scope includes the resource ID
- Use `*` scope for admin/testing purposes (not recommended for production)
- Example: To publish to topic "events", client needs `topics:publish` or `topics:publish:events` scope

**Missing FASTPUBSUB_AUTH_SECRET_KEY:**
- Generate a secret key using `docker run --rm allisson/fastpubsub generate_secret_key`
- Set it as an environment variable: `FASTPUBSUB_AUTH_SECRET_KEY=your-generated-key`
- The same secret key must be used across all server instances

---

Made with ❤️ using FastAPI and PostgreSQL
