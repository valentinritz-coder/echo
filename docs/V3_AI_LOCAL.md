# V3.A AI local-only (DB + API plumbing)

This phase adds DB and API plumbing for AI processing metadata/runs.
No worker and no ML inference are included.

## Sandbox data directory

Use `./data_sandbox` mounted to `/app/data` via compose override:

```bash
mkdir -p data_sandbox/audio
cp -n .env.example .env || true
docker compose -f docker-compose.yml -f docker-compose.sandbox.yml up --build -d
```

## Apply migrations (Alembic only)

```bash
docker compose -f docker-compose.yml -f docker-compose.sandbox.yml exec api alembic upgrade head
```

Optional checks:

```bash
docker compose -f docker-compose.yml -f docker-compose.sandbox.yml exec api alembic current
docker compose -f docker-compose.yml -f docker-compose.sandbox.yml logs -f api
```

## V3.A endpoint curl tests

### 1) Create an entry

Place an audio file in `./data_sandbox/audio/` first (example: `./data_sandbox/audio/sample.mp3`).

```bash
QID=$(curl -s http://localhost:8000/questions/today | python -c "import sys,json; print(json.load(sys.stdin)['id'])")
ENTRY_JSON=$(curl -s -X POST http://localhost:8000/entries \
  -F "user_id=sandbox-user" \
  -F "question_id=${QID}" \
  -F "audio_file=@./data_sandbox/audio/sample.mp3;type=audio/mpeg")
ENTRY_ID=$(echo "$ENTRY_JSON" | python -c "import sys,json; print(json.load(sys.stdin)['id'])")
```

### 2) Queue/process AI (DB-only)

```bash
curl -i -X POST "http://localhost:8000/entries/${ENTRY_ID}/ai/process" \
  -H "Content-Type: application/json" \
  -d '{"tasks":["transcribe","summarize"],"force":false,"pipeline_version":"v3.a"}'
```

### 3) Read entry AI status

```bash
curl -s "http://localhost:8000/entries/${ENTRY_ID}/ai"
```

### 4) Read AI run by id

```bash
RUN_ID=$(curl -s "http://localhost:8000/entries/${ENTRY_ID}/ai" | python -c "import sys,json; print(json.load(sys.stdin)['ai_last_run_id'])")
curl -s "http://localhost:8000/ai/runs/${RUN_ID}"
```

## V2.5 non-regression checklist

- `GET /health` returns `{ "status": "ok" }`
- Upload audio via `POST /entries` still works (same MIME validation)
- List entries via `GET /entries?user_id=...` still works
- Read audio via `GET /entries/{id}/audio` still works
- Delete via `DELETE /entries/{id}` removes DB row + audio file
- Persistence across restart with sandbox mount:
  - stop: `docker compose -f docker-compose.yml -f docker-compose.sandbox.yml down`
  - start again and verify previous entry still exists

## Stop sandbox stack

```bash
docker compose -f docker-compose.yml -f docker-compose.sandbox.yml down
```
