# Good and bad tests

Behavior through the public seam. Code can change; the test should not.

## Good

```python
def test_create_user_makes_user_retrievable():
    user = create_user(name="Alice")
    assert get_user(user.id).name == "Alice"
```

```php
it('makes the user retrievable', function () {
    $user = createUser(['name' => 'Alice']);
    expect(User::query()->findOrFail($user->id)->name)->toBe('Alice');
});
```

- Names WHAT, not HOW
- Public API only
- Independent expected value (`"Alice"`, `15`)
- One logical assertion

## Bad — implementation-coupled

```python
def test_checkout_calls_payment_service_process():
    mock = mocker.patch.object(payment_service, "process")
    checkout(cart, payment)
    mock.assert_called_once_with(cart.total)
```

Tell: refactoring internals breaks the test; user-facing behavior did not change.

## Bad — tautological

```python
def test_calculate_total_sums_line_items():
    items = [{"price": 10}, {"price": 5}]
    expected = sum(i["price"] for i in items)
    assert calculate_total(items) == expected
```

```python
def test_calculate_total_sums_line_items():
    assert calculate_total([{"price": 10}, {"price": 5}]) == 15
```

## Bad — bypasses the seam

```python
def test_create_user_saves_to_database():
    create_user(name="Alice")
    row = db.query("SELECT * FROM users WHERE name = ?", ["Alice"])
    assert row
```

Use `get_user` / the HTTP JSON / the Pest acting-as response instead.
