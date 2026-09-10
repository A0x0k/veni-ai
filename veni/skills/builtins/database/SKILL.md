---
name: "Database"
description: "SQL, ORM patterns, query optimisation, migrations, and indexing"
triggers: ["sql", "database", "query", "orm", "migration", "postgres", "mysql", "sqlite", "index", "join", "transaction", "schema"]
version: "1.0.0"
author: "veni-team"
---

# Database Skill

## Always Flag
- String formatting in SQL: `f"SELECT * FROM users WHERE id={user_id}"` → parameterized only
- `SELECT *` in production code → list columns explicitly
- Missing `WHERE` on `UPDATE` or `DELETE` → always confirm intent
- Queries inside loops → N+1 problem; use JOIN or batch fetch
- Missing transaction on multi-step writes → partial failure leaves corrupt state

## Query Optimisation Checklist
Before suggesting a query, check:
1. Is there an index on every column in WHERE, JOIN ON, and ORDER BY?
2. Does the query return more rows than needed? Add LIMIT.
3. Are there subqueries that could be CTEs or JOINs?
4. Is `DISTINCT` hiding a JOIN problem?

## Index Rules
- Index foreign keys — always
- Composite index column order: most selective first, then range columns last
- Don't index columns with <10 distinct values (boolean, status enum)
- Partial indexes for sparse conditions: `WHERE deleted_at IS NULL`

## Django ORM Patterns
```python
# N+1 — flag this:
for user in User.objects.all():
    print(user.profile.bio)  # query per user

# Fix:
for user in User.objects.select_related('profile'):
    print(user.profile.bio)  # 1 query

# Bulk operations — never loop .save():
User.objects.bulk_create(users)
User.objects.filter(active=False).update(deleted_at=now())
```

## SQLAlchemy Patterns
```python
# Lazy loading trap — flag this in async context:
result = await session.execute(select(User))
user = result.scalar()
print(user.orders)  # triggers sync lazy load — will fail or block

# Fix: use selectinload or joinedload
result = await session.execute(
    select(User).options(selectinload(User.orders))
)
```

## Migration Safety
- Never drop a column in the same migration that removes code using it
- Add nullable columns first, backfill, then add NOT NULL constraint
- Test migrations on a copy of production data before deploying
