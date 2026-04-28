# Caching Strategies for Web Applications

**Category**: architecture
**Source**: AWS, Redis docs, web.dev
**Use Case**: Architect Agent uses this to design performance optimizations in technical specs.

---

## 1. Overview

**Caching** is the practice of storing copies of data closer to consumers—in memory, on disk, at the edge of the network—to reduce latency and reduce load on origin systems. Caching is one of the highest-leverage performance techniques in web architecture: a well-placed cache can turn a 200-millisecond database query into a sub-millisecond memory read, and a CDN cache can serve a static asset to a user on another continent in less time than a round trip to the origin server.

The principle is simple, but the practice is not. Phil Karlton's widely cited observation captures the central difficulty: **"There are only two hard things in Computer Science: cache invalidation and naming things."** The hard part is not putting data into a cache; the hard part is knowing when to remove it, when to refresh it, and how to keep multiple caches consistent with the underlying truth. Caches that serve stale data quietly produce some of the most frustrating bugs in production—the user updates a setting, the page does not change, no one is sure why.

This document covers the five layers of caching commonly found in modern web architectures, the major invalidation strategies, the trade-offs between cache stores (Redis, Memcached, local in-process), the standard read/write patterns, the cache-stampede problem and its mitigations, and a concrete caching plan for an educational coding app. It closes with the most common pitfalls.

---

## 2. The Five Layers of Caching

A complete caching strategy typically combines several layers, each addressing a different latency and load concern.

**1. Browser cache.** The user's browser caches resources locally based on HTTP headers returned by the server. The two main mechanisms are `Cache-Control` (specifying how long a resource is fresh and where it may be cached) and `ETag` (a content-derived identifier that lets the browser ask "has this changed?" rather than re-downloading the resource). Browser caching is the cheapest layer—the request never leaves the user's machine—but it is also the hardest to invalidate, because once a resource is cached in a browser, the server cannot directly purge it. The standard discipline is to use **fingerprinted filenames** (e.g., `app.a1b2c3.js`) for static assets and serve them with long `Cache-Control` lifetimes, while serving HTML with short or zero cache lifetimes so that updates to fingerprinted asset references propagate immediately.

**2. CDN (Content Delivery Network).** A CDN is a geographically distributed network of edge servers that cache content close to users. Cloudflare, Akamai, AWS CloudFront, and Fastly are the major commercial CDNs. CDNs cache static assets (images, scripts, stylesheets, video) and increasingly also cache API responses and dynamic HTML at the edge. The benefit is twofold: lower latency for users far from the origin and significantly reduced load on origin servers. CDN cache invalidation is typically handled through cache-key design and explicit purge APIs.

**3. API gateway / reverse proxy cache.** Sitting in front of application servers, reverse proxies like **Nginx** and **Varnish** can cache responses for short periods, absorbing repeated requests for the same data. This layer is particularly effective for read-heavy endpoints with high request rates and modest data freshness requirements. Reverse-proxy caching is harder to apply to authenticated traffic because cache keys must include the user's identity to avoid leaking one user's data to another.

**4. Application cache.** In-memory caching inside the application process itself: Python's `functools.lru_cache`, Node.js Maps, Java's Caffeine. The cache lives in the same process as the application code, making access essentially free. Application caches are excellent for derived data that is expensive to compute and changes slowly. Their limitation is that the cache is per-process; with multiple application instances, each has its own copy and they can drift out of sync.

**5. Database / shared cache.** A separate caching server—**Redis** or **Memcached** are the canonical choices—holds frequently accessed data in memory, shared across all application instances. Common uses: cached database query results, session data, computed views, rate-limit counters, leaderboards. The shared cache layer trades single-process speed for cross-instance consistency, and it adds a network hop but eliminates the per-process duplication of in-process caches.

A well-designed system uses several of these layers together, with each layer addressing a different concern. Static assets are cached at the browser and the CDN; API responses might be cached briefly at a reverse proxy and at the application level; database query results live in Redis. Each layer's behavior must be understood and tuned independently.

---

## 3. Cache Invalidation Strategies

The hard problem in caching is keeping the cache aligned with the underlying truth. Four standard strategies cover most cases.

**TTL (Time-to-Live).** The simplest strategy: set an expiration time on each cached entry. After the TTL elapses, the entry is removed (or treated as stale and refreshed on the next access). TTL is easy to implement, requires no coordination between the writer of the canonical data and the cache, and produces predictable cache behavior. The trade-off is that data is stale for up to TTL seconds after a change. For data where some staleness is acceptable—lesson content that updates rarely, leaderboards that need not be exact to the second—TTL alone is often sufficient.

**Write-through.** Every write to the underlying data store is also written to the cache, synchronously, in the same operation. The cache and the database stay aligned by construction. Reads always hit a fresh cache. The trade-off is that writes become slower (two stores to update instead of one), and a failure to write to the cache must be handled carefully to avoid leaving the database updated with a stale cache.

