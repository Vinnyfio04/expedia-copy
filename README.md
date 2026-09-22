# expedia-copy

`expedia-copy` is a learning project that recreates the core experience of a travel-booking site. The initial goal is to provide a Vue user interface backed by a FastAPI API, then grow the project in small, testable increments.

## Project structure

```text
.
|-- controller/       FastAPI application and tests
|   |-- app/
|   |   `-- main.py
|   `-- requirements.txt
|-- model/            CSV application data and relationship assets
|-- view/             Vue application powered by Vite
|   |-- src/
|   |-- index.html
|   |-- package.json
|   `-- vite.config.js
|-- docs/             Project documentation
|-- prompts/          Selected project prompts
|-- handoffs/         Current project handoff
`-- AGENTS.md          Project rules for coding agents
```

## Prerequisites

- Python 3.11 or newer
- Node.js 20 or newer
- npm 10 or newer

## Controller setup

Dependencies are not installed as part of this scaffold. When you are ready to install them:

```powershell
cd controller
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`. Its interactive documentation will be at `http://localhost:8000/docs`.

## View setup

In a separate terminal, when you are ready to install dependencies:

```powershell
cd view
npm install
npm run dev
```

Vite will print the local frontend URL, typically `http://localhost:5173`.

## View checks

From the `view` directory, run:

```powershell
npm run lint
npm test
npm run build
```

## Project context

- [Design and request pipeline](docs/design-pipeline.md)
- [Selected project prompts](prompts/)
- Project handoffs belong in `handoffs/` when that directory is created.
