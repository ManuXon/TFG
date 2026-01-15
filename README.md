# MapAI-UB (TFG) — Visual Analytics + Gated Chatbot

Web-based visual analytics platform to explore survey data about AI tool usage in teaching at the University of Barcelona (UB).  
The system combines interactive dashboards (quantitative aggregates + coordinated filtering) with qualitative open-text exploration (sentiment/topic groupings) and a gated chatbot for computation-grounded Q&A.

> **Note:** The `dev` branch contains the latest changes.

---

## Run the platform (production compose)

In the repository root, rename `example.backend.env` to `backend.env` and fill in:
- an OpenAI API key (required for the chatbot’s LLM requests)
- a random Redis security key

From the repository root:

```bash
docker-compose -f docker-compose.prod.yml up
```

## User Management

To access the gated chatbot you must create/manage users in the backend using the built-in text UI.

Run this inside the running backend container:
```bash
python -m src.scripts.users_tui
```

## React (IDE review) — avoid TypeScript errors

If you open the files under `TFG/services/frontend/react-components` without installing the React dependencies, your IDE may show TypeScript errors (unresolved modules/types).

The Docker build already installs these dependencies during the image build — the following step is only needed to review the React files locally without seeing typescript errors in an IDE.

From the repository root:

```bash
cd ./services/frontend/react-components
npm install
```
