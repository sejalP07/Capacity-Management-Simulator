# Security

Do not commit real OAuth secrets, JWT secrets, database passwords, or production environment files.

Report security issues privately to the repository owner.

Production recommendations:

- Replace the default `JWT_SECRET`.
- Use HTTPS.
- Restrict CORS origins.
- Rotate OAuth credentials if they are exposed.
- Prefer managed PostgreSQL and Redis services with network-level access controls.
