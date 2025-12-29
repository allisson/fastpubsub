# 🚀 FastPubSub

> A simple, fast, and reliable pub/sub system based on FastAPI and PostgreSQL

FastPubSub is a lightweight message queue and pub/sub system that leverages the power of PostgreSQL for reliable message delivery. Built with modern Python technologies, it provides a simple HTTP API for publishing and consuming messages with guaranteed delivery semantics.

## ✨ Features

- 📬 **Topic-based messaging** - Create topics and publish messages to multiple subscribers
- 🔄 **Multiple subscriptions** - Subscribe to topics with independent message queues
- 🎯 **Message filtering** - Filter messages based on JSON payload attributes
- 🔁 **Automatic retries** - Configurable retry logic with exponential backoff
- 💀 **Dead Letter Queue (DLQ)** - Automatic handling of failed messages
- 📊 **Metrics** - Track message status and subscription health
- 🔒 **Message locking** - Prevent duplicate processing with consumer locks
- ⚡ **High performance** - Built on FastAPI and PostgreSQL for speed and reliability
- 🐳 **Docker ready** - Available as a pre-built Docker image

## 🏗️ Architecture

FastPubSub uses PostgreSQL as its backbone for message storage and delivery guarantees. The system consists of:

- **API Server**: RESTful HTTP API for all operations
- **Topics**: Named channels for publishing messages
- **Subscriptions**: Consumers that receive messages from topics
- **Messages**: JSON payloads with delivery tracking
- **Background Workers**: Cleanup processes for maintenance

### Message States

Messages flow through different states in their lifecycle:

1. **Available** - Ready to be consumed
2. **Delivered** - Locked by a consumer for processing
3. **Acked** - Successfully processed (ready for cleanup)
4. **DLQ** - Failed after max retry attempts

## 🐳 Docker Hub

FastPubSub is available as a Docker image on Docker Hub:

