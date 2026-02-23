import pytest
import asyncio
from typing import AsyncGenerator, Generator
from unittest.mock import AsyncMock, patch
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import StaticPool
from httpx import AsyncClient, ASGITransport

from main import app
from app.db.deps import get_db
from app.utils.base_model import Base

from app.models import User, Client, Lead
from app.utils.enums import UserRole, ClientType, Channel, LeadStatus

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
    class_=AsyncSession,
)


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with TestingSessionLocal() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as c:
        yield c

    app.dependency_overrides.clear()


# --- Mock de Email Service ---
@pytest.fixture
def mock_email_service():
    """Mock del servicio de email para tests - solo prints en terminal"""
    with patch("app.services.client_service.email_service") as mock:
        mock.notify_new_client = AsyncMock(return_value=True)
        mock.notify_new_lead = AsyncMock(return_value=True)
        mock.notify_lead_status_change = AsyncMock(return_value=True)
        mock.send_admin_notification = AsyncMock(return_value=True)
        yield mock


# --- Fixtures de Datos ---


@pytest.fixture
async def test_user(db_session: AsyncSession) -> User:
    """Crea un usuario de prueba"""
    from app.core.security import get_password_hash

    user = User(
        username="testuser",
        email="test@example.com",
        hashed_password=get_password_hash("testpass123"),
        role=UserRole.ADMIN,
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def test_user_sales(db_session: AsyncSession) -> User:
    """Crea un usuario de ventas de prueba"""
    from app.core.security import get_password_hash

    user = User(
        username="salesuser",
        email="sales@example.com",
        hashed_password=get_password_hash("testpass123"),
        role=UserRole.SALES,
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def test_client(db_session: AsyncSession) -> Client:
    """Crea un cliente de prueba"""
    client = Client(
        client_type=ClientType.NATURAL,
        contact_name="John Doe",
        phone="+584121234567",
        address="123 Main St",
    )
    db_session.add(client)
    await db_session.commit()
    await db_session.refresh(client)
    return client


@pytest.fixture
async def test_client_juridical(db_session: AsyncSession) -> Client:
    """Crea un cliente jurídico de prueba"""
    client = Client(
        client_type=ClientType.JURIDICAL,
        contact_name="Jane Smith",
        company_name="Tech Corp",
        phone="+584141234567",
        address="456 Business Ave",
    )
    db_session.add(client)
    await db_session.commit()
    await db_session.refresh(client)
    return client


@pytest.fixture
async def test_lead(
    db_session: AsyncSession, test_client: Client, test_user: User
) -> Lead:
    """Crea un lead de prueba"""
    lead = Lead(
        client_id=test_client.id,
        channel=Channel.WEB,
        status=LeadStatus.NEW,
        created_by_id=test_user.id,
    )
    db_session.add(lead)
    await db_session.commit()
    await db_session.refresh(lead)
    return lead
