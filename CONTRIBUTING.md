# Contributing

Use focused commits and keep backend, frontend, and documentation changes separated when possible.

Before opening a pull request:

```bash
cd backend
pytest
```

```bash
cd frontend
npm run build
```

Avoid committing local runtime files such as `.env`, virtual environments, build output, databases, or logs.