**Image**: [`allisson/fastpubsub`](https://hub.docker.com/r/allisson/fastpubsub)

Pull the latest version:
```bash
docker pull allisson/fastpubsub
```

## 📋 Prerequisites

- 🐘 **PostgreSQL 12+** - A running PostgreSQL database instance
- 🐳 **Docker** - For running FastPubSub containers

## ⚙️ Configuration

FastPubSub is configured through environment variables. All variables are prefixed with `fastpubsub_`.

### Required Configuration

| Variable | Description | Example |
|----------|-------------|---------|
| `fastpubsub_database_url` | PostgreSQL connection URL | `postgresql+psycopg://user:pass@host:5432/db` |

### Optional Configuration

#### Database Settings
| Variable | Default | Description |
|----------|---------|-------------|
| `fastpubsub_database_echo` | `false` | Enable SQL query logging |
| `fastpubsub_database_pool_size` | `5` | Connection pool size |
| `fastpubsub_database_max_overflow` | `10` | Max overflow connections |
| `fastpubsub_database_pool_pre_ping` | `true` | Test connections before use |

#### Logging Settings
| Variable | Default | Description |
|----------|---------|-------------|
| `fastpubsub_log_level` | `info` | Log level (debug, info, warning, error) |
| `fastpubsub_log_formatter` | Custom format | Log message format |

#### Subscription Defaults
| Variable | Default | Description |
|----------|---------|-------------|
| `fastpubsub_subscription_max_attempts` | `5` | Max delivery attempts before DLQ |
| `fastpubsub_subscription_backoff_min_seconds` | `5` | Minimum retry backoff time |
| `fastpubsub_subscription_backoff_max_seconds` | `300` | Maximum retry backoff time |

#### API Server Settings
| Variable | Default | Description |
|----------|---------|-------------|
| `fastpubsub_api_debug` | `false` | Enable debug mode |
| `fastpubsub_api_host` | `0.0.0.0` | API server bind address |
| `fastpubsub_api_port` | `8000` | API server port |
| `fastpubsub_api_num_workers` | `1` | Number of worker processes |

#### Cleanup Worker Settings
| Variable | Default | Description |
|----------|---------|-------------|
| `fastpubsub_cleanup_acked_messages_older_than_seconds` | `3600` | Delete acked messages older than (seconds) |
| `fastpubsub_cleanup_stuck_messages_lock_timeout_seconds` | `60` | Release message locks older than (seconds) |

## 🚀 Running with Docker

### 1️⃣ Initialize the Database

Before first use, run database migrations to create the required tables:

```bash
docker run --rm \
  -e fastpubsub_database_url='postgresql+psycopg://user:password@host:5432/fastpubsub' \
  allisson/fastpubsub db-migrate
```

### 2️⃣ Start the API Server

Run the API server to handle HTTP requests:

```bash
docker run -d \
  --name fastpubsub-server \
  -p 8000:8000 \
  -e fastpubsub_database_url='postgresql+psycopg://user:password@host:5432/fastpubsub' \
  -e fastpubsub_api_num_workers='4' \
  allisson/fastpubsub server
```

The API will be available at `http://localhost:8000`.

#### API Documentation

Once running, access the interactive API documentation at:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### 3️⃣ Cleanup Workers (Optional)

Run background workers to maintain the system:

#### Cleanup Acknowledged Messages

Removes successfully processed messages that are older than the configured threshold:

```bash
docker run --rm \
  -e fastpubsub_database_url='postgresql+psycopg://user:password@host:5432/fastpubsub' \
  -e fastpubsub_cleanup_acked_messages_older_than_seconds='3600' \
  allisson/fastpubsub cleanup_acked_messages
```

💡 **Tip**: Run this as a cron job or scheduled task every hour.

#### Cleanup Stuck Messages

Releases messages that have been locked for too long (consumer crashed or timed out):

```bash
docker run --rm \
  -e fastpubsub_database_url='postgresql+psycopg://user:password@host:5432/fastpubsub' \
  -e fastpubsub_cleanup_stuck_messages_lock_timeout_seconds='60' \
  allisson/fastpubsub cleanup_stuck_messages
```

💡 **Tip**: Run this frequently (every 1-5 minutes) to quickly recover stuck messages.

### 📝 Docker Compose Example

Here's a complete example using Docker Compose:

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:16
    environment:
      POSTGRES_USER: fastpubsub
      POSTGRES_PASSWORD: fastpubsub
      POSTGRES_DB: fastpubsub
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  fastpubsub-migrate:
    image: allisson/fastpubsub
    command: db-migrate
    environment:
      fastpubsub_database_url: postgresql+psycopg://fastpubsub:fastpubsub@postgres:5432/fastpubsub
    depends_on:
      - postgres

  fastpubsub-server:
    image: allisson/fastpubsub
    command: server
    environment:
      fastpubsub_database_url: postgresql+psycopg://fastpubsub:fastpubsub@postgres:5432/fastpubsub
      fastpubsub_api_num_workers: 4
    ports:
      - "8000:8000"
    depends_on:
      fastpubsub-migrate:
        condition: service_completed_successfully

  fastpubsub-cleanup-acked:
    image: allisson/fastpubsub
    command: cleanup_acked_messages
    environment:
      fastpubsub_database_url: postgresql+psycopg://fastpubsub:fastpubsub@postgres:5432/fastpubsub
      fastpubsub_cleanup_acked_messages_older_than_seconds: 3600
    depends_on:
      - postgres
    # Run every hour (use a cron scheduler or Kubernetes CronJob in production)

  fastpubsub-cleanup-stuck:
    image: allisson/fastpubsub
    command: cleanup_stuck_messages
    environment:
      fastpubsub_database_url: postgresql+psycopg://fastpubsub:fastpubsub@postgres:5432/fastpubsub
      fastpubsub_cleanup_stuck_messages_lock_timeout_seconds: 60
    depends_on:
      - postgres
    # Run every 5 minutes (use a cron scheduler or Kubernetes CronJob in production)

volumes:
  postgres_data:
```

## 📚 API Reference

### Topics

#### Create a Topic
```bash
curl -X POST http://localhost:8000/topics \
  -H "Content-Type: application/json" \
  -d '{"id": "orders"}'
```

#### Get a Topic
```bash
curl http://localhost:8000/topics/orders
```

#### List Topics
```bash
curl http://localhost:8000/topics?offset=0&limit=10
```

#### Delete a Topic
```bash
curl -X DELETE http://localhost:8000/topics/orders
```

#### Publish Messages
```bash
curl -X POST http://localhost:8000/topics/orders/messages \
  -H "Content-Type: application/json" \
  -d '[
    {"order_id": "123", "amount": 99.99},
    {"order_id": "124", "amount": 149.99}
  ]'
