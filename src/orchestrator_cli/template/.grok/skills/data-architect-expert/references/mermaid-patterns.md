# Mermaid patterns for data-architect-expert

## ER diagram (core)

```mermaid
erDiagram
    ACCOUNT ||--o{ MEMBERSHIP : has
    MEMBERSHIP }o--|| ORGANISATION : belongs_to
    ACCOUNT {
        uuid id PK
        string email UK
        timestamp created_at
    }
```

Cardinality: `||--||` one-one, `||--o{` one-many, `}o--o{` many-many (use junction entity in logical model).

## Migration phase flow

```mermaid
flowchart TD
    A[Phase 0: backup + test DB] --> B[Phase 1: additive columns]
    B --> C[Phase 2: backfill job]
    C --> D[Phase 3: NOT NULL + indexes]
    D --> E[Phase 4: drop legacy]
```

## Read replica / cache

```mermaid
flowchart LR
    App[Laravel App] --> Primary[(Primary DB)]
    App --> Replica[(Read Replica)]
    App --> Redis[(Cache)]
```

## Vector + relational (RAG)

```mermaid
erDiagram
    DOCUMENT ||--o{ CHUNK : splits_into
    CHUNK ||--o| EMBEDDING : maps_to
    DOCUMENT {
        bigint id PK
        string source_uri
    }
    CHUNK {
        bigint id PK
        bigint document_id FK
        int chunk_index
    }
```

Delegate embedding store details to `/vector-database-expert`.