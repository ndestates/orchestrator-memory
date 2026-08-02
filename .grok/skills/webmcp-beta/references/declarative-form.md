# WebMCP declarative form (beta snippet)

Attribute names follow Chrome’s declarative API and may change with the trial.

```html
<form
  toolname="bookSlot"
  tooldescription="Reserve a 30-minute consultation."
  toolautosubmit
>
  <label>
    Date
    <input
      type="date"
      name="date"
      toolparamdescription="Date of the booking"
      required
    />
  </label>
  <label>
    Time
    <input
      type="time"
      name="time"
      toolparamdescription="Start time (24-hour)"
      required
    />
  </label>
  <label>
    Name
    <input
      name="name"
      toolparamdescription="Full name of the guest"
      required
    />
  </label>
  <label>
    Email
    <input
      type="email"
      name="email"
      toolparamdescription="Confirmation email"
      required
    />
  </label>
  <button type="submit">Book</button>
</form>
```

Notes:

- Prefer semantic HTML and clear labels for humans and agents.
- Do not put API keys or tokens in attributes.
- Non-readonly actions should still surface a human confirmation step in the app.

Docs: https://developer.chrome.com/docs/ai/webmcp/declarative-api  
