# URL Shortener

A React web interface and FastAPI REST API that turn HTTP and HTTPS destinations into short links. PostgreSQL stores the links in a Docker volume.

## Run locally

Install Docker Engine or Docker Desktop with Docker Compose v2. From the repository root, run:

```sh
docker compose up --build --wait
```

Open `http://localhost:8000` to create a link, or visit `http://localhost:8000/docs` for the interactive API documentation. Set `APP_PORT` if port 8000 is already in use.

```sh
curl -fsS http://localhost:8000/health
curl -fsS -X POST http://localhost:8000/api/links \
  -H 'Content-Type: application/json' \
  -d '{"url":"https://example.com/guide"}'
```

Use the returned `short_url` in a browser, or pass it to `curl -i` to inspect the redirect. The link uses the host from the creation request. A link created through localhost works on that machine.

Stop the services with `docker compose down`. PostgreSQL data persists in the named volume. The Compose configuration binds the app to loopback and uses a development database password by default. Set `POSTGRES_PASSWORD` before initializing a new volume to override it.

See [PROJECT_REPORT.md](PROJECT_REPORT.md) for the architecture, API contract, and validation results.

### Build behind a TLS-inspecting proxy

If the package registries use your organization's trusted proxy certificate, pass the system CA bundle to the build:

```sh
BUILD_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt \
  docker compose -f compose.yaml -f compose.build-ca.yaml up --build --wait
```

The override mounts the bundle during dependency installation so npm and pip can verify TLS.
