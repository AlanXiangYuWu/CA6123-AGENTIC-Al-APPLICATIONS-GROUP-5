# Data Migration Strategies

**Category**: data_design
**Source**: AWS, Martin Fowler "Evolutionary Database"
**Use Case**: Architect Agent uses this when planning DB schema evolution or platform migration.

---

## 1. Overview

**Data migration** is the process of moving or transforming data from one form to another while keeping the system running and the data intact. Migrations come in two distinct flavors: **schema migrations** (changes to the structure of an existing database—adding columns, renaming tables, changing types) and **database-to-database migrations** (moving data from one database engine or instance to another, often across vendors or environments). Both are operationally consequential. Both can produce extended outages, data loss, and bugs that surface weeks after the migration if done poorly.

The disciplines that produce safe migrations are well-established. **Martin Fowler's "Evolutionary Database Design"** articulated the principles that underlie modern schema-migration practice: every change should be small, reversible, idempotent, and backward-compatible during the deployment window. The **expand/contract pattern** translates these principles into a concrete sequence for zero-downtime deployments. For database-to-database migrations, **lift-and-shift**, **refactor**, and **Strangler Fig** patterns describe the major strategic options, each with its own trade-offs.

This document covers both flavors of migration. It compares the major schema-migration tools across language ecosystems, presents the core principles of evolutionary database design, walks through the expand/contract pattern with a concrete example, surveys database-to-database migration patterns and tooling, and applies the analysis to a realistic schema change in an educational coding app. It closes with the pitfalls that produce most migration incidents.

---

## 2. Two Types of Migrations

The two migration types share some principles but differ substantially in operational character.

**Schema migrations within the same database.** Adding a column, dropping a column, changing a type, renaming a table, adding an index, adding a constraint, or restructuring a relationship. These changes happen continuously over a product's life as the data model evolves. They are typically authored as small, versioned scripts checked into source control alongside the application code, applied automatically as part of deployment, and tracked in a migrations metadata table that records which migrations have been applied. The work is incremental: hundreds of small migrations over years, not a few large ones.

**Database-to-database migrations.** Moving data from one database engine to another (MySQL to PostgreSQL), from one host to another (on-premises to cloud), from one major version to another with breaking changes, or from one vendor to another. These migrations are larger, rarer, and more strategic. They typically involve careful planning, extensive testing in staging, dual-write or replication windows, cutover plans, and rollback procedures. A given system might undergo such a migration once every few years.

The shared principles—small changes where possible, reversibility, validation, and minimizing downtime—apply to both. The tactics differ because schema migrations operate within a running database while database-to-database migrations move data between systems.

---

## 3. Schema Migration Tools

Every modern language ecosystem has at least one well-supported schema-migration tool. The choice usually follows the application's primary language and ORM.

| Tool | Stack | Strengths |
|---|---|---|
| **Alembic** | Python, particularly with SQLAlchemy | Tight SQLAlchemy integration; autogenerates migrations from model changes; clean up/down semantics. The default for FastAPI and most modern Python web stacks. |
| **Flyway** | JVM, multi-language | Plain SQL migrations with predictable execution; widely used in enterprise Java environments; supports many databases. |
| **Liquibase** | Multi-language | XML, YAML, JSON, or SQL migration files; sophisticated change-tracking; rollback support; preferred when database changes need to be language-agnostic and reviewable by DBAs. |
| **Prisma Migrate** | Node.js / TypeScript with Prisma ORM | Generates SQL from schema definitions; integrates with Prisma's type-safe client; the modern default for Prisma-based stacks. |
| **Django migrations** | Python / Django | Built into Django; autogenerates migrations from model changes; tightly coupled with Django's ORM. |
| **Rails Active Record migrations** | Ruby / Rails | Built into Rails; the original modern schema-migration tool, dating from 2007; influential on every later tool. |
| **TypeORM / MikroORM migrations** | Node.js / TypeScript | Common alternatives to Prisma in Node.js stacks. |

