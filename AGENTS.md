# AGENTS.md — SaaS CRM

## Commands

### Package manager
This project uses **uv** for dependency management.

```bash
uv add <package>           # Add a dependency
uv sync                    # Install/lock dependencies
```

### Docker (primary dev environment)
```bash
docker compose up -d       # Start backend + postgres
docker compose down        # Stop all services
docker compose logs -f     # Follow logs
```

### Running inside the container
```bash
docker exec -it sass_crm_backend bash
```

### Alembic migrations
The project uses two `.ini` files to isolate migration branches (see README.md for why):

```bash
# Public schema (users, tenants, audit_logs, etc.)
alembic -c alembic_public.ini revision --autogenerate -m "description"
alembic -c alembic_public.ini upgrade head
alembic -c alembic_public.ini current

# Tenant schemas (core_crm models)
alembic -c alembic_tenant.ini revision --autogenerate -m "description"
# Tenant migrations are applied automatically by TenantService in production
```

### Tests
No test framework is currently configured. Add pytest when needed:
```bash
uv add --dev pytest pytest-asyncio httpx
```

### Linting / formatting
**ruff** is the configured linter/formatter (via pyproject.toml defaults).
```bash
ruff check .              # Lint
ruff format .             # Format
```

## Code Style

### Imports
- Standard library first, then third-party, then app-local — each group separated by a blank line
- Use absolute imports: `from app.core.base_model import Base`
- Use `TYPE_CHECKING` blocks for model forward references to avoid circular imports

### Types
- Use `Mapped[T]` and `mapped_column()` for SQLAlchemy column definitions
- Use `uuid.UUID` for all primary/foreign keys (not str)
- Use type hints on all function signatures; prefer `str | None` over `Optional[str]` (Python 3.13+)
- Return types are required on all functions

### Naming conventions
- **Files/directories**: `snake_case` (e.g., `base_repository.py`, `core_crm/`)
- **Classes**: `PascalCase` (e.g., `BaseRepository`, `TenantBase`)
- **Functions/methods**: `snake_case` (e.g., `get_by_id`, `apply_tenant_filter`)
- **Constants**: `UPPER_SNAKE_CASE` (e.g., `DB_URL`, `SECRET_KEY`)
- **SQLAlchemy tables**: `snake_case` plural (e.g., `__tablename__ = "contacts"`)
- **Alembic migration files**: `<rev_id>_<description>.py`

### Models
- Public models inherit from `Base` (in `app.core.base_model`)
- Tenant models inherit from `TenantBase`
- Use `TimestampMixin` for `created_at`/`updated_at` columns
- All models use `Mapped` type annotations with `mapped_column()`

### Error handling
- Use custom exceptions from `app.core.exceptions`: `NotFoundException`, `BadRequestException`, `ConflictException`, `UnauthorizedException`, `ForbiddenException`
- All exceptions return structured `detail` dicts with `status` and `message` keys
- Repositories use try/except with `db.rollback()` on failure
- Never commit inside repository methods that are called within a larger transaction — use `flush()` instead

### Async patterns
- All DB operations are async: `await self.db.execute(query)`
- Use `db.flush()` to generate IDs without committing
- Use `db.refresh(obj)` after flush to load server-generated values
- The audit log is staged via `db.add()` within the same transaction — no separate commit

### Architecture
- **Modules** live in `app/modules/<feature>/` with submodules for models, router, schemas, service
- **Router**: each module has a `router.py` that exports an `APIRouter`
- **Repository**: `BaseRepository` in `app.core.base_repository` provides generic CRUD with tenant isolation and audit logging
- **Config**: `app.core.config.Settings` via pydantic-settings, singleton `settings`
- **Multi-tenant**: middleware sets `search_path` per request; repositories never call `SET search_path` directly
