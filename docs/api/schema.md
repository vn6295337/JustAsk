# Database Schema

**SQLite (React Native on-device)**

---

## offline_queue

Stores pending queries when offline.

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER PRIMARY KEY | Auto-increment |
| query | TEXT NOT NULL | Query text |
| timestamp | INTEGER NOT NULL | Query timestamp (ms) |
| status | TEXT DEFAULT 'pending' | pending \| synced |
| created_at | INTEGER DEFAULT now | Insertion time (unix) |

**Indexes:** id (primary), status (lookup)

---

## offline_responses

Stores responses for synced queries.

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER PRIMARY KEY | Auto-increment |
| queue_id | INTEGER NOT NULL | FK to offline_queue |
| response | TEXT NOT NULL | LLM response |
| llm_used | TEXT | Provider (gemini\|groq\|openrouter) |
| category | TEXT | Query category |
| response_time | INTEGER | Response time (ms) |
| synced_at | INTEGER DEFAULT now | Sync timestamp (unix) |

**Indexes:** id (primary), queue_id (FK lookup)
**Foreign Key:** queue_id → offline_queue.id

---

## cache

Stores cached responses.

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER PRIMARY KEY | Auto-increment |
| query_hash | TEXT UNIQUE NOT NULL | MD5(query.toLowerCase()) |
| query_text | TEXT | Original query |
| response | TEXT NOT NULL | LLM response |
| llm_used | TEXT | Provider |
| category | TEXT | Query category |
| response_time | INTEGER | Response time (ms) |
| created_at | INTEGER DEFAULT now | Creation time (unix) |
| expires_at | INTEGER NOT NULL | Expiration time (unix) |

**Indexes:** id (primary), query_hash (unique lookup), expires_at (cleanup)

---

## Lifecycle

**Query → Offline Queue → Sync → Offline Responses → Cache**

1. User offline: `INSERT offline_queue`
2. Network restored: Read `offline_queue WHERE status='pending'`
3. Sync response: `INSERT offline_responses + UPDATE offline_queue SET status='synced'`
4. User online: Direct `INSERT cache` after API call
5. Cleanup: Delete `offline_responses` and `offline_queue` where status='synced' (optional)