```

### Subscriptions

#### Create a Subscription
```bash
curl -X POST http://localhost:8000/subscriptions \
  -H "Content-Type: application/json" \
  -d '{
    "id": "order-processor",
    "topic_id": "orders",
    "filter": {"amount": {"$gt": 100}},
    "max_delivery_attempts": 5,
    "backoff_min_seconds": 5,
    "backoff_max_seconds": 300
  }'
```

🎯 **Filter**: Optional JSON filter to only receive messages matching criteria. Uses MongoDB-style operators.

#### Get a Subscription
```bash
curl http://localhost:8000/subscriptions/order-processor
```

#### List Subscriptions
```bash
curl http://localhost:8000/subscriptions?offset=0&limit=10
```

#### Delete a Subscription
```bash
curl -X DELETE http://localhost:8000/subscriptions/order-processor
```

#### Consume Messages
```bash
curl "http://localhost:8000/subscriptions/order-processor/messages?consumer_id=worker-1&batch_size=10"
```

⚠️ **Consumer ID**: A unique identifier for your consumer instance. Messages locked by one consumer can only be acked/nacked by that same consumer.

#### Acknowledge Messages (Success)
```bash
curl -X POST http://localhost:8000/subscriptions/order-processor/acks \
  -H "Content-Type: application/json" \
  -d '["550e8400-e29b-41d4-a716-446655440000"]'
```

✅ Marks messages as successfully processed.

#### Negative Acknowledge (Retry)
```bash
curl -X POST http://localhost:8000/subscriptions/order-processor/nacks \
  -H "Content-Type: application/json" \
  -d '["550e8400-e29b-41d4-a716-446655440001"]'
```

🔄 Returns messages to the queue for retry with exponential backoff.

### Dead Letter Queue (DLQ)

#### List DLQ Messages
```bash
curl "http://localhost:8000/subscriptions/order-processor/dlq?offset=0&limit=10"
```

#### Reprocess DLQ Messages
```bash
curl -X POST http://localhost:8000/subscriptions/order-processor/dlq/reprocess \
  -H "Content-Type: application/json" \
  -d '["550e8400-e29b-41d4-a716-446655440002"]'
```

♻️ Moves messages back to the active queue for reprocessing.

### Metrics

#### Get Subscription Metrics
```bash
curl http://localhost:8000/subscriptions/order-processor/metrics
```

Response:
```json
{
  "subscription_id": "order-processor",
  "available": 150,
  "delivered": 25,
  "acked": 1000,
  "dlq": 5
}
```

## 💡 Usage Examples

### Example 1: Simple Order Processing

1. **Create a topic for orders:**
```bash
curl -X POST http://localhost:8000/topics \
  -H "Content-Type: application/json" \
  -d '{"id": "orders"}'
```

2. **Create a subscription to process orders:**
```bash
curl -X POST http://localhost:8000/subscriptions \
  -H "Content-Type: application/json" \
  -d '{
    "id": "order-processor",
    "topic_id": "orders"
  }'
```

3. **Publish orders:**
```bash
curl -X POST http://localhost:8000/topics/orders/messages \
  -H "Content-Type: application/json" \
  -d '[
    {"order_id": "ORD-001", "customer": "John Doe", "total": 99.99},
    {"order_id": "ORD-002", "customer": "Jane Smith", "total": 149.99}
  ]'
```

4. **Consume and process messages:**
```bash
# Fetch messages
messages=$(curl -s "http://localhost:8000/subscriptions/order-processor/messages?consumer_id=worker-1&batch_size=10")

# Process messages (your business logic here)
echo "$messages" | jq -r '.data[].id' | while read -r msg_id; do
  # If processing succeeds:
  curl -X POST http://localhost:8000/subscriptions/order-processor/acks \
    -H "Content-Type: application/json" \
    -d "[\"$msg_id\"]"
  
  # If processing fails:
  # curl -X POST http://localhost:8000/subscriptions/order-processor/nacks \
  #   -H "Content-Type: application/json" \
  #   -d "[\"$msg_id\"]"
done
```

### Example 2: High-Value Order Filtering

Create a subscription that only processes orders over $100:

```bash
curl -X POST http://localhost:8000/subscriptions \
  -H "Content-Type: application/json" \
  -d '{
    "id": "high-value-orders",
    "topic_id": "orders",
    "filter": {"total": {"$gt": 100}}
  }'
```

### Example 3: Multiple Subscribers Pattern

Multiple subscriptions can receive the same messages:

```bash
# Subscription 1: Send email notifications
curl -X POST http://localhost:8000/subscriptions \
  -H "Content-Type: application/json" \
  -d '{"id": "email-notifier", "topic_id": "orders"}'

# Subscription 2: Update inventory
curl -X POST http://localhost:8000/subscriptions \
  -H "Content-Type: application/json" \
  -d '{"id": "inventory-updater", "topic_id": "orders"}'

# Subscription 3: Analytics
curl -X POST http://localhost:8000/subscriptions \
  -H "Content-Type: application/json" \
  -d '{"id": "analytics", "topic_id": "orders"}'
```

Each subscription maintains its own independent queue and delivery tracking.

## 🔄 Message Lifecycle

Understanding the message lifecycle is crucial for building reliable consumers:

1. **Published** 📝
   - Messages are published to a topic
   - Immediately copied to all subscription queues
   - Status: `available`

2. **Consumed** 🔒
   - Consumer fetches messages using `consumer_id`
   - Messages are locked to prevent duplicate processing
   - Status: `delivered` (locked)

3. **Processing** ⚙️
   - Consumer processes the message
   - Consumer decides: ack (success) or nack (retry)

4. **Acknowledged** ✅
   - Message processing succeeded
   - Status: `acked`
   - Eventually deleted by cleanup worker

5. **Negative Acknowledged** 🔄
   - Message processing failed
   - Returns to queue with backoff delay
   - `delivery_attempts` incremented
   - Status: `available` (after backoff)

6. **Dead Letter Queue** ⚰️
   - Max retry attempts exceeded
   - Status: `dlq`
   - Requires manual intervention or reprocessing

### Exponential Backoff

When a message is nacked, it becomes available again after a delay calculated using exponential backoff:

```
delay = min(backoff_min_seconds * (2 ^ delivery_attempts), backoff_max_seconds)
```

Example with defaults (min=5s, max=300s):
- Attempt 1: 5 seconds
- Attempt 2: 10 seconds
- Attempt 3: 20 seconds
- Attempt 4: 40 seconds
- Attempt 5: 80 seconds
- Attempt 6+: 300 seconds (capped)

## 🧹 Maintenance

### Cleanup Workers

FastPubSub requires two cleanup workers for optimal performance:

#### 1. Cleanup Acknowledged Messages

**Purpose**: Removes successfully processed messages to prevent table bloat.

**Frequency**: Every 1-2 hours

**Docker Command**:
```bash
docker run --rm \
  -e fastpubsub_database_url='postgresql+psycopg://user:password@host:5432/fastpubsub' \
  allisson/fastpubsub cleanup_acked_messages
```

**Configuration**: Set `fastpubsub_cleanup_acked_messages_older_than_seconds` to define how long to keep acked messages (default: 1 hour).

#### 2. Cleanup Stuck Messages

**Purpose**: Releases messages locked by consumers that crashed or timed out.

**Frequency**: Every 1-5 minutes

**Docker Command**:
```bash
docker run --rm \
  -e fastpubsub_database_url='postgresql+psycopg://user:password@host:5432/fastpubsub' \
  allisson/fastpubsub cleanup_stuck_messages
```

**Configuration**: Set `fastpubsub_cleanup_stuck_messages_lock_timeout_seconds` to define the lock timeout (default: 60 seconds).

### Scheduling Cleanup Workers

**Using Cron** (Linux):
```bash
# Edit crontab
crontab -e

# Add these lines:
# Cleanup acked messages every hour
0 * * * * docker run --rm -e fastpubsub_database_url='...' allisson/fastpubsub cleanup_acked_messages

# Cleanup stuck messages every 5 minutes
*/5 * * * * docker run --rm -e fastpubsub_database_url='...' allisson/fastpubsub cleanup_stuck_messages
```

**Using Kubernetes CronJob**:
```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: fastpubsub-cleanup-acked
spec:
  schedule: "0 * * * *"  # Every hour
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: cleanup
            image: allisson/fastpubsub
            command: ["python", "fastpubsub/main.py", "cleanup_acked_messages"]
            env:
            - name: fastpubsub_database_url
              value: "postgresql+psycopg://user:password@postgres:5432/fastpubsub"
          restartPolicy: OnFailure
```

## 🎯 Best Practices

### For Publishers

1. **Batch publish** when possible to reduce API calls
2. **Use meaningful topic names** that reflect the data type
3. **Keep message payloads small** for better performance
4. **Include timestamps** in your payload for tracking

### For Consumers

1. **Use unique consumer IDs** for each worker instance
2. **Process messages idempotently** (handle duplicates gracefully)
3. **Ack quickly** to free up locks
4. **Nack on transient failures** (network issues, temporary outages)
5. **Monitor DLQ** regularly and investigate failed messages
6. **Adjust batch_size** based on processing time
7. **Handle graceful shutdown** properly to avoid stuck messages

### For Operations

1. **Run cleanup workers** regularly to maintain performance
2. **Monitor metrics** to track queue depth and DLQ size
3. **Set appropriate timeouts** based on your processing needs
4. **Scale horizontally** by adding more consumer instances
5. **Use connection pooling** for PostgreSQL
6. **Regular database maintenance** (VACUUM, ANALYZE)

## 🔒 Security Considerations

1. **Network Security**: Use private networks or VPNs for PostgreSQL connections
2. **Authentication**: Implement API gateway authentication (FastPubSub itself has no built-in auth)
3. **TLS/SSL**: Use encrypted PostgreSQL connections in production
4. **Environment Variables**: Never commit credentials; use secrets management
5. **Input Validation**: Message payloads are stored as-is; validate in your consumers

## 📊 Performance Tips

1. **Database Indexing**: The migrations create appropriate indexes
2. **Connection Pooling**: Configure `database_pool_size` based on worker count
3. **Batch Operations**: Use larger batch sizes for consumers when appropriate
4. **Worker Scaling**: Run multiple consumer instances with different `consumer_id`
5. **PostgreSQL Tuning**: Optimize PostgreSQL settings for your workload

## 🆘 Troubleshooting

### Messages stuck in delivered state

**Cause**: Consumer crashed without acking/nacking messages.

**Solution**: Run `cleanup_stuck_messages` worker or reduce `lock_timeout_seconds`.

### High DLQ count

**Cause**: Messages consistently failing processing.

**Solution**: 
1. Check consumer logs for errors
2. Inspect DLQ messages to identify patterns
3. Fix consumer code
4. Reprocess DLQ messages

### Slow message processing

**Cause**: Database connection issues or table bloat.

**Solution**:
1. Run cleanup workers regularly
2. Increase `database_pool_size`
3. Run PostgreSQL VACUUM ANALYZE

### API returns 404 for subscription

**Cause**: Topic must exist before creating subscriptions.

**Solution**: Create the topic first, then create subscriptions.

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/allisson/fastpubsub/issues)
- **Docker Hub**: [allisson/fastpubsub](https://hub.docker.com/r/allisson/fastpubsub)