**Write-behind (write-back).** Writes go to the cache first and are propagated to the underlying store asynchronously. The cache is the source of truth from the application's perspective; the database catches up later. This pattern produces fast writes but introduces real risk: a cache failure between the write and the asynchronous flush can lose data. Write-behind is appropriate for data where some loss is acceptable in exchange for write performance, such as analytics counters or non-critical telemetry.

**Cache-aside (lazy loading).** The application is responsible for reading from the cache, falling back to the database on a cache miss, and populating the cache after the miss. Writes go directly to the database, and the cache is invalidated (or updated) explicitly. Cache-aside is the most common pattern in modern web applications because it gives the application full control over caching policy without coupling the cache and database into a single write path. The trade-off is that the application code must handle cache misses, repopulation, and invalidation explicitly—which is where many caching bugs live.

The four strategies are not exclusive. A typical application uses cache-aside for most data, TTL on top of cache-aside as a safety net, and write-through for a small set of values where strict freshness is essential.

---

## 4. Cache Stores Compared

| Store | Strengths | Trade-offs | Typical use |
|---|---|---|---|
| **Redis** | In-memory key-value store with rich data structures (strings, lists, hashes, sets, sorted sets, streams). Supports persistence (RDB snapshots and AOF logs), replication, pub/sub, scripting (Lua), and clustering. | Operationally more complex than Memcached. Data in memory must fit the working set, with options for spilling to disk. | Sessions, rate limiting, leaderboards, queues, complex cached views, distributed locks. The default modern choice for most caching needs. |
| **Memcached** | Simpler in-memory key-value store. Plain strings only; no rich data structures. Multi-threaded architecture; very fast for simple key-value access. | No persistence; data is lost on restart. No native replication or clustering (though clients can shard). Limited to flat key-value pairs. | High-volume simple caching where Redis's data structures and persistence are not needed. Less common in new systems; many teams now default to Redis even for simple caching needs. |
| **Local in-process** | Fastest possible access—same process, same memory. No network hop. Standard libraries (Python's `functools.lru_cache`, Node.js Maps, Java's Caffeine) provide LRU and other eviction policies. | Per-process, so multiple application instances have separate copies that can drift. Cache is lost on process restart. Difficult to invalidate across instances. | Hot, small, slow-changing computed data: configuration, lookup tables, derived constants, feature flags resolved per request. |

The practical pattern: **use local in-process caches for the smallest, hottest, slowest-changing data; use Redis (or equivalent) for shared cached state; reserve Memcached for legacy or specific high-throughput simple-key-value scenarios**. Redis has become the default in most new systems because its data structures, persistence, and clustering options cover a wide range of needs without forcing the team to add a second cache layer for slightly different workloads.

---

## 5. Common Patterns

The four invalidation strategies in Section 3 combine with the cache stores in Section 4 to produce several recurring patterns.

**Read-through.** The application asks the cache for data; if the cache misses, the cache itself loads from the database and returns the result. The application never talks directly to the database for reads. Read-through is conceptually clean but requires cache-side database integration, which is uncommon in most application caches and more typical in dedicated caching layers. Most "read-through" implementations in practice are actually cache-aside, with the application performing the fallback.

**Cache-aside.** The dominant pattern in application code. The application reads the cache; on a miss, it reads the database, populates the cache, and returns the result. On writes, it updates the database and either invalidates the cache entry or writes the new value. Most caching code in production follows this pattern.

**Write-through.** Writes update both the cache and the database in a coordinated operation. Best when read traffic dominates and the cost of slightly slower writes is acceptable.

**Write-behind / write-back.** Writes update the cache, and the cache asynchronously propagates to the database. Best for write-heavy workloads where strict durability is not required.

**Refresh-ahead.** The cache proactively refreshes entries before they expire, based on access patterns or TTL proximity. Reduces the chance of users hitting an expired entry but requires more sophisticated cache logic.

---

## 6. Cache Stampede and Mitigation

The **cache stampede** (also called the "thundering herd" problem) is a failure mode that emerges when a popular cache entry expires. Many concurrent requests miss the cache simultaneously, all attempt to load the data from the underlying database, and the database is hit with a sudden burst of identical queries. In the worst case, the database is overloaded, requests time out, and the cache cannot be repopulated—an outage triggered by the cache layer itself.

Three standard mitigations:

**Request coalescing (single-flight).** When multiple concurrent requests miss the cache for the same key, only one of them performs the underlying load; the others wait for it to complete and use its result. This pattern is implemented in libraries like Go's `singleflight` package or via in-application locks. The behavior is precisely what cache stampede prevention requires: regardless of how many concurrent misses occur, the underlying database sees one query.

**Jittered TTL.** Instead of giving every cache entry the same TTL (which would cause many entries to expire simultaneously), add randomness: TTL = base + random(0, jitter). This spreads expirations out over time and prevents synchronized stampedes when many entries were populated together (e.g., on application startup).

**Probabilistic early refresh.** As an entry approaches its TTL, requests probabilistically refresh it before expiration, distributing the refresh load over time rather than concentrating it at the moment of expiry.

