# Database Indexing

**Category**: data_design
**Source**: PostgreSQL docs, Use The Index, Luke!
**Use Case**: Architect Agent uses this when designing query performance in technical specs.

---

## 1. Overview

A **database index** is an auxiliary data structure that the database maintains alongside a table to accelerate the retrieval of specific rows. Without an index, finding rows that match a query condition requires the database to examine every row in the table—a **full table scan**, with cost proportional to table size (`O(n)`). With an appropriate index, the database can locate matching rows in time roughly proportional to the logarithm of the table size (`O(log n)` for the most common index type, the B-tree). For tables with millions or billions of rows, the difference between a full scan and an index lookup is the difference between seconds-to-minutes and milliseconds.

Indexes are not free. Every index occupies disk space, and every insert, update, or delete on the indexed table also updates the index. A table with five indexes pays five times the index-maintenance cost on every write. The art of database performance is choosing which indexes to maintain: enough to make the dominant queries fast, few enough that writes do not slow unacceptably, and well-shaped enough that the queries the application actually runs can use them.

This document explains how indexes work, the major index types in PostgreSQL (the canonical example, though most modern relational databases offer similar facilities), composite-index design, when not to index, how to inspect query plans, and a concrete indexing plan for an educational coding app for children. It closes with the common pitfalls that produce slow queries and bloated tables.

---

## 2. How Indexes Work

The dominant index type is the **B-tree** (balanced tree), and almost all "default" indexes in modern relational databases are B-trees. A B-tree organizes index entries into a balanced tree of pages, with internal pages containing routing keys and leaf pages containing the actual indexed values along with pointers to the corresponding table rows.

A simplified ASCII view of a B-tree on an integer column:

```
                       [ 50 | 100 ]
                      /      |      \
              [10|30]    [60|80]    [120|150]
              /  |  \    /  |  \    /   |   \
            ... ... ... ... ... ... ... ... ...
```

To find rows matching `WHERE id = 75`, the database starts at the root, sees that 75 falls between 50 and 100, descends to the middle internal page, sees that 75 falls between 60 and 80, descends to the appropriate leaf, and finds 75 (or determines it does not exist). Each step skips most of the data; the number of steps grows logarithmically with the number of rows.

B-trees support both **equality** queries (`WHERE id = 75`) and **range** queries (`WHERE id BETWEEN 50 AND 100`, `WHERE id > 75`, `WHERE id < 200`) efficiently, because the leaves are stored in sorted order. They also support sorted retrieval (`ORDER BY id`) without an additional sort step.

Other index types use different data structures optimized for different query patterns. The choice of index type matters; using the wrong type produces an index that the query planner ignores, paying the maintenance cost without the lookup benefit.

---

## 3. Index Types

PostgreSQL supports several index types beyond B-tree. Each fits a specific class of query.

| Type | Data structure | Best for | Limitations |
|---|---|---|---|
| **B-tree** | Balanced tree | Equality and range queries on scalar values; sorted retrieval. The default and most common index type. | Less efficient for full-text search, JSON document queries, or geospatial data. |
| **Hash** | Hash table | Pure equality queries (`=`). Faster than B-tree for equality on some workloads. | No range queries, no sorted retrieval. Rarely used in PostgreSQL because B-tree handles equality competently. |
| **GIN (Generalized Inverted Index)** | Inverted index | Full-text search (`tsvector`), JSON/JSONB containment queries, array containment, trigram-based fuzzy matching. | Larger than B-tree; slower to update. Best for read-heavy workloads on these data types. |
| **GiST (Generalized Search Tree)** | Generalized search tree | Geospatial (PostGIS), range types, nearest-neighbor queries, custom data types. | More specialized; the right choice depends on the extension or data type. |
| **BRIN (Block Range Index)** | Block-range summary | Very large tables with **natural physical ordering**, especially time-series data (timestamps that grow monotonically). Tiny on disk relative to B-tree. | Only useful when the data has correlation between physical row order and indexed value. |

The practical guidance for most applications:

- **Default to B-tree.** The great majority of indexes in any application are B-tree indexes on scalar columns.
- **Use GIN for JSONB queries and full-text search.** When the application stores JSONB documents and queries inside them (`WHERE data @> '{"type": "lesson"}'`) or uses full-text search, GIN is the index type that makes those queries fast.
- **Use GiST for geospatial.** PostGIS workloads use GiST as a matter of course.
- **Use BRIN for very large append-only tables.** Time-series tables (events, logs, telemetry) with monotonically increasing timestamps benefit from BRIN's tiny footprint and reasonable lookup performance.
- **Hash is rarely the right answer in modern PostgreSQL.** B-tree handles equality well, and hash indexes have historical operational issues that B-trees do not.

---

## 4. Composite Indexes and Column Order

A **composite index** (also called a multi-column or compound index) covers multiple columns in a defined order. Column order matters significantly: a composite index on `(a, b)` is useful for queries that filter on `a` alone or on `a` and `b` together, but **not** for queries that filter on `b` alone.

A simple example. Suppose a `progress` table has columns `(learner_id, lesson_id, status, completed_at)`, and the application's dominant queries are:

1. "Find all progress rows for a given learner": `WHERE learner_id = ?`
2. "Find a specific learner's progress on a specific lesson": `WHERE learner_id = ? AND lesson_id = ?`
3. "Find a learner's completed lessons": `WHERE learner_id = ? AND status = 'completed'`

A composite index on `(learner_id, lesson_id)` accelerates queries 1 and 2 but not 3 (where the second filter is on `status`, not `lesson_id`). A composite index on `(learner_id, status)` would accelerate queries 1 and 3 but not 2.

The standard guidance: **place the most selective and most commonly filtered columns first**. Most query planners will use a leading prefix of a composite index, so `(learner_id, lesson_id)` is usable for `WHERE learner_id = ?` (using just the first column) but not for `WHERE lesson_id = ?` (which would need the second column without the first).

A related concept is the **covering index** (`INCLUDE` clause in PostgreSQL 11+). A covering index includes additional columns in its leaf pages so that the query can be answered entirely from the index, without going back to the table. This is a useful optimization for queries that read a small set of columns from a large table:

```sql
CREATE INDEX idx_progress_lookup
ON progress (learner_id, lesson_id)
INCLUDE (status, completed_at);
```

A query like `SELECT status, completed_at FROM progress WHERE learner_id = ? AND lesson_id = ?` can be served entirely from this index, avoiding a table lookup.

---

## 5. When to Index (and When Not to)

Indexing is a balance between read performance and write cost. The decision to add an index should be deliberate.

**Index when:**

- The column appears in **`WHERE` clauses** of frequent queries. The classic case.
- The column is a **foreign key** used in joins. Most query planners benefit substantially from foreign-key indexes during joins, and most databases do **not** create them automatically; the schema designer must do so explicitly.
- The column appears in **`ORDER BY`** clauses of frequent queries, particularly when results are large enough that sorting them in memory is expensive.
- A composite of columns is queried together frequently, in which case a composite index is more efficient than separate single-column indexes.

**Do not index when:**

- The table has a **very high write rate** and the query patterns can tolerate slower reads. Each index multiplies write cost; on heavy-write tables, every index must be justified.
- The column has **low cardinality**—it has only a few distinct values. A B-tree index on a `boolean` or a `gender` column with three possible values typically does not help, because the query planner concludes that scanning the table is cheaper than scanning a fat index that points to a large fraction of the rows. (Partial indexes can sometimes help with low-cardinality columns when only one value is queried.)
- The table is **very small**. For a table with a few hundred rows, a full scan is faster than an index lookup. The database planner usually chooses the scan automatically; building an index is unnecessary.
- The query pattern uses constructs that **defeat the index**. The most famous case: `WHERE name LIKE '%foo%'` cannot use a standard B-tree index (a leading wildcard means there is no prefix to start the search with). Full-text search (GIN with `tsvector`) or trigram indexes are the correct tools for substring search.

A useful heuristic: **start with indexes on primary keys (which the database creates automatically), foreign keys, and the columns appearing in the most frequent queries' `WHERE` clauses. Add additional indexes when measurement shows specific queries are slow, not in anticipation.**

---

## 6. Inspecting Query Plans (EXPLAIN)

PostgreSQL's `EXPLAIN` and `EXPLAIN ANALYZE` commands show how the database plans to execute (or actually executed) a query. They are the primary tool for diagnosing index usage and query performance.

`EXPLAIN` shows the planned execution strategy without running the query:

```sql
EXPLAIN
SELECT * FROM progress
WHERE learner_id = '...' AND status = 'completed';
```

`EXPLAIN ANALYZE` runs the query and reports actual execution timing and row counts:

```sql
EXPLAIN ANALYZE
SELECT * FROM progress
WHERE learner_id = '...' AND status = 'completed';
```

Key things to look for in the output:

- **`Seq Scan`**: a sequential scan, examining every row in the table. For large tables, this typically indicates a missing or unusable index.
- **`Index Scan`**: the database is using an index. The output names which index is being used.
- **`Index Only Scan`**: the query is satisfied entirely from the index without touching the table—a sign that a covering index is working.
- **`Bitmap Index Scan` / `Bitmap Heap Scan`**: a hybrid approach for queries that match many rows.
- **Estimated vs actual row counts**: large discrepancies suggest stale statistics; running `ANALYZE` on the table refreshes them.
- **`Rows Removed by Filter`**: rows that the index returned but that an additional filter discarded; suggests the index could be more selective.

Reading `EXPLAIN` output is an essential skill for anyone working on query performance. It is the only way to know whether an index is actually being used; assuming the planner will use an index because it exists is unreliable.

---

## 7. Example: Educational Coding App for Kids

Consider the indexing plan for **CodeCub**, an educational coding app for children aged 6–12, with tables for parents, learners, courses, lessons, progress, and achievements (as described in the Data Modeling document).

**Query 1 — Look up a parent by email at login.**

```sql
SELECT id FROM parents WHERE email = ?;
```

This query runs on every login attempt. It must be fast and must use an index.

```sql
CREATE UNIQUE INDEX idx_parents_email ON parents (email);
```

A unique index serves two purposes: it accelerates the lookup, and it enforces the database constraint that emails are unique. Equality lookup on a B-tree index is `O(log n)`.

**Query 2 — Get all progress records for a specific learner.**

```sql
SELECT lesson_id, status, completed_at
FROM progress
WHERE learner_id = ?;
```

This is the dashboard query, run every time a parent or child opens the app. The `learner_id` foreign key needs an index:

```sql
CREATE INDEX idx_progress_learner ON progress (learner_id);
```

If the dashboard frequently filters further by status (e.g., "show only completed lessons"), a composite index would be more efficient:

```sql
CREATE INDEX idx_progress_learner_status ON progress (learner_id, status);
```

This composite serves both the unfiltered `WHERE learner_id = ?` query (using the leading column) and the filtered `WHERE learner_id = ? AND status = ?` query (using both).

**Query 3 — Find the specific progress row for a learner on a specific lesson.**

```sql
SELECT * FROM progress
WHERE learner_id = ? AND lesson_id = ?;
```

This query runs every time a child attempts a lesson and the system needs to read or update their progress. The optimal index is composite, with a uniqueness constraint:

```sql
CREATE UNIQUE INDEX idx_progress_learner_lesson
ON progress (learner_id, lesson_id);
```

The uniqueness constraint encodes the business rule that each learner has at most one progress row per lesson. The index also accelerates lookups on `learner_id` alone (using the leading column).

**Query 4 — Search lessons by tag (e.g., "find all lessons tagged 'loops'").**

If lessons have a `tags` column of type `text[]` or `jsonb`:

```sql
SELECT id, title FROM lessons
WHERE tags @> ARRAY['loops'];
```

A B-tree index does not help here. The right tool is GIN:

```sql
CREATE INDEX idx_lessons_tags ON lessons USING GIN (tags);
```

GIN supports the array containment operator `@>` and similar JSONB operations efficiently.

**Query 5 — Find a learner's recent activity (chronological feed).**

```sql
SELECT lesson_id, completed_at FROM progress
WHERE learner_id = ?
ORDER BY completed_at DESC
LIMIT 20;
```

A composite index on `(learner_id, completed_at DESC)` serves this efficiently:

```sql
CREATE INDEX idx_progress_learner_completed
ON progress (learner_id, completed_at DESC);
```

The descending order in the index definition matches the query's `ORDER BY` clause, allowing the database to read directly in the desired order without a sort step.

**Indexes deliberately not added at launch:**

- An index on `progress.status` alone. Status is low-cardinality (a handful of distinct values), and queries filtering only on status without `learner_id` are rare.
- An index on `learners.age_band` alone. Same reasoning—low cardinality, and `age_band` is almost always used in combination with another filter.
- Indexes on every foreign key by default. Indexes are added based on observed query patterns, not as a reflex.

The full launch index set:

```sql
CREATE UNIQUE INDEX idx_parents_email ON parents (email);
CREATE INDEX idx_learners_parent ON learners (parent_id);
CREATE UNIQUE INDEX idx_progress_learner_lesson ON progress (learner_id, lesson_id);
CREATE INDEX idx_progress_learner_status ON progress (learner_id, status);
CREATE INDEX idx_progress_learner_completed ON progress (learner_id, completed_at DESC);
CREATE INDEX idx_lessons_course ON lessons (course_id, order_index);
CREATE INDEX idx_lessons_tags ON lessons USING GIN (tags);
CREATE INDEX idx_achievements_learner ON achievements (learner_id, awarded_at DESC);
```

This index set covers the dominant query patterns at launch. New indexes will be added as production query telemetry surfaces specific slow queries, verified through `EXPLAIN ANALYZE`.

---

## 8. Common Pitfalls

- **Over-indexing.** Every additional index slows every write. Tables with many indexes can spend more time maintaining indexes than processing the underlying data. Index deliberately, not reflexively.
- **Indexing low-cardinality columns.** A B-tree index on a boolean or gender column rarely helps because each index entry points to a large fraction of the table. Partial indexes on the rare value can help if the use case justifies them.
- **Missing index on foreign keys.** Most databases do not create FK indexes automatically; their absence produces slow joins and slow cascading deletes. Foreign keys are almost always worth indexing.
- **Wrong column order in composite indexes.** A composite index on `(b, a)` does not help a query filtering by `a` alone. Match the index column order to the dominant query patterns.
- **`LIKE '%foo%'` on a B-tree-indexed column.** Leading-wildcard `LIKE` patterns cannot use a B-tree index. Use full-text search (GIN with `tsvector`) or trigram indexes for substring search.
- **Functions on indexed columns in `WHERE` clauses.** `WHERE LOWER(email) = ?` cannot use an index on `email`. Either index the function expression (`CREATE INDEX ON parents (LOWER(email))`) or normalize at write time.
- **Stale statistics.** PostgreSQL uses table statistics to plan queries; outdated statistics produce bad plans. Auto-vacuum usually keeps them current, but explicit `ANALYZE` is sometimes necessary after large data changes.
- **Adding an index without verifying it is used.** Always check `EXPLAIN` output after adding an index. Indexes that the planner rejects are pure cost.
- **Indexing tiny tables.** For tables with a few hundred rows, a sequential scan is faster than an index lookup. Save the index budget for tables where it pays off.
- **Forgetting the `UNIQUE` constraint when uniqueness is required.** A non-unique index on a column that should be unique permits duplicate inserts; the constraint must be expressed explicitly through `UNIQUE` or `PRIMARY KEY`.

---

## 9. References

- PostgreSQL documentation — Indexes: https://www.postgresql.org/docs/current/indexes.html
- Use The Index, Luke!: https://use-the-index-luke.com/