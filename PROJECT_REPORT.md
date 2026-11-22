# Containerized URL Shortener | Project Report

## Objective

Build a web application that turns a long HTTP or HTTPS URL into a compact link. The application should run from a single Docker Compose command and preserve links when containers are replaced.

## Architecture

| Component | Responsibility |
| --- | --- |
| React and Vite | Collect a destination URL, show the resulting short link, and copy it to the clipboard |
| FastAPI and Uvicorn | Serve the built frontend, validate requests, generate link codes, and issue redirects |
| PostgreSQL 17 | Store each code and destination in the `links` table |
| Docker Compose | Build the application image, start both services, and attach persistent storage |

A multi-stage Docker build compiles the React bundle with Node.js and copies it into the Python image. FastAPI serves the bundle and API on the same origin. Compose connects the API and database over its internal network and waits for PostgreSQL before starting the API. PostgreSQL stores its data in the `pgdata` named volume.

## Request flow

1. React sends a JSON destination to `POST /api/links`.
2. FastAPI validates the URL and generates an eight-character alphanumeric code with Python's `secrets` module.
3. PostgreSQL enforces uniqueness through the code's primary key. The API retries a code collision before returning an error.
4. The browser displays the returned short link. Requests to that link look up its code and receive an HTTP redirect to the stored destination.

| Method and path | Successful result | Other outcomes |
| --- | --- | --- |
| `GET /` | React application | |
| `POST /api/links` | `201` with the code, short URL, and destination | `422` for invalid destinations, `503` if code allocation is exhausted |
| `GET /s/{code}` | `307` with the destination in the `Location` header | `404` for unknown codes, `422` for malformed codes |
| `GET /health` | `200` when the app can query its table | `503` when the database query fails |

## Deployment scope

The project targets local development. Anyone who can reach the service can create a short link. A public deployment would need a public origin, HTTPS, and measures to handle abuse. The application stores link mappings only.

## Validation results

Verified in the Codex cloud environment with Docker Compose v2.

| Check | Result |
| --- | --- |
| Build the React bundle and application image | Passed |
| Start PostgreSQL and the app and wait for both health checks | Passed |
| Create a link in Chromium, copy it, and check its redirect | Passed |
| Create a link through the REST API and verify the exact redirect destination | Passed |
| Reject unsupported URL schemes and embedded credentials | Passed |
| Return the documented status for unknown and malformed codes | Passed |
| Recreate both containers and resolve a previously created link using the retained volume | Passed |

The cloud build used the system CA bundle so dependency downloads could pass TLS verification through the network proxy.