For high-traffic systems, all three mitigations together produce a robust caching layer. For modest-traffic systems, jittered TTL alone is often sufficient.

## 7. Example: Educational Coding App for Kids

Consider the caching strategy for **CodeCub**, an educational Python coding app for children aged 6–12 with a web frontend, a parent dashboard, and a planned school-channel admin interface. The system has several distinct caching opportunities at different layers.

**Layer 1 — CDN for static assets.**
All JavaScript bundles, CSS, images, lesson illustrations, audio assets, and video assets are served through a CDN (Cloudflare or AWS CloudFront). Filenames are fingerprinted (`app.a1b2c3.js`); these files have long `Cache-Control` lifetimes (a year). HTML is served with short or zero cache lifetimes so that newly fingerprinted asset references propagate immediately. This layer alone reduces origin traffic by a large factor and improves global latency for users far from the origin region.

**Layer 2 — Browser cache for lesson content.**
Lesson definitions (the curriculum content itself, which is the same for every learner of a given age band) are cached aggressively in the browser with `Cache-Control: max-age` headers covering hours to days, plus an `ETag` for revalidation. Once a child has loaded a lesson, opening it again costs nothing.

**Layer 3 — Redis for session, real-time, and computed views.**
Redis serves several roles:
- *Session data* for parent and child authentication: small, hot, accessed on every request. Cache-aside with TTL aligned to session length.
- *Rate limiting* for the AI tutoring endpoint, which is the most expensive backend call. Redis counters with sliding windows protect against abuse and runaway costs.
- *Leaderboards* (if and when introduced for child-visible streaks or weekly XP). Redis sorted sets are the canonical implementation.
- *Computed parent dashboard summaries* (this week's lessons completed, total streak, etc.). Cache-aside with a short TTL (minutes) plus invalidation on lesson completion.

**Layer 4 — Application cache for hot, slow-changing data.**
In-process caches inside the FastAPI service hold lookup data: lesson metadata, age-band rules, feature flags. These are small, change slowly, and tolerate per-process drift because they are seldom updated and updates can wait until the next deployment or a TTL expiry.

**Layer 5 — Database query cache.**
The main PostgreSQL instance handles its own query plan caching internally, and read replicas absorb read traffic that does not need to hit the primary. Explicit query-result caching in Redis is reserved for genuinely expensive queries (e.g., teacher dashboard aggregations across a large class roster), with cache-aside and TTL.

**Invalidation discipline.**
- Static assets: fingerprinted filenames; old versions remain valid until evicted, new versions propagate via new filenames.
- Lesson content: TTL-based, with a deliberate 5-minute lag accepted between curriculum updates and full propagation.
- Parent dashboard summaries: invalidated explicitly on lesson completion (write triggers an invalidation event), plus a short TTL as a safety net.
- AI tutoring rate limits: TTL is the only invalidation needed.

This layering produces a system where the database is largely shielded from read traffic, global users see fast-loading static content, the parent dashboard updates quickly after a child finishes a lesson, and AI inference cost is bounded by enforceable rate limits.

---

## 8. Common Pitfalls

- **Caching too aggressively without invalidation thinking.** Long TTLs on data that changes more often than the TTL produces stale-data bugs that are hard to reproduce and harder to explain. Match TTLs to the data's actual change rate, not to maximize cache hit rate.
- **No invalidation strategy at all.** Caches with TTL alone are forgiving; caches relied upon as the source of truth without explicit invalidation produce silent inconsistencies.
- **Cache key collisions.** Two different data items mapping to the same cache key returns one user's data for another user's request—a security and correctness bug. Include all relevant identifiers (user ID, locale, version) in the cache key.
- **Hot keys overwhelming the cache server.** A single very popular key can saturate a single Redis node. Mitigations include local in-process caching for hot keys, key sharding, or Redis Cluster.
- **Cache stampede on popular keys.** Without request coalescing or jittered TTL, a popular key's expiration can produce a thundering herd that overwhelms the database.
- **Caching authenticated content at shared layers.** A reverse proxy or CDN that caches per-user data without including the user identity in the cache key serves one user's data to another. Always verify cache-key dimensions for any layer that sees authenticated traffic.
- **Forgetting that local in-process caches drift across instances.** A cached value updated in one process is not updated in others; for shared cached state, use a shared cache (Redis) instead of in-process structures.
- **Caching error responses inadvertently.** Reverse proxies and CDNs sometimes cache 5xx error responses by default. Configure caching to skip error responses unless caching them is specifically intended.
- **Treating cache hit rate as the goal.** A high hit rate is a means, not an end. The goal is correctness with acceptable latency; a 99% hit rate that serves wrong data is worse than a 90% hit rate that is correct.

---

## 9. References

- AWS — Caching: https://aws.amazon.com/caching/
- Redis — Client-side caching: https://redis.io/docs/manual/client-side-caching/
- web.dev — HTTP cache: https://web.dev/articles/http-cache