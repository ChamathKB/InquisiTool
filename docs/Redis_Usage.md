# Redis Usage

Redis is used as a caching layer to reduce latency and external API calls across the survey flow.

## Implemented

### Session/Interaction State Caching

`get_interaction` is called on every survey request to fetch the full interaction document (campaign, answers, questions). Cached by `session_id`, updated in-place after each question turn, and deleted on survey end.

- Key: `interaction:<session_id>`
- TTL: 1 hour
- Client: async (`app.state.redis_client`)

### Campaign Data Caching

`get_campaign` is called on every new session. Campaign data is immutable during a survey, so it is cached on first read and reused across all sessions under the same campaign.

- Key: `campaign:<campaign_id>`
- TTL: 1 hour
- Client: async (`app.state.redis_client`)

### Embedding Cache

`get_embeddings()` calls the Gemini API on every query. Cached by `hash(text)` so identical query text skips the API call entirely. Used by both `QdrantSearchTool` and `load_pdf_to_qdrant`.

- Key: `embedding:<hash(text)>`
- TTL: 24 hours
- Client: sync (`db/redis.py` singleton) — required since `get_embeddings` is a sync function

### Rate Limiting

Rate limiting is implemented via `slowapi` using Redis as the backing store, keyed by remote IP. Limits are enforced after Keycloak JWT auth on all endpoints.

- `/query/survey` — 30 requests / minute
- All other endpoints — no limit set (auth enforced only)

See `docs/Rate_Limits.md` for full reference.

## Monitoring

### Application Logs

Cache hits and misses are logged at `DEBUG` level via `db/redis.py`. Run with `--log-level debug` to see them:

```bash
inquisitool run --log-level debug
```

Output:

```
[*] cache hit: interaction:xyz-456
[*] cache miss: campaign:abc-123
```

### Redis CLI (Docker)

Shell into the running container:

```bash
docker exec -it inquisitool-redis redis-cli
```

Useful commands once inside:

```bash
# watch all commands in real time
MONITOR

# check hit/miss stats
INFO stats

# see all cached keys
KEYS *

# inspect a specific key
GET interaction:<session_id>
GET campaign:<campaign_id>
GET embedding:<hash>

# check TTL remaining on a key
TTL interaction:<session_id>
```

### RedisInsight (GUI)

Free GUI from Redis with key browser, memory usage, and hit rate graphs — no code changes needed:

```bash
docker run -p 5540:5540 redis/redisinsight
```

Then open `http://localhost:5540` and connect to `inquisitool-redis:6379`.

## Not Worth It

- **Qdrant search results** — Queries are dynamic and personalized per session, so cache hit rate would be too low to justify.
- **Closing messages** — Generated once per session; caching adds complexity with minimal benefit.
