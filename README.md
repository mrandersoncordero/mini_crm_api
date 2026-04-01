# SaaS CRM

## Migraciones de base de datos

El proyecto usa Alembic con dos ramas independientes de migraciones:

- **`public`** — tablas del schema público: `users`, `tenants`, `profiles`, `audit_logs`, etc.
- **`tenant`** — tablas de cada schema tenant: modelos de `core_crm` (contacts, sales, business, system).

### Por qué hay dos archivos `.ini`

Alembic exige que **todas** las ramas conocidas estén aplicadas en la DB antes de permitir `revision --autogenerate`. El problema es que la rama `tenant` nunca tiene registro en `public.alembic_version` — cada schema tenant tiene su propia tabla `alembic_version` interna, y en producción los schemas se crean dinámicamente via `TenantService`.

Con un solo `alembic.ini` que declara ambas ramas en `version_locations`, Alembic siempre bloquea el autogenerate con "Target database is not up to date".

La solución es usar un `.ini` por rama al generar migraciones, de modo que `ScriptDirectory` solo conozca los heads de la rama activa:

| Archivo | `version_locations` | Uso |
|---|---|---|
| `alembic_public.ini` | `alembic/versions/public` | Crear y aplicar migraciones de public |
| `alembic_tenant.ini` | `alembic/versions/tenant` | Crear migraciones de tenant |
| `alembic.ini` | ambas carpetas | Usado por `run_migrations.py` al iniciar el contenedor |

### Comandos

Todos los comandos se ejecutan **dentro del contenedor**:

```bash
docker exec -it sass_crm_backend bash
```

#### Crear una migración nueva

```bash
# Schema public (usuarios, tenants, audit_logs, etc.)
alembic -c alembic_public.ini revision --autogenerate -m "descripcion"

# Schema tenant (modelos de core_crm)
# Requiere que exista al menos un tenant en la DB para usar como referencia
alembic -c alembic_tenant.ini revision --autogenerate -m "descripcion"
```

#### Aplicar migraciones

```bash
# Aplicar migraciones de public
alembic -c alembic_public.ini upgrade head

# Ver estado actual de public
alembic -c alembic_public.ini current

# Ver historial de public
alembic -c alembic_public.ini history
```

> Las migraciones de tenant **no se aplican manualmente** en producción.
> `TenantService` las aplica automáticamente al crear un nuevo tenant.
> Al iniciar el contenedor, `run_migrations.py` también las re-aplica sobre los schemas tenant existentes.

#### Revertir migraciones

```bash
# Revertir una migración de public
alembic -c alembic_public.ini downgrade -1
```

### Estructura de archivos

```
alembic/
├── env.py                          # Configuración compartida, detecta la rama activa
├── versions/
│   ├── public/                     # Migraciones del schema public
│   │   └── a6ed75519c87_0001_initial_schema_public.py
│   └── tenant/                     # Migraciones de schemas tenant
│       └── f5d7670ea416_0001_initial_schema_tenant.py
alembic.ini                         # Usado por run_migrations.py (ambas ramas)
alembic_public.ini                  # Usado en desarrollo para migraciones de public
alembic_tenant.ini                  # Usado en desarrollo para migraciones de tenant
```

### Agregar un modelo nuevo

1. Crear el modelo heredando de `Base` (public) o `TenantBase` (tenant).
2. Importar el módulo en `alembic/env.py` en el bloque correspondiente.
3. Generar la migración con el `.ini` correcto.
4. Aplicarla con `upgrade head`.