The differences between tools are operationally smaller than they appear. All major tools support versioned, repeatable, reversible migrations; they differ in how migrations are authored (SQL vs. ORM-generated), how they handle conflicts when multiple developers create migrations in parallel, and how they integrate with the application's deployment pipeline. **Choose the tool that matches the primary stack**; switching tools later is rarely justified.

---

## 4. Migration Principles (Reversible, Idempotent, Backward-Compatible)

Martin Fowler's "Evolutionary Database Design" articulates the principles that produce safe schema migrations.

**Always reversible.** Every migration has both an "up" (apply) and a "down" (revert) script. If a deployment goes wrong, the down script restores the prior schema. Reversibility is not always strictly possible (a migration that drops a column cannot recover the dropped data), but the down script must restore the structure even if it cannot restore the data. The discipline of writing down scripts catches careless changes during code review.

**Always idempotent.** Re-running a migration must not break anything. Migration tools track which migrations have been applied and refuse to re-run them, but the underlying SQL should still be safe to run twice. `CREATE TABLE IF NOT EXISTS`, `ADD COLUMN IF NOT EXISTS` (where supported), and similar guards make recovery from partial failures safe.

**Backward compatible during the deployment window.** A migration that adds a required column with no default breaks the previous version of the application. During a rolling deployment, both versions must be able to operate against both the old and new schema. The discipline is to make schema changes additive: add columns as nullable or with defaults, deprecate before removing, and split irreversible changes into multiple deployments.

**Small and frequent.** Many small migrations over many releases are operationally safer than a few large migrations. A migration that touches one table is easy to review, test, and roll back; a migration that restructures ten tables is risky regardless of how carefully it is written. Big-bang migrations almost always produce avoidable incidents.

**Tested in staging against representative data volumes.** A migration that runs in five seconds against a 10,000-row test database may run for an hour against a 10-million-row production database, and during that hour it may hold locks that block production traffic. Test migrations against data shapes and volumes that approximate production.

**Authored alongside the application change.** Schema changes are part of the feature, not a separate workstream. A pull request that introduces a new column should also introduce the migration that adds it, the application code that uses it, and the tests that verify the combined behavior.

---

## 5. Zero-Downtime Migration: Expand/Contract Pattern

The **expand/contract pattern** (sometimes called **expand/migrate/contract**) is the standard technique for evolving schemas without downtime. It splits a schema change that would otherwise be a single breaking deployment into a sequence of small, individually safe deployments.

**Phase 1 — Expand.** Add the new schema element (column, table, index) without removing the old one. The application is unchanged at this stage; both old and new structures exist, but only the old one is in use.

**Phase 2 — Migrate (write to both).** Update the application to write to both the old and new structures. Reads still come from the old structure. Behind the scenes, a one-time backfill populates the new structure with data from the old. After this phase, the new structure is fully populated and stays current.

**Phase 3 — Cut over (read from new).** Update the application to read from the new structure. The old structure is still being written but is no longer read. Verify the new structure is producing correct results.

**Phase 4 — Contract.** Stop writing to the old structure. Drop the old structure in a final migration.

Each phase is its own deployment. Between phases, the system is in a consistent intermediate state and can be rolled back to the previous deployment without data loss. The total elapsed time from expand to contract is typically days or weeks—long enough to verify each phase—not minutes.

The pattern handles every common schema change:

- **Renaming a column**: add the new column (expand), write to both, copy historical data, switch reads, stop writing to the old, drop the old.
- **Splitting a column**: add the new columns, write parsed values to them as well as to the original, backfill, switch reads, drop the original.
- **Changing a type**: add a new column with the new type, write both representations, backfill, switch reads, drop the old.
- **Splitting a table**: similar pattern, applied at the table level with dual writes.

The trade-off is that expand/contract takes longer than a single breaking change. The reason to use it is that during the entire sequence, the application can be deployed and rolled back without coordination with the database; no production outage is required.

---

## 6. Database-to-Database Migration Patterns

