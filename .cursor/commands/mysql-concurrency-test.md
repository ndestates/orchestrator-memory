# /mysql-concurrency-test

> Design MySQL concurrency tests adapted for Laravel 12 + Eloquent (lockForUpdate, DB::transaction, queues, optimistic/pessimistic locking).

**Platform:** Cursor · same skill as Grok `/mysql-concurrency-test` · Claude `/mysql-concurrency-test`

Execute this skill for the current project. Cache-first. Manifest-first.

# MySQL Concurrency Tests (Laravel/Eloquent)

**Source (distilled & adapted):** Anthropic Prompt Engineering patterns + Laravel Eloquent + MySQL 8 best practices.  
**Primary reusable prompt:** `.grok/prompts/mysql-concurrency-test.md`  
**When to use:** Race conditions, lost updates, deadlocks in Eloquent models, queued jobs, or critical inventory/wallet flows.

## Quick Laravel/Eloquent Patterns (grounded in mysql-database-expert + laravel-expert-agent)

### Pessimistic Locking (recommended for most money/stock cases)
```php
DB::transaction(function () {
    $product = Product::where('id', $id)
        ->lockForUpdate()
        ->firstOrFail();

    if ($product->stock < $quantity) {
        throw new \Exception('Insufficient stock');
    }

    $product->decrement('stock', $quantity);
    // create order line etc.
});
```

### Optimistic Locking (lighter, with version column)
Add `version` unsigned integer column (or rely on `updated_at`).

```php
$product = Product::findOrFail($id);

$updated = Product::where('id', $product->id)
    ->where('version', $product->version)
    ->update([
        'stock' => DB::raw('stock - ' . $quantity),
        'version' => $product->version + 1,
    ]);

if (! $updated) {
    // retry or fail
}
```

### Queue / Job Safety
- Use `ShouldBeUnique` on jobs when possible.
- Wrap critical logic in `DB::transaction` inside the job.
- Consider `unique_for` + database unique job table.

### Testing Concurrency in Laravel
- Real concurrency requires multiple processes/workers (not just faking).
- Common pattern: custom Artisan command that spawns `Symfony\Component\Process\Process` instances.
- Use test database + `RefreshDatabase` trait carefully (transactions don't cross processes well).
- Verify with:
  ```bash
  ddev mysql -e "SHOW ENGINE INNODB STATUS\G"
  ```

## How to use the full grounded prompt
```
/load-project-cache-first
Read .grok/prompts/mysql-concurrency-test.md

[describe your Eloquent models + operation]
```

The prompt forces the grounded pattern:
- First extract `<quotes>` from your actual Eloquent code + DB output.
- Only generate test plans supported by those quotes.
- Explicit refusal when evidence is missing.

## Project Integration
- Cache first (manifest + CONCERNS + TESTING).
- Use DDEV for all DB commands.
- Combine with:
  - `/mysql-database-expert` for schema, EXPLAIN, indexes
  - `/laravel-expert-agent` for services, resources, observers
  - `/test-safety-agent` before introducing concurrent test logic
- Always cite the model file + line numbers + DB output in responses.
- Update `reports/research/prompt-patterns.md` citation when using these patterns.

**See also:** `reports/research/prompt-patterns.md` (grounded RAG + complex structure), mysql-database-expert, laravel-expert-agent.

User focus (optional): use any extra chat text as $ARGUMENTS.
