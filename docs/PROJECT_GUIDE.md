# Project Guide: Containerized URL Shortener (Project 23)

This guide explains the whole project in plain language. You do not need to know Docker, Kubernetes or Ansible before you start. Each new word is explained the first time it appears, and there is a word list in [section 3](#3-words-you-will-see).

If you only have five minutes, read sections 1, 2 and 5.

---

## Contents

1. [What this project is](#1-what-this-project-is)
2. [The big picture](#2-the-big-picture)
3. [Words you will see](#3-words-you-will-see)
4. [The three parts of the app](#4-the-three-parts-of-the-app)
5. [What happens when you use it](#5-what-happens-when-you-use-it)
6. [A tour of the folders and files](#6-a-tour-of-the-folders-and-files)
7. [Run it on your computer with Docker Compose](#7-run-it-on-your-computer-with-docker-compose)
8. [Run it on Kubernetes with Ansible](#8-run-it-on-kubernetes-with-ansible)
9. [How the Kubernetes setup works](#9-how-the-kubernetes-setup-works)
10. [Testing](#10-testing)
11. [Problems we found and how we fixed them](#11-problems-we-found-and-how-we-fixed-them)
12. [Command cheat sheet](#12-command-cheat-sheet)
13. [When something goes wrong](#13-when-something-goes-wrong)
14. [What is not done yet](#14-what-is-not-done-yet)
15. [Other documents](#15-other-documents)

---

## 1. What this project is

A **URL shortener** turns a long web address into a short one.

```
Long:   https://example.com/blog/2026/how-to-set-up-kubernetes-on-your-laptop?ref=newsletter
Short:  http://shortener.test/s/aB3dE9xY
```

When someone opens the short link, they are sent to the long one.

The app itself is small. The point of the project is to show how a real app is **packaged, deployed and scaled** using common DevOps tools. The project brief asks for:

| Brief item | What it means | Where it is in this repo |
|---|---|---|
| Client, API, Database | A web page, a server program, and a database | `frontend/`, `app.py`, PostgreSQL |
| Docker | Package the app so it runs the same everywhere | `Dockerfile`, `compose.yaml` |
| Kubernetes | Run several copies and let them find the database by name | `k8s/` |
| Ansible | Deploy everything with one command | `ansible/deploy.yml` |
| Extension: HPA and Ingress | Add copies automatically under load, and give the app one web address | `k8s/api.yaml.j2` |

---

## 2. The big picture

### On your laptop (Docker Compose)

```
  Your browser
       |
  http://localhost:8000
       |
  +----v-----------------+        +------------------+
  |  app container       | -----> |  db container    |
  |  (web page + API)    |        |  (PostgreSQL)    |
  +----------------------+        +--------+---------+
                                           |
                                     pgdata volume
                                  (links saved on disk)
```

### On Kubernetes (minikube)

```
  Your browser
       |
  http://shortener.test
       |
  +----v------------------------+
  |  Ingress (front door)       |   one address for the whole app
  +----+------------------------+
       |
  +----v------------------------+
  |  Service: shortener-api     |   spreads requests across the copies
  +----+---------+---------+----+
       |         |         |
    +--v--+   +--v--+   +--v--+
    | API |   | API |   | API |    2 to 8 copies (pods)
    +--+--+   +--+--+   +--+--+    the HPA adds or removes copies
       |         |         |
       +---------+---------+
                 |
       "db" (found by name, not by IP address)
                 |
  +--------------v--------------+
  |  Service: db                |
  +--------------+--------------+
                 |
  +--------------v--------------+
  |  PostgreSQL pod             |
  |  + 1 GiB disk (PVC)         |   links survive restarts
  +-----------------------------+

  Ansible runs on your computer and sets all of this up with one command.
```

---

## 3. Words you will see

| Word | Simple meaning |
|---|---|
| **Container** | A sealed box that holds a program and everything it needs. It runs the same on any computer. |
| **Image** | The recipe for a container. You build an image once, then start as many containers from it as you like. |
| **Docker** | The tool that builds images and runs containers. |
| **Dockerfile** | The instructions Docker follows to build the image. |
| **Docker Compose** | Starts several containers together (here: the app and the database) from one file, `compose.yaml`. |
| **Volume** | A folder on disk that a container can use. Data in it stays when the container is deleted. |
| **Kubernetes (K8s)** | A system that runs containers across one or more machines, restarts them if they crash, and adds more copies when needed. |
| **minikube** | A small Kubernetes that runs on your own computer, for learning and testing. |
| **Cluster** | The group of machines Kubernetes manages. With minikube it is just one. |
| **Namespace** | A named folder inside the cluster. Everything for this app lives in `url-shortener`. |
| **Pod** | The smallest thing Kubernetes runs. Here each pod holds one container. |
| **Deployment** | Tells Kubernetes "keep N copies of this pod running". If one dies, it makes a new one. |
| **Replica** | One copy of a pod. |
| **Service** | A fixed name and address in front of a group of pods. Other pods use the name, so they never need to know IP addresses. |
| **Service discovery** | Finding another part of the system by its name (like `db`) instead of a fixed address. |
| **Ingress** | The front door. It takes web requests for `shortener.test` from outside the cluster and passes them to the right Service. |
| **Ingress controller** | The program that actually runs the front door. Here it is ingress-nginx. |
| **HPA (Horizontal Pod Autoscaler)** | Watches CPU use and adds or removes API copies automatically. |
| **metrics-server** | Measures how much CPU and memory each pod uses. The HPA reads these numbers. |
| **PVC (PersistentVolumeClaim)** | A request for disk space that stays even if the pod is deleted. The database keeps its data here. |
| **Secret** | A Kubernetes object for private values such as passwords. |
| **Probe** | A health check Kubernetes runs on a pod. A *readiness* probe decides if the pod gets traffic. A *liveness* probe decides if the pod should be restarted. |
| **Rolling update** | Replacing old pods with new ones a few at a time, so the app never fully goes down. |
| **Ansible** | A tool that runs a list of setup steps for you. |
| **Playbook** | Ansible's list of steps, written in YAML. Ours is `ansible/deploy.yml`. |
| **Idempotent** | Running it again changes nothing if everything is already correct. |
| **API** | The part of the server that other programs (and our web page) talk to. |
| **Endpoint** | One address on the API, such as `POST /api/links`. |
| **Connection pool** | A small set of database connections that are opened once and reused, instead of opening a new one for every request. |
| **Load test** | Sending lots of fake traffic to see how the app behaves when busy. |
| **p95 latency** | 95 out of 100 requests were at least this fast. |
| **E2E test** | End-to-end test. A robot uses the real app in a real browser, the way a person would. |

---

## 4. The three parts of the app

### 4.1 Client (the web page)

- Folder: `frontend/`
- Built with **React** (a JavaScript library for web pages) and **Vite** (a tool that bundles the code).
- What you see: a box to paste a URL, a **Shorten** button, the short link, and a **Copy** button.
- The page talks to the API with `fetch('/api/links')`.
- The API serves the finished page itself, so there is no separate web server.

### 4.2 API (the server)

- File: `app.py`
- Built with **FastAPI** (a Python web framework) and run by **Uvicorn** (the program that serves it).
- It has these endpoints:

| Endpoint | What it does | Possible answers |
|---|---|---|
| `GET /` | Sends the web page | 200 |
| `POST /api/links` | Takes `{"url": "https://..."}` and makes a short link | 201 created, 422 bad URL, 503 database down |
| `GET /s/{code}` | Sends the browser to the long URL | 307 redirect, 404 unknown code, 422 badly formed code |
| `GET /health` | Says if the app can reach the database | 200 OK, 503 database down |
| `GET /docs` | Interactive API documentation | 200 |

Rules the API follows:

- Only `http://` and `https://` links are accepted.
- Links with a username or password inside them (like `https://user:pass@site.com`) are refused.
- Each short code is **8 random letters and digits**, made with Python's `secrets` module (safe randomness).
- If a code is already taken, it tries a new one, up to 5 times.
- If the database cannot be reached, the API answers **503 "Database unavailable"** instead of crashing.

### 4.3 Database

- **PostgreSQL 17**, using the official image.
- One table:

```sql
CREATE TABLE links (
    code text PRIMARY KEY,   -- the 8-character short code
    url  text NOT NULL       -- the original long URL
);
```

- The API creates this table when it starts. A database lock makes sure only one copy creates it, even if many start at once.

---

## 5. What happens when you use it

### Making a short link

1. You paste `https://example.com/guide` and press **Shorten**.
2. The page sends `POST /api/links` with that URL.
3. The Ingress (on Kubernetes) passes it to the `shortener-api` Service, which picks one API pod.
4. The API checks the URL is allowed.
5. It makes a random 8-character code, for example `aB3dE9xY`.
6. It borrows a database connection from its pool and saves `aB3dE9xY -> https://example.com/guide`.
7. It replies with:

```json
{
  "code": "aB3dE9xY",
  "short_url": "http://shortener.test/s/aB3dE9xY",
  "url": "https://example.com/guide"
}
```

8. The page shows the short link. **Copy** puts it on your clipboard.

### Opening a short link

1. Someone opens `http://shortener.test/s/aB3dE9xY`.
2. The API looks up `aB3dE9xY` in the database.
3. It answers **307 Temporary Redirect** with the long URL.
4. The browser goes there automatically.

---

## 6. A tour of the folders and files

```
DevOps-PBL/
|-- app.py                  The API (Python, FastAPI)
|-- requirements.txt        Python libraries the API needs, with exact versions
|-- frontend/               The web page (React)
|   |-- index.html
|   |-- main.jsx            Page logic: shorten, show link, copy
|   |-- style.css
|   `-- package.json        JavaScript libraries, with exact versions
|-- Dockerfile              How to build the app image
|-- .dockerignore           Files Docker should skip
|-- compose.yaml            Run app + database on your computer
|-- compose.build-ca.yaml   Extra setting for building behind a company proxy
|-- .env.example            Example settings for Compose (copy to .env)
|-- k8s/
|   |-- database.yaml       PostgreSQL: Service "db", disk (PVC), Deployment
|   `-- api.yaml.j2         API: Service, Deployment, HPA, Ingress (a template)
|-- ansible/
|   `-- deploy.yml          One-command deployment to Kubernetes
|-- scripts/
|   `-- loadtest.js         k6 load test (ramp and spike)
|-- e2e/                    Playwright browser and API tests
|   |-- playwright.config.js
|   `-- tests/
|       |-- api.spec.js     15 API tests
|       |-- ui.spec.js      7 browser tests
|       `-- docker.spec.js  2 tests that stop and restart containers
|-- docs/
|   `-- PROJECT_GUIDE.md    This guide
|-- README.md               Short setup instructions
|-- PRD.md                  Requirements and progress tracker
|-- PROJECT_REPORT.md       Architecture and validation report
`-- STRESS_TEST_RESULTS.md  Load test results, bugs and fixes
```

### How the image is built (`Dockerfile`)

The Dockerfile has **two stages**. This keeps the final image small.

1. **Stage 1 (Node.js):** install the JavaScript libraries and build the web page into plain files (`dist/`).
2. **Stage 2 (Python):** install the Python libraries, copy in `app.py` and the built page, and start Uvicorn.

Safety and size choices:

- The app runs as a normal user (number 10001), not as the all-powerful `root` user.
- All versions are fixed (pinned), so a build today matches a build next month.
- Uvicorn keeps idle connections open for 75 seconds (`--timeout-keep-alive 75`). This matches the Ingress, so it never reuses a connection the app has just closed.

---

## 7. Run it on your computer with Docker Compose

This is the quickest way to try the app.

**You need:** Docker with Compose v2.

```sh
git clone https://github.com/SumanthBHegde/DevOps-PBL.git
cd DevOps-PBL
docker compose up --build --wait
```

Open **http://localhost:8000**.

What Compose does:

- Builds the app image from the `Dockerfile`.
- Starts PostgreSQL and waits until it is healthy.
- Starts the app and waits until `/health` says OK.
- Saves links in a volume called `pgdata`, so they survive restarts.
- Only listens on your own computer (`127.0.0.1`), not your whole network.

Try the API from a terminal:

```sh
curl http://localhost:8000/health
curl -X POST http://localhost:8000/api/links \
  -H 'Content-Type: application/json' \
  -d '{"url":"https://example.com/guide"}'
```

Stop it:

```sh
docker compose down        # stop, keep saved links
docker compose down -v     # stop and delete saved links
```

**Settings:** copy `.env.example` to `.env` to change the port (`APP_PORT`) or the database password (`POSTGRES_PASSWORD`). The password only applies when the volume is first created.

---

## 8. Run it on Kubernetes with Ansible

### What you need

| Tool | Why |
|---|---|
| Docker | Builds the image and runs minikube |
| minikube | The local Kubernetes cluster |
| kubectl | Talks to the cluster |
| ansible-core | Runs the playbook |

### Step 1: Start the cluster and turn on add-ons

```sh
minikube start --cpus 4 --memory 4g
minikube addons enable storage-provisioner
minikube addons enable default-storageclass
minikube addons enable metrics-server
minikube addons enable ingress
```

The add-ons give you disk space for the database, CPU numbers for the HPA, and the Ingress front door.

### Step 2: Build the image and give it to minikube

```sh
docker build -t url-shortener:project23 .
minikube image load url-shortener:project23
```

minikube has its own image store, separate from your computer's Docker. `image load` copies the image across.

### Step 3: Deploy with one command

```sh
ansible-playbook -i localhost, ansible/deploy.yml \
  -e kube_context=minikube -e app_image=url-shortener:project23
```

The playbook does these steps in order:

1. Checks you passed `kube_context` and `app_image`.
2. Creates the `url-shortener` namespace.
3. Checks if a database password already exists.
4. If not, makes a random 40-character password and stores it in the `shortener-db` Secret. The password is never printed or saved in Git.
5. Applies `database.yaml` and `api.yaml.j2` (filling in the image name and host name).
6. Waits until the database and API are fully running.

Run it a second time and it reports `changed=0`. That means it is **idempotent**: it only changes what is different.

### Step 4: Open the app

Tell your computer that `shortener.test` means the minikube address:

```sh
echo "$(minikube ip) shortener.test" | sudo tee -a /etc/hosts
```

Now open **http://shortener.test**.

### Step 5: Check it

```sh
kubectl -n url-shortener get pods        # 2 API pods + 1 db pod, all Running
kubectl -n url-shortener get pvc         # shortener-data is Bound
kubectl -n url-shortener get hpa         # shows CPU use and replica count
kubectl -n url-shortener top pods        # CPU and memory per pod
curl -H 'Host: shortener.test' http://$(minikube ip)/health
```

The HPA shows `<unknown>` for about 2 minutes after a fresh start. That is normal: metrics-server needs time to collect its first numbers.

### Releasing a new version

Build with a **new tag**, load it, and run the playbook again with that tag:

```sh
docker build -t url-shortener:v2 .
minikube image load url-shortener:v2
ansible-playbook -i localhost, ansible/deploy.yml \
  -e kube_context=minikube -e app_image=url-shortener:v2
```

Kubernetes swaps the pods one by one (a rolling update). In our tests this caused zero failed requests, even under heavy load.

---

## 9. How the Kubernetes setup works

### 9.1 Service discovery: how the API finds the database

The API connects to:

```
postgresql://shortener@db:5432/shortener
```

`db` is the name of a Kubernetes **Service**. Kubernetes has a built-in phone book (DNS). Any pod can ask "where is `db`?" and get the right address, even if the database pod moves or restarts with a new IP. No IP addresses are written anywhere.

The full name is `db.url-shortener.svc.cluster.local`, but inside the same namespace `db` is enough.

### 9.2 Scaling: how the HPA adds copies

| Setting | Value |
|---|---|
| Minimum copies | 2 |
| Maximum copies | 8 |
| Target | 65% of each pod's CPU request |
| CPU request per pod | 100m (one tenth of a CPU core) |

How it behaves:

- **Busy:** if average CPU goes above 65%, the HPA adds pods. In our tests it went from 2 to 8 within about a minute.
- **Quiet:** after load stops, it waits about 5 minutes (so it does not flip back and forth), then goes back to 2. In our tests this took 6 to 7 minutes.
- **Short spikes:** minikube's metrics-server only measures every 60 seconds, so the HPA can be slow. The README shows how to make it measure every 15 seconds.

You can also scale by hand:

```sh
kubectl -n url-shortener scale deploy/shortener-api --replicas=4
```

The HPA takes over again on its next check.

### 9.3 The Ingress: one front door

The Ingress sends every request for host `shortener.test` to the `shortener-api` Service. Because the Ingress passes along the original host name, short links come out as `http://shortener.test/s/...`, which work from your browser.

### 9.4 Keeping data safe

- The database stores its files on a **1 GiB PVC** called `shortener-data`.
- If the database pod is deleted, Kubernetes starts a new one and attaches the same disk. In our test, all 35,623 links were still there.
- The database Deployment uses the `Recreate` strategy: the old pod stops fully before the new one starts, so two databases never write to the same disk.

### 9.5 Keeping the password safe

- Ansible makes a random password the first time and stores it in the `shortener-db` Secret.
- The database and the API both read it from that Secret.
- It is not in Git and not in the playbook output.
- Keep the Secret as long as you keep the database disk. A new password would not match the existing database.

### 9.6 Health checks (probes)

| Probe | What it checks | What happens if it fails |
|---|---|---|
| Readiness, `GET /health` every 5 s | Can this pod reach the database? | The pod stops getting traffic until it recovers |
| Liveness, TCP port 8000 every 15 s | Is the program still listening? | Kubernetes restarts the pod |

`/health` runs on its own database connection, separate from normal requests, so it still answers quickly when the app is busy.

### 9.7 Shutting down cleanly

When a pod is being removed (during an update or when scaling down), it waits 5 seconds before stopping (`preStop: sleep 5`). This gives the Ingress time to stop sending it new requests, so nobody gets an error.

### 9.8 Database connections

PostgreSQL allows about 100 connections. Each API pod keeps a **pool** of at most 10 connections, plus 1 for health checks:

```
8 pods x (10 + 1) = 88 connections, safely under 100
```

If all 10 are busy, a request waits up to 10 seconds for one to free up. If none frees up, the API answers 503 instead of overloading the database. You can change the pool size with the `DB_POOL_MAX` setting.

---

## 10. Testing

### 10.1 Playwright tests (does it work correctly?)

Playwright drives a real Chromium browser and also calls the API directly. There are 24 tests:

| File | Tests | What they check |
|---|---|---|
| `api.spec.js` | 15 | Health, creating links, redirects, refusing bad URLs, 404 and 422 codes, API docs, unique codes |
| `ui.spec.js` | 7 | Page loads with no errors, shorten and copy, redirect works, error messages, phone-size layout |
| `docker.spec.js` | 2 | Links survive restarting containers; 503 while the database is down, then recovery |

Run them (needs Node.js 20 or newer):

```sh
cd e2e
npm ci
npx playwright install chromium
npm test                                       # against http://localhost:8000
BASE_URL=http://shortener.test npm test        # against Kubernetes
npm run test:docker                            # also the 2 Docker tests (Compose only)
```

Latest results: **24 of 24 pass on Compose**, and **22 pass with 2 Docker-only skipped on Kubernetes**.

### 10.2 k6 load test (does it cope when busy?)

`scripts/loadtest.js` pretends to be many users at once. 80% of them open short links and 20% create new ones.

| Profile | What it does |
|---|---|
| `ramp` | Slowly grows from 10 to 100 users over about 3 minutes |
| `spike` | Jumps straight to 300 users for a minute |

Run it against Kubernetes:

```sh
docker run --rm --network host \
  -e TARGETS=http://$(minikube ip) -e HOST=shortener.test -e PROFILE=ramp \
  -i grafana/k6 run - < scripts/loadtest.js
```

Watch the HPA in another terminal while it runs:

```sh
kubectl -n url-shortener get hpa -w
```

Latest results on minikube (4 CPUs):

| Test | Requests | Failed | p95 latency |
|---|---|---|---|
| Ramp | about 35,000 | 0 | 0.68 s |
| Spike | about 18,000 | 0 | 3.2 s |
| Ramp with a rolling update | about 31,000 | 0 | 1.04 s |
| Ramp with the database pod deleted | about 39,500 | 2 (during the 5 s restart) | 0.61 s |

---

## 11. Problems we found and how we fixed them

The first load test found real problems. Each one is explained simply here. Full details and numbers are in [STRESS_TEST_RESULTS.md](../STRESS_TEST_RESULTS.md).

| # | Problem in plain words | What we changed | Result |
|---|---|---|---|
| 1 | The API opened a brand new database connection for every request. When busy, PostgreSQL ran out of connections and refused people. | Added a connection pool: each pod reuses up to 10 connections. | Failed requests on the ramp test went from 22% to 0%. Speed went from 42 to about 200 requests per second. |
| 2 | Under heavy load, the health check got stuck in the queue behind normal requests. Kubernetes thought every pod was broken and the front door had nowhere to send traffic. | Health checks now run separately with their own connection. | Failed requests on the spike test went from 70% to 0%. |
| 3 | If the API started before the database was ready, it crashed and had to be restarted. | The API now waits and retries for up to 30 seconds. | No more restarts on a fresh deploy. |
| 4 | During an update, a pod stopped before the front door knew, so a few requests failed. | Pods wait 5 seconds before stopping. | Zero failed requests during a rolling update under load. |
| 5 | The front door sometimes reused a connection the app had just closed, causing rare errors. | The app keeps idle connections open longer (75 s) than the front door (60 s). | No more "connection reset" errors. |
| 6 | The Copy button did not work on `http://shortener.test`, because browsers only allow the modern clipboard on `https://` or `localhost`. | Added an older copy method as a backup. | Copy works everywhere; all browser tests pass. |
| 7 | The HPA reacts slowly to very short spikes. | Not an app bug. The README explains how to make metrics-server measure more often. | Documented. |

---

## 12. Command cheat sheet

### Docker Compose

```sh
docker compose up --build --wait      # start
docker compose ps                     # status
docker compose logs -f app            # follow app logs
docker compose down                   # stop (keep data)
docker compose down -v                # stop and delete data
```

### minikube

```sh
minikube start --cpus 4 --memory 4g   # start the cluster
minikube ip                           # cluster address
minikube image load <image:tag>       # copy an image into the cluster
minikube image ls                     # images inside the cluster
minikube stop                         # pause the cluster (keeps everything)
minikube delete                       # remove the cluster completely
```

### kubectl (add `-n url-shortener` to each)

```sh
kubectl -n url-shortener get pods                        # list pods
kubectl -n url-shortener get deploy,svc,pvc,ingress,hpa  # list everything
kubectl -n url-shortener logs -l app=shortener-api       # API logs
kubectl -n url-shortener describe pod <name>             # details and events
kubectl -n url-shortener top pods                        # CPU and memory
kubectl -n url-shortener get hpa -w                      # watch scaling live
kubectl -n url-shortener rollout status deploy/shortener-api
kubectl -n url-shortener exec deploy/shortener-db -- \
  psql -U shortener -d shortener -c 'select count(*) from links'
```

### Ansible

```sh
ansible-playbook -i localhost, ansible/deploy.yml \
  -e kube_context=minikube -e app_image=url-shortener:project23
```

### Remove the app from the cluster

```sh
kubectl delete namespace url-shortener     # deletes the app AND all saved links
```

---

## 13. When something goes wrong

| What you see | Likely reason | What to do |
|---|---|---|
| Pods show `ErrImagePull` or `ImagePullBackOff` | The image is not inside minikube | Run `minikube image load <image:tag>` |
| HPA shows `cpu: <unknown>` | metrics-server is still starting, or is not enabled | Wait 2 minutes; check `minikube addons list` |
| `http://shortener.test` does not open | No hosts entry, or the Ingress add-on is off | Check `/etc/hosts` has `$(minikube ip) shortener.test`; run `minikube addons enable ingress` |
| `/health` returns 503 | The API cannot reach the database | `kubectl -n url-shortener get pods`; check the db pod logs |
| PVC stuck in `Pending` | No storage class | Enable `storage-provisioner` and `default-storageclass` |
| Database refuses the password after redeploying | The Secret was deleted but the disk was kept | Delete the namespace to start fresh (this deletes links), or restore the old Secret |
| Playwright says it needs Node.js 20 | Your Node.js is too old | Install Node.js 20+ (for example with `nvm install 22`) |
| `ansible-playbook: command not found` | Ansible is not installed | `python3 -m venv ~/.venvs/ansible && ~/.venvs/ansible/bin/pip install ansible-core` |
| Port 8000 already in use (Compose) | Another program uses it | Set `APP_PORT=8080` in `.env` |

---

## 14. What is not done yet

These are listed in [PRD.md](../PRD.md). They are missing features, not bugs.

- **Ansible structure:** no inventory file, no separate roles, no automatic smoke test, no teardown playbook.
- **`X-Served-By` header:** would show which pod answered each request, to demonstrate load balancing.
- **HTTPS (TLS) on the Ingress.**
- **CI:** tests do not yet run automatically on every push.
- **Speed target:** the PRD asks for redirects under 200 ms (p95) during the load test. We get about 650 ms on a 4-CPU laptop that also runs the load generator.
- **Naming:** the PRD uses `shortener`, `short.local`, a `postgres` StatefulSet and an HPA of 2 to 6 at 60%. The code uses `url-shortener`, `shortener.test`, a `db` Deployment and 2 to 8 at 65%. The team still needs to pick one.

---

## 15. Other documents

| Document | Read it for |
|---|---|
| [README.md](../README.md) | Short setup instructions |
| [PRD.md](../PRD.md) | Every requirement, its acceptance check, and its current status |
| [PROJECT_REPORT.md](../PROJECT_REPORT.md) | Architecture and validation report |
| [STRESS_TEST_RESULTS.md](../STRESS_TEST_RESULTS.md) | Full load test numbers, bug evidence, and before and after results |
