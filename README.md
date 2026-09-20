# CampusGPT

## 1. Environment variables

Create the root `.env` file:

```bash
curl -fsSL https://raw.githubusercontent.com/deeks528/scripts/main/gen_env.sh | bash -s -- .env.example .env
```

Create the Remote File Manager `.env` file:

```bash
curl -fsSL https://raw.githubusercontent.com/deeks528/scripts/main/gen_env.sh | bash -s -- FS/remote-file-manager/.env.example FS/remote-file-manager/.env
```

This should create:

```text
CampusGPT/
├── .env
└── FS/
    └── remote-file-manager/
        └── .env
```

---

## 2. Python environment

Create the virtual environment:

```bash
python -m venv campusgpt
```

### Linux / macOS

Activate it:

```bash
source campusgpt/bin/activate
```

### Windows PowerShell

Activate it:

```powershell
.\campusgpt\Scripts\Activate.ps1
```

Install Python dependencies:

```bash
pip install -r requirements.txt
```

---

## 3. Database setup

Make sure PostgreSQL is running and the database configured in `.env` exists.

Run the database migrations:

```bash
cd modules/database
alembic upgrade head
```

Check the current migration:

```bash
alembic current
```

---

## 4. Start the servers

CampusGPT uses three components:

* File System backend
* Remote File Manager frontend
* CampusGPT DB/processing API

Start each component in a separate terminal.

### 4.1 File System backend

From the project root:

```bash
mkdir storage
cd FS/backend
python run.py -root "$PWD/../../storage"
```

### 4.2 Remote File Manager

In another terminal:

```bash
cd FS/remote-file-manager
npm install
npm run dev
```

### 4.3 CampusGPT DB API

In another terminal:

```bash
cd modules
uvicorn api.main:app --reload --host 127.0.0.1 --port 8000
```

---

## 5. Database migrations

The migration files are located at:

```text
modules/database/migrations/versions/
```

Whenever the SQLAlchemy database models are changed, create a new migration.

First:

```bash
cd modules/database
```

Generate the migration:

```bash
alembic revision --autogenerate -m "describe the change"
```

Review the generated migration carefully.

Then apply it:

```bash
alembic upgrade head
```

Check the current database revision:

```bash
alembic current
```

View migration history:

```bash
alembic history
```

> Never manually modify an already-applied migration. Create a new migration instead.

---

## 6. Useful migration commands

Rollback one migration:

```bash
alembic downgrade -1
```

Create a migration manually:

```bash
alembic revision -m "describe the change"
```

Upgrade to the latest migration:

```bash
alembic upgrade head
```

---

## 7. Quick setup

For a fresh clone:

```bash
cd CampusGPT

python -m venv campusgpt

# Linux/macOS
source campusgpt/bin/activate

# Windows PowerShell
# .\campusgpt\Scripts\Activate.ps1

pip install -r requirements.txt

curl -fsSL https://raw.githubusercontent.com/deeks528/scripts/main/gen_env.sh | bash -s -- .env.example .env

curl -fsSL https://raw.githubusercontent.com/deeks528/scripts/main/gen_env.sh | bash -s -- FS/remote-file-manager/.env.example FS/remote-file-manager/.env

mkdir storage
cd modules/database
alembic upgrade head
```

Then start the three services in separate terminals as described above.
