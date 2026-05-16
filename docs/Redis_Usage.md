# Redis Usage

Redis is used as a caching layer to reduce latency and external API calls across the survey flow.

## High Value

- **Session/interaction state caching** — `get_interaction` is called on every survey request to fetch the full interaction document (campaign, answers, questions). Caching by `session_id` avoids repeated MongoDB reads for active sessions.
- **Campaign data caching** — `get_campaign` and the `CampaignInfoTool`/`QuestionCounterTool` both query MongoDB for campaign data that is immutable during a survey. Caching by `campaign_id` eliminates redundant DB reads across all sessions under the same campaign.

### Moderate Value

- **Embedding cache** — `get_embeddings()` calls the Gemini API on every query. Caching `query_text → vector` avoids redundant API calls and reduces cost when similar queries recur across sessions.
- **Rate limiting** — Redis provides a standard backing store (token bucket / sliding window) for per `campaign_id` or `user_id` rate limiting against Gemini API quotas.

## Monitoring

### Application Logs

Cache hits and misses are logged automatically via `db/redis.py`:

```bash
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

# check TTL remaining on a key
TTL interaction:<session_id>
```

### RedisInsight (GUI)

Free GUI from Redis with key browser, memory usage, and hit rate graphs — no code changes needed:

```bash
docker run -p 5540:5540 redis/redisinsight
```

Then open `http://localhost:5540` and connect to `inquisitool-redis:6379`.

### Not Worth It

- **Qdrant search results** — Queries are dynamic and personalized per session, so cache hit rate would be too low to justify.
- **Closing messages** — Generated once per session; caching adds complexity with minimal benefit.
