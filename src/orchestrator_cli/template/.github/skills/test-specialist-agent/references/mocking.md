# When to mock

Mock **system boundaries** only:

- External APIs (payment, email, KYC)
- Time / randomness
- The network

Prefer a real **test** / `:memory:` database over a mocked one. Never a live DB.

Do **not** mock:

- Your own services, actions, or Eloquent models
- Internal collaborators you control

## Inject the boundary

```python
def process_payment(order, payment_client):
    return payment_client.charge(order.total)
```

Not `StripeClient(os.environ["STRIPE_KEY"])` constructed inside the unit under test.

## SDK-style over a generic fetcher

```python
api = {
    "get_user": lambda id: fetch(f"/users/{id}"),
    "create_order": lambda data: fetch("/orders", method="POST", body=data),
}
```

Each mock returns one shape. No `if endpoint == …` inside the test double.
