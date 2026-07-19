AGENTS.md
Project

Mubify is a backend portfolio project for backend engineering job applications.

The backend code is located at the repository root.

Main stack:

FastAPI
PostgreSQL
SQLAlchemy 2.0
Alembic
JWT
pytest
ChromaDB

This repository is a backend-only version extracted from a team project. The repository owner was responsible for the backend implementation and does not claim responsibility for the frontend implementation.

Git Workflow
Work in the current main branch working tree.
Do not create or switch branches.
Do not stage, commit, or push changes.
Inspect git status before editing.
Do not overwrite or revert existing user changes.
If unrelated uncommitted changes exist, report them before editing.
Complete only the requested task.
Stop after validation and wait for user review.
Scope
Modify only files required by the current task.
Do not perform unrelated cleanup or broad refactoring.
Do not add frontend code.
Do not claim responsibility for frontend work from the original team project.
Preserve existing API behavior unless explicitly requested.
Do not change recommendation weights or ranking logic unless explicitly requested.
Do not add unnecessary dependencies.
Backend Rules
Run Python, Alembic, pytest, Ruff, and Docker commands from the repository root.
PostgreSQL is the production database.
SQLite may be used for fast unit tests.
Database schema changes require an Alembic migration.
Add or update tests when behavior changes.
Do not delete, skip, or weaken valid tests to make them pass.
Run the narrowest relevant tests first, followed by the relevant full suite.
Do not commit secrets, datasets, local databases, or generated Chroma data.
Documentation Accuracy

Verify documentation claims against the code.

Do not claim:

a trained machine-learning recommendation model
benchmark or accuracy improvements without reproducible results
production readiness
deployment, CI, or Docker support before they exist
responsibility for frontend development

Describe the recommendation system as:

ChromaDB semantic candidate retrieval
PostgreSQL as the track source of truth
heuristic audio-feature and popularity reranking
Completion Report

After editing, report:

Files changed.
What changed.
Behavior changes, if any.
Commands run and results.
Anything not verified.
Suggested commit message.

Do not commit or push.