Moving from one database engine or instance to another is operationally larger than schema evolution within a single database. Three patterns dominate.

**Lift-and-shift.** Copy the data as-is into the new database, with minimal structural change. Fastest to execute. Useful when the goal is platform migration (e.g., on-premises Postgres to cloud-managed Postgres) without restructuring the data. The downside is that any structural debt in the source carries over; the migration produces a working system on the new platform but does not improve the data model.

**Refactor.** Restructure the data during the migration—normalize, split tables, change types, consolidate redundant fields. Slower and riskier, because the migration logic is more complex and the validation surface is larger. Justified when the target system is meaningfully better than the source and the team has the budget to refactor as part of the move.

**Strangler Fig.** Named after the strangler fig tree, which gradually grows around a host tree until the host is gone. The pattern: introduce the new database alongside the old, route a small percentage of traffic to it, gradually increase the percentage as confidence grows, and eventually retire the old database. Strangler Fig is the safest pattern for high-stakes migrations because it provides continuous validation under real production traffic and allows rollback at any percentage. It requires application changes to support routing decisions and dual writes.

**Tooling for cross-database migration:**

- **AWS DMS (Database Migration Service)** — managed migration service supporting many source/target combinations, including ongoing replication for Strangler Fig-style cutovers.
- **pgloader** — open-source tool for migrating data into PostgreSQL from MySQL, SQLite, MS SQL, and others, with type-mapping and concurrency support.
- **Apache NiFi** — general-purpose data pipeline tool; used for complex ETL during migrations and for ongoing data movement.
- **Database-native logical replication** — PostgreSQL logical replication, MySQL binlog replication, and similar features support continuous replication during migration windows.

The choice of tool matters less than the discipline: validate every step, replicate continuously rather than copying once, and plan rollback at every stage.

---

## 7. Example: Educational Coding App for Kids

Consider a real schema change for **CodeCub**: the `learners` table currently has an `age_band` column (`'6-8'`, `'9-10'`, `'11-12'`), and the team wants to add a `level` column to track the learner's current skill level (`'beginner'`, `'intermediate'`, `'advanced'`) for use in lesson recommendation.

The simplest version—a single migration that adds the column—is unsafe if the application requires the column to be populated and a rolling deployment is in progress.

The expand/contract sequence:

**Phase 1 — Expand. Add the column as nullable.**

```sql
-- migration: add_level_to_learners.up.sql
ALTER TABLE learners
ADD COLUMN level TEXT;

CREATE INDEX idx_learners_level ON learners (level);
```

```sql
-- migration: add_level_to_learners.down.sql
DROP INDEX idx_learners_level;
ALTER TABLE learners DROP COLUMN level;
```

The column is added as nullable. Existing rows have `NULL` for `level`. The previous version of the application ignores the column. The new version of the application can read it but should treat `NULL` as "level not yet determined." Deployment of this migration is safe because the column's existence does not affect the previous version of the code.

**Phase 2 — Migrate (write to both, backfill historical).**

The application is updated to populate `level` whenever a learner is created or whenever a relevant event (lesson completion, age-band transition) occurs.

```python
# application code, simplified
def update_learner_after_lesson(learner_id, lesson_id):
    learner = get_learner(learner_id)
    progress = get_progress(learner_id)

    # legacy logic continues to update existing fields
    update_streak(learner_id, ...)

    # new: also update level
    new_level = compute_level(learner.age_band, progress)
    update_learner_level(learner_id, new_level)
```

A one-time backfill populates `level` for existing learners:

```sql
-- backfill, run once
UPDATE learners
SET level = CASE
    WHEN age_band = '6-8' THEN 'beginner'
    WHEN age_band = '9-10' THEN 'intermediate'
    WHEN age_band = '11-12' THEN 'advanced'
END
WHERE level IS NULL;
```

For very large tables, backfills are typically batched (`UPDATE ... WHERE id BETWEEN ? AND ?` in a loop) to avoid long-running transactions that hold locks.

