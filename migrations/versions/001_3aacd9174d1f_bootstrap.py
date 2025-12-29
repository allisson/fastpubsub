"""bootstrap

Revision ID: 3aacd9174d1f
Revises:
Create Date: 2025-12-26 12:53:23.638504

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "3aacd9174d1f"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        ---------- uuid v7 generation ----------
        CREATE OR REPLACE FUNCTION uuid_generate_v7()
        RETURNS uuid
        AS $$
        DECLARE
            unix_ts_ms bytea;
            uuid_bytes bytea;
        BEGIN
            unix_ts_ms := decode(lpad(to_hex(floor(extract(epoch FROM clock_timestamp()) * 1000)::bigint), 12, '0'), 'hex');
            uuid_bytes := unix_ts_ms || substring(decode(replace(gen_random_uuid()::text, '-', ''), 'hex') from 7 for 10);
            uuid_bytes := set_byte(uuid_bytes, 6, (get_byte(uuid_bytes, 6) & 15) | 112);
            uuid_bytes := set_byte(uuid_bytes, 8, (get_byte(uuid_bytes, 8) & 63) | 128);
            RETURN encode(uuid_bytes, 'hex')::uuid;
        END;
        $$ LANGUAGE plpgsql VOLATILE;

        ---------- Tables ----------
        CREATE TABLE topics (
            id TEXT PRIMARY KEY,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );

        CREATE TABLE subscriptions (
            id TEXT PRIMARY KEY,
            topic_id TEXT NOT NULL REFERENCES topics(id) ON DELETE CASCADE,
            filter JSONB NOT NULL DEFAULT '{}'::jsonb,
            max_delivery_attempts INT NOT NULL DEFAULT 5,
            backoff_min_seconds INT NOT NULL DEFAULT 5,
            backoff_max_seconds INT NOT NULL DEFAULT 300,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );

        CREATE TABLE subscription_messages (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v7(),
            subscription_id TEXT NOT NULL REFERENCES subscriptions(id) ON DELETE CASCADE,
            payload JSONB NOT NULL,
            status TEXT NOT NULL DEFAULT 'available',
            delivery_attempts INT NOT NULL DEFAULT 0,
            available_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            locked_at TIMESTAMPTZ,
            locked_by TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            acked_at TIMESTAMPTZ
        );

        ---------- Indexes ----------
        -- Hot path: consume
        CREATE INDEX idx_sub_msgs_available
        ON subscription_messages (subscription_id, available_at)
        WHERE status = 'available';

        -- Ack / Nack batches
        CREATE INDEX idx_sub_msgs_delivered
        ON subscription_messages (subscription_id)
        WHERE status = 'delivered';

        -- DLQ listing
        CREATE INDEX idx_sub_msgs_dlq
        ON subscription_messages (subscription_id)
        WHERE status = 'dlq';

        -- Payload filtering
        CREATE INDEX idx_sub_msgs_payload_gin
        ON subscription_messages
        USING GIN (payload jsonb_path_ops);

        -- Publish performance
        CREATE INDEX idx_subscriptions_topic
        ON subscriptions (topic_id);

        ---------- Stored procedures ----------
        CREATE OR REPLACE FUNCTION publish_messages(
            p_topic_id TEXT,
            p_messages JSONB[]
        )
        RETURNS INT
        LANGUAGE plpgsql
        AS $$
        DECLARE
            inserted_count INT;
        BEGIN
            WITH messages AS (
                SELECT m AS payload
                FROM unnest(p_messages) AS m
                WHERE jsonb_typeof(m) = 'object'
            ),
            eligible AS (
                SELECT
                    s.id AS subscription_id,
                    m.payload
                FROM subscriptions s
                JOIN messages m ON TRUE
                WHERE s.topic_id = p_topic_id
                AND (
                    -- no filter or invalid filter -> accept
                    s.filter IS NULL
                    OR jsonb_typeof(s.filter) <> 'object'
                    OR s.filter = '{}'::jsonb
                    OR NOT EXISTS (
                        SELECT 1
                        FROM jsonb_each(s.filter) f(key, allowed_values)
                        WHERE
                            jsonb_typeof(allowed_values) = 'array'
                            AND NOT (
                                m.payload ->> f.key = ANY (
                                    SELECT jsonb_array_elements_text(allowed_values)
                                )
                            )
                        )
                )
            )
            INSERT INTO subscription_messages (
                subscription_id,
                payload
            )
            SELECT
                subscription_id,
                payload
            FROM eligible;

            GET DIAGNOSTICS inserted_count = ROW_COUNT;

            RETURN inserted_count;
        END;
        $$;


        CREATE OR REPLACE FUNCTION consume_messages(
            p_subscription_id TEXT,
            p_consumer_id TEXT,
            p_batch_size INT
        )
        RETURNS SETOF subscription_messages
        LANGUAGE sql
        AS $$
        WITH cte AS (
            SELECT id
            FROM subscription_messages
            WHERE subscription_id = p_subscription_id
            AND status = 'available'
            AND available_at <= now()
            ORDER BY available_at
            LIMIT p_batch_size
            FOR UPDATE SKIP LOCKED
        )
        UPDATE subscription_messages sm
        SET status = 'delivered',
            locked_at = now(),
            locked_by = p_consumer_id,
            delivery_attempts = delivery_attempts + 1
        FROM cte
        WHERE sm.id = cte.id
        RETURNING sm.*;
        $$;

        CREATE OR REPLACE FUNCTION ack_messages(
            p_subscription_id TEXT,
            p_message_ids UUID[]
        )
        RETURNS INT
        LANGUAGE sql
        AS $$
        UPDATE subscription_messages
        SET status = 'acked',
            acked_at = now(),
            locked_at = NULL,
            locked_by = NULL
        WHERE subscription_id = p_subscription_id
        AND id = ANY (p_message_ids)
        AND status = 'delivered'
        RETURNING 1;
        $$;

        CREATE OR REPLACE FUNCTION nack_messages(
            p_subscription_id TEXT,
            p_message_ids UUID[]
        )
        RETURNS INT
        LANGUAGE plpgsql
        AS $$
        DECLARE
            sub subscriptions;
        BEGIN
            SELECT * INTO sub
            FROM subscriptions
            WHERE id = p_subscription_id;

            UPDATE subscription_messages
            SET status = CASE
                WHEN delivery_attempts >= sub.max_delivery_attempts THEN 'dlq'
                ELSE 'available'
            END,
            available_at = CASE
                WHEN delivery_attempts >= sub.max_delivery_attempts THEN available_at
                ELSE now() + make_interval(
                    secs => LEAST(
                        sub.backoff_max_seconds,
                        sub.backoff_min_seconds * (2 ^ delivery_attempts)
                    )
                )
            END,
            locked_at = NULL,
            locked_by = NULL
            WHERE id = ANY (p_message_ids)
            AND subscription_id = p_subscription_id
            AND status = 'delivered';

            RETURN 1;
        END;
        $$;

        CREATE OR REPLACE FUNCTION list_dlq_messages(
            p_subscription_id TEXT,
            p_limit INT
        )
        RETURNS SETOF subscription_messages
        LANGUAGE sql
        AS $$
        SELECT *
        FROM subscription_messages
        WHERE subscription_id = p_subscription_id
        AND status = 'dlq'
        ORDER BY created_at
        LIMIT p_limit;
        $$;

        CREATE OR REPLACE FUNCTION reprocess_dlq_messages(
            p_subscription_id TEXT,
            p_message_ids UUID[]
        )
        RETURNS INT
        LANGUAGE sql
        AS $$
        UPDATE subscription_messages
        SET status = 'available',
            delivery_attempts = 0,
            available_at = now()
        WHERE subscription_id = p_subscription_id
        AND id = ANY (p_message_ids)
        AND status = 'dlq'
        RETURNING 1;
        $$;

        CREATE OR REPLACE FUNCTION cleanup_stuck_messages(
            p_subscription_id TEXT,
            p_lock_timeout INTERVAL
        )
        RETURNS INT
        LANGUAGE sql
        AS $$
        UPDATE subscription_messages
        SET status = 'available',
            locked_at = NULL,
            locked_by = NULL
        WHERE subscription_id = p_subscription_id
        AND status = 'delivered'
        AND locked_at < now() - p_lock_timeout
        RETURNING 1;
        $$;

        CREATE OR REPLACE FUNCTION cleanup_acked_messages(
            p_subscription_id TEXT,
            p_older_than INTERVAL
        )
        RETURNS INT
        LANGUAGE sql
        AS $$
        DELETE FROM subscription_messages
        WHERE subscription_id = p_subscription_id
        AND status = 'acked'
        AND acked_at < now() - p_older_than
        RETURNING 1;
        $$;

        CREATE OR REPLACE FUNCTION subscription_metrics(
            p_subscription_id TEXT
        )
        RETURNS TABLE (
            available BIGINT,
            delivered BIGINT,
            acked BIGINT,
            dlq BIGINT
        )
        LANGUAGE sql
        AS $$
        SELECT
            count(*) FILTER (WHERE status = 'available'),
            count(*) FILTER (WHERE status = 'delivered'),
            count(*) FILTER (WHERE status = 'acked'),
            count(*) FILTER (WHERE status = 'dlq')
        FROM subscription_messages
        WHERE subscription_id = p_subscription_id;
        $$;
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DROP FUNCTION IF EXISTS publish_messages;
        DROP FUNCTION IF EXISTS consume_messages;
        DROP FUNCTION IF EXISTS ack_messages;
        DROP FUNCTION IF EXISTS nack_messages;
        DROP FUNCTION IF EXISTS list_dlq_messages;
        DROP FUNCTION IF EXISTS reprocess_dlq_messages;
        DROP FUNCTION IF EXISTS cleanup_stuck_messages;
        DROP FUNCTION IF EXISTS cleanup_acked_messages;
        DROP FUNCTION IF EXISTS subscription_metrics;

        DROP INDEX IF EXISTS idx_sub_msgs_available;
        DROP INDEX IF EXISTS idx_sub_msgs_delivered;
        DROP INDEX IF EXISTS idx_sub_msgs_dlq;
        DROP INDEX IF EXISTS idx_sub_msgs_payload_gin;

        DROP TABLE IF EXISTS subscription_messages;
        DROP TABLE IF EXISTS subscriptions;
        DROP TABLE IF EXISTS topics;

        DROP FUNCTION IF EXISTS uuid_generate_v7();
        """
    )
