# Sharing & Running the SIH-DNK Mockup

This repo is a small full-stack mockup: a Postgres database, a Redis cache, five
services (one real validation engine plus four placeholder APIs), and a
frontend, all wired together with Docker Compose. The whole thing runs on your
own machine with Docker. This guide has two audiences, so pick your section:

- If you're the **owner** (the person who made the repo), start at [Section A](#a-how-the-owner-gives-access).
- If you're a **friend** who just got invited, start at [Section B](#b-clone-the-repo).

Everything here assumes a GitHub account and basic comfort with a terminal.

---

## A. How the owner gives access

The repo is **private**, so the owner has to explicitly invite people. There are
two permission levels:

- **Read** (`--permission read`): the friend can view and clone the repo, but
  cannot push changes. Use this for "come look at it" invites.
- **Write** (`--permission write`): the friend can also push commits and open
  pull requests. Use this for teammates who will actually contribute.

### Via the command line (fastest)

If you have the [GitHub CLI](https://cli.github.com/) (`gh`) installed and
logged in:

```bash
gh repo edit BlackPool25/sih-dnk-mockup --add-collaborator <friend-username> --permission read
```

Swap `read` for `write` if they're going to contribute. You can repeat this for
as many friends as you like.

### Via the GitHub website

No CLI needed. On the repo page:

1. Go to **Settings** (top-right tab, only visible to you).
2. In the left sidebar pick **Collaborators and teams**.
3. Click **Add people**, type their GitHub username, pick a role
   (**Read** or **Write**), and confirm.

### What about making the repo public?

You *could* flip the repo to public and skip all this. Don't. This project
contains business logic and internal research you probably don't want the whole
world browsing, and public is permanent-ish to unwind. Inviting collaborators is
free and keeps the repo private.

---

## B. Clone the repo

Once you've been invited, open a terminal and pick one method.

### Option 1: SSH (recommended if you've set up a key)

```bash
git clone git@github.com:BlackPool25/sih-dnk-mockup.git
```

This needs an **SSH key added to your GitHub account**. If you haven't done
that before, GitHub's docs cover it ("Adding a new SSH key to your GitHub
account"). You'll also know it works because you'll never be asked for a
password.

### Option 2: HTTPS (simplest)

```bash
git clone https://github.com/BlackPool25/sih-dnk-mockup.git
```

With HTTPS you just need to be **logged into GitHub in your browser**. When
git asks for a password, that's where it can fall over: GitHub doesn't accept
your normal password for git anymore, only a token. The easy way around it is
to use a tool like [GitHub Desktop](https://desktop.github.com/) or
[`gh auth login`](https://cli.github.com/) once, which caches your login so
`git pull` and `git push` just work afterwards.

Either way you end up in a folder called `sih-dnk-mockup`:

```bash
cd sih-dnk-mockup
```

---

## C. Run the full stack

### Step 0: Prerequisites

You need Docker with the Compose v2 plugin. This is the only real install.

- **Windows or macOS:** install [Docker Desktop](https://www.docker.com/products/docker-desktop/). It bundles everything, including `docker compose`.
- **Linux:** install Docker Engine and the `docker compose` plugin (your distro's package manager or Docker's official instructions).

Check both from a terminal:

```bash
docker --version
docker compose version
```

If the second command prints something like `Docker Compose version v2.x.x`,
you're good. If it says "docker: 'compose' is not a docker command", you have
old standalone `docker-compose` or nothing at all, and need the v2 plugin.

### Step 1: Create your `.env` file (do not skip this)

```bash
cp .env.example .env
```

This is the most important step, so here's the deal. The database password
lives in `.env`, and `.env` is **gitignored**: it exists on your machine only
and is never committed to the repo. That's deliberate. Everyone who clones the
repo gets a fresh copy of the template and invents their own values.

Open `.env` in a text editor. It looks like this (fill in your own values):

```bash
DB_PASSWORD=changeme
DB_PORT=5433
POSTGRES_DB=sih_dnk
POSTGRES_USER=sih_dnk
DATABASE_URL=postgresql+psycopg://sih_dnk:changeme@localhost:5433/sih_dnk
```

What to put in each field:

- `DB_PASSWORD`: any string, the stronger the better. Make it your own so it's
  not the same as everyone else's.
- `DB_PORT`: `5433` (keep it. Port 5432 is used by other local software, so the
  project deliberately picked 5433).
- `POSTGRES_DB`: `sih_dnk` (keep it).
- `POSTGRES_USER`: `sih_dnk` (keep it).
- `DATABASE_URL`: the connection string for tools that run on your machine
  (migrations, seeding). Notice it embeds the password after `sih_dnk:`. If you
  changed `DB_PASSWORD`, **paste the same password in there too**, replacing
  `changeme`. Forgetting this is the classic "everything started but seeding
  fails with authentication" gotcha.

### Step 2: Build and start everything

```bash
docker compose up -d --build
```

This builds the images and starts all seven pieces: Postgres, Redis, the
validation engine, the three placeholder APIs, and the frontend. The first run
takes a few minutes because Docker downloads base images and installs
dependencies. Later runs are much faster.

Then check that everything came up healthy:

```bash
docker compose ps
```

You want to see all seven services with `Up` and `healthy` in the status
column. Give it a few seconds if some are still starting.

### Step 3: Prove the stack is alive

Open <http://127.0.0.1:8005> in your browser. That's the frontend placeholder
(an nginx page saying the stack is up). If it loads, all seven containers are
running and talking to each other.

### Step 4 (optional but useful): Seed the database

Fresh clones start with an **empty database**. The seeded configuration data
(lanes, product categories, duty rates, tax tables) lives in a Docker volume
called `sih_dnk_pgdata`, which is created locally on the machine that ran the
stack. It is *not* stored in the repo, and there's no reason it should be: the
seed code is, so anyone can rebuild the data.

To seed, first install `uv` if you don't have it (the project uses it for
Python tooling):

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Then, from the `validation-engine` directory, run the documented sequence from
`validation-engine/README.md`:

```bash
cd validation-engine

# load the DB settings you put in .env into this terminal
set -a && . ../.env && set +a

uv run alembic upgrade head                 # apply the schema (safe to re-run)
uv run python -m app.services.convert --all # seed every config table (idempotent)
uv run python -m app.services.verify        # optional: run the sanity checks
```

Notes:

- The stack must be up first, because seeding writes to the Postgres container.
- `convert --all` is safe to re-run. It clears and refills each table in its own
  transaction, so you can't end up with duplicates.
- The seed logic lives in `validation-engine/app/services/seed/` (the CLI is
  just a thin wrapper). If you're curious about what gets seeded, that's where
  to look.

---

## D. Port map (quick reference)

Every service binds to `127.0.0.1` only, which means they're reachable just
from your own machine, never from the internet. Handy table:

| Service | URL |
|---|---|
| validation-engine | http://127.0.0.1:8001 |
| voice-pipeline | http://127.0.0.1:8002 |
| pricing-engine | http://127.0.0.1:8003 |
| tracking-api | http://127.0.0.1:8004 |
| frontend | http://127.0.0.1:8005 |
| postgres | 127.0.0.1:5433 |
| redis | 127.0.0.1:6379 |

The validation engine is the real service; voice-pipeline, pricing-engine, and
tracking-api are placeholders that answer a health check and will be fleshed
out later.

---

## E. Stop, and update

### Stop the stack (keep your data)

```bash
docker compose down
```

Stops the containers. Your database volume (`sih_dnk_pgdata`) survives, so next
time you `up` again, your data is still there.

### Stop and wipe (be very careful with this one)

```bash
docker compose down -v
```

The `-v` flag **deletes the database volume along with all its data**. The
empty-seed rule no longer applies: after this, your DB is gone and you have to
re-run the seeding steps from Section C. Use it only when you truly want a
fresh slate.

### Pull new changes from teammates

```bash
git pull
docker compose up -d --build
```

`git pull` fetches new commits (requires a collaborator permission of **read**
or **write**, which you have if you're reading this). The compose command then
rebuilds anything that changed and starts it up. Because `.env` is gitignored,
your local database password is untouched by pulls, so you never need to
recreate it.
