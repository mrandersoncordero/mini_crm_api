# Mini CRM - API

Sistema de gestión de leads y clientes con API REST construida con FastAPI.

## Características

- **Autenticación JWT**: Login seguro con tokens JWT
- **Roles de usuario**: Admin, Ventas y Administración
- **Gestión de Clientes**: Registro con validación de teléfono (único)
- **Gestión de Leads**: Tracking de prospectos desde múltiples canales
- **Audit Log**: Registro automático de todas las operaciones CRUD
- **Validación de datos**: Validación de teléfonos con formato internacional

## Tecnologías

- **FastAPI**: Framework web moderno y rápido
- **SQLAlchemy 2.0**: ORM con soporte async
- **PostgreSQL**: Base de datos relacional
- **Alembic**: Migraciones de base de datos
- **Pydantic**: Validación de datos
- **JWT**: Autenticación basada en tokens
- **Phonenumbers**: Validación de números telefónicos

## Estructura del Proyecto

```
mini_crm_diseinca/
├── app/
│   ├── core/              # Configuración y seguridad
│   ├── db/                # Base de datos y sesiones
│   ├── models/            # Modelos SQLAlchemy
│   ├── schemas/           # Schemas Pydantic
│   ├── repositories/      # Repositorios base
│   ├── services/          # Lógica de negocio
│   ├── routers/           # Endpoints API
│   └── utils/             # Utilidades y enums
├── alembic/               # Migraciones
├── scripts/               # Scripts utilitarios
├── main.py                # Punto de entrada
└── docker-compose.dev.yml # Configuración Docker
```

## Instalación

### 1. Clonar y configurar

```bash
# Clonar el repositorio
git clone <repo-url>
cd mini_crm_diseinca

# Instalar dependencias
uv sync

# Configurar variables de entorno
# El archivo .env ya está configurado con valores por defecto
```

### 2. Iniciar base de datos

```bash
# Iniciar PostgreSQL con Docker
docker compose -f docker-compose.dev.yml up -d postgres
```

### 3. Crear migraciones y seed

```bash
# Para crear migraciones (si hay cambios en modelos)
alembic revision --autogenerate -m "Descripción de cambios"

# Aplicar migraciones
alembic upgrade head

# Crear usuario admin por defecto
python scripts/create_admin.py
```

Credenciales admin por defecto:
- Username: `admin`
- Password: `admin123`

### 4. Ejecutar la API

```bash
# Opción 1: Directamente con Python
python main.py

# Opción 2: Con uvicorn
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Opción 3: Con Docker
docker compose -f docker-compose.dev.yml up -d
```

La API estará disponible en: http://localhost:8000

Documentación interactiva: http://localhost:8000/docs

## Endpoints API

### Autenticación

```
POST   /auth/login              # Login de usuario
GET    /auth/me                 # Perfil del usuario actual
```

### Usuarios (Admin only)

```
GET    /users                   # Listar usuarios
POST   /users                   # Crear usuario
GET    /users/{id}              # Ver usuario
PATCH  /users/{id}              # Actualizar usuario (parcial)
DELETE /users/{id}              # Eliminar usuario
```

### Clientes

```
GET    /clients                 # Listar clientes
POST   /clients                 # Crear cliente
GET    /clients/search          # Buscar por nombre
GET    /clients/by-phone/{phone}# Buscar por teléfono
GET    /clients/{id}            # Ver cliente (con leads)
PATCH  /clients/{id}            # Actualizar cliente (parcial)
DELETE /clients/{id}            # Eliminar cliente
```

### Leads

```
GET    /leads                   # Listar leads (con filtros)
POST   /leads                   # Crear lead
GET    /leads/stats             # Estadísticas
GET    /leads/{id}              # Ver lead detalle
PATCH  /leads/{id}              # Actualizar lead (parcial)
PATCH  /leads/{id}/status       # Cambiar estado
PATCH  /leads/{id}/assign       # Asignar a usuario
DELETE /leads/{id}              # Eliminar lead
```

## Tipos de Datos

### Tipos de Cliente
- `natural`: Persona natural
- `juridical`: Persona jurídica/empresa

### Canales
- `web`: Formulario web
- `whatsapp`: WhatsApp
- `instagram`: Instagram
- `manual`: Registro manual

### Estados de Lead
- `new`: Nuevo
- `contacted`: Contactado
- `quoted`: Cotizado
- `closed`: Cerrado
- `discarded`: Descartado

### Roles de Usuario
- `admin`: Administrador (acceso total)
- `sales`: Ventas (gestión de leads)
- `management`: Administración (gestión de leads)

## Ejemplos de Uso

### Login

```bash
curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin123"
```

Respuesta:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

### Crear Cliente

```bash
curl -X POST "http://localhost:8000/clients" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{
    "client_type": "natural",
    "contact_name": "Juan Pérez",
    "phone": "+584123456789",
    "email": "juan@example.com",
    "address": "Calle Principal 123"
  }'
```

### Crear Lead

```bash
curl -X POST "http://localhost:8000/leads" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{
    "client_id": 1,
    "channel": "web",
    "status": "new",
    "admin_notes": "Cliente interesado en servicios",
    "sales_notes": "Llamar el lunes"
  }'
```

## Audit Log

Todas las operaciones de creación, actualización y eliminación se registran automáticamente en la tabla `audit_logs` con:
- Tabla afectada
- ID del registro
- Tipo de acción (create/update/delete)
- Valores anteriores y nuevos (JSON)
- Usuario que realizó la acción
- Fecha y hora

## Desarrollo

### Crear una migración

```bash
# Después de modificar modelos
alembic revision --autogenerate -m "Descripción de cambios"

# Aplicar migración
alembic upgrade head

# Revertir última migración
alembic downgrade -1
```

### Comandos útiles

```bash
# Ver logs de PostgreSQL
docker logs -f postgres

# Acceder a PostgreSQL
docker exec -it postgres psql -U postgres -d mini_crm_diseinca

# Reiniciar contenedores
docker compose -f docker-compose.dev.yml restart
```

## Notas

- Los teléfonos se validan y formatean automáticamente al formato E.164 (ej: +584123456789)
- El teléfono es único por cliente
- Los usuarios de Ventas solo pueden ver leads asignados a ellos (por implementar)
- Todos los timestamps se almacenan en UTC

## Próximas Mejoras

- [ ] Filtros avanzados en listados
- [ ] Exportación a Excel
- [ ] Notificaciones por email
- [ ] Integración con WhatsApp Business API
- [ ] Dashboard con estadísticas
- [ ] Búsqueda full-text
