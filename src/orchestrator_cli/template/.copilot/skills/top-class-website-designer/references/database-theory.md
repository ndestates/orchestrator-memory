# Database Theory Quick Reference (MySQL Focus)

## Normalization

- **1NF**: Atomic values, no repeating groups.
- **2NF**: Full functional dependency on candidate key (no partial).
- **3NF**: No transitive dependencies.
- **BCNF**: Every determinant is a candidate key.
- **4NF**: No multi-valued dependencies.
- **5NF**: Join dependency satisfaction (rarely needed in practice).

Always document the highest normal form achieved and any intentional denormalization with measured justification (read vs write ratio, query patterns).

## Indexing Theory (InnoDB)

- Clustered primary key: data ordered by PK. Choose carefully (monotonically increasing preferred for insert locality).
- Secondary indexes: B+ tree, leaf nodes contain PK.
- Covering index: index contains all columns needed by query → index-only scan.
- Selectivity: high cardinality columns preferred for first key parts.
- Composite indexes: leftmost prefix rule. Order by equality filters then range.
- Invisible indexes (MySQL 8): for safe testing of index impact.
- Histograms: improve cardinality estimates for non-indexed or skewed data.

Always pair proposed indexes with representative EXPLAIN ANALYZE output when data is available.

## Transaction Isolation (InnoDB Defaults)

- REPEATABLE READ (default) + MVCC + gap locks → phantom prevention for most cases.
- Know when to drop to READ COMMITTED or raise to SERIALIZABLE.
- Explicit locking (SELECT ... FOR UPDATE / SHARE) with clear justification and deadlock awareness.

## CAP and Consistency Choices

For web systems:
- Strong consistency (MySQL primary) for financial, inventory, auth.
- Eventual consistency via caches, read replicas, or message queues for feeds, analytics, search.
- Document the consistency boundary explicitly in architecture diagrams or ADRs.