After Phase 2, the `level` column is fully populated and stays current. The application is not yet using `level` for any reads.

**Phase 3 — Cut over (read from new).**

The application is updated to read `level` for lesson recommendation:

```python
def recommend_next_lesson(learner_id):
    learner = get_learner(learner_id)
    # was: select lessons by age_band only
    # now: select lessons by level (with age_band as fallback)
    return select_lessons(level=learner.level, age_band=learner.age_band)
```

This change is observed in production. If lesson recommendations look wrong, roll back to the previous version (which still works because Phase 2 left both fields populated). After Phase 3 has been live and verified, proceed to Phase 4.

**Phase 4 — Contract (only if applicable).**

In this example, no field is being removed; the migration adds capability rather than replacing existing behavior. The "contract" phase is empty. In a more invasive migration—say, replacing `age_band` entirely with `level`—the contract phase would drop `age_band` and any code that used it, after enough time has passed to be confident the new field is sufficient.

If, in a later iteration, the team decides to add `NOT NULL` to `level` (now that all rows have values):

```sql
-- migration: make_level_required.up.sql
ALTER TABLE learners
ALTER COLUMN level SET NOT NULL;
```

This migration is safe only after Phase 2's backfill has completed and the application has stopped writing `NULL` values. Running it earlier would produce an error.

The full sequence is several deployments over a period of days or weeks, each individually safe and reversible. No phase requires downtime. If any phase fails, the system rolls back cleanly to the previous deployment.

---

## 8. Common Pitfalls

- **Long-running migrations holding locks.** A simple `ALTER TABLE ADD COLUMN` on a 100-million-row table can hold a lock for minutes, blocking production traffic. Tools like **pt-online-schema-change** (MySQL) and **gh-ost** (MySQL, GitHub's open-source online schema change tool), or PostgreSQL's lock-free migrations using `ADD COLUMN ... NOT NULL DEFAULT` carefully (PostgreSQL 11+ supports this without a full table rewrite), avoid the lock.
- **Data loss from incomplete validation.** A migration that transforms data should be validated against representative samples in staging and against checksum comparisons in production. "It seemed to work" is not validation.
- **Orphaned references when changing foreign-key structure.** Restructuring relationships between tables can leave foreign keys pointing at deleted or moved rows. Validate referential integrity after any FK-touching migration.
- **Charset and encoding mismatches.** Migrating from databases with different default encodings (latin-1 to UTF-8, for example) can silently corrupt characters outside the ASCII range. Verify encoding handling for any cross-database migration.
- **Forgetting to update the application alongside the schema.** Application code that assumes the old schema fails when the new schema is deployed; application code that assumes the new schema fails before the migration runs. Always coordinate the application change and the schema change to be backward-compatible during the deployment window.
- **Skipping the expand/contract pattern for "small" changes.** A column rename looks small and is sometimes done as a single migration; the result is a deployment window during which old and new code disagree about which column to use. Apply expand/contract for any schema change that affects column or table names, types, or constraints.
- **Not testing the down migration.** Reversibility is only meaningful if the down script actually works. Test it as part of the migration's own validation.
- **Migrations that depend on application state.** A migration that runs at deploy time should not depend on application logic running concurrently. Migrations should be self-contained SQL or pure data transformations.
- **Inadequate rollback planning for database-to-database migrations.** A Strangler Fig migration that has shifted 50% of traffic to a new database cannot easily be rolled back if dual writes were not maintained. Plan rollback at every traffic percentage, not just at the start.
- **Ignoring auto-vacuum and statistics updates.** Large data changes can leave PostgreSQL's planner with outdated statistics, producing bad query plans until `ANALYZE` runs. Run `ANALYZE` explicitly after large migrations.

---

## 9. References

- AWS — Cloud Data Migration: https://aws.amazon.com/cloud-data-migration/
- Martin Fowler — Evolutionary Database Design: https://martinfowler.com/articles/evodb.html