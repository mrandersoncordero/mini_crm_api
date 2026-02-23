import pytest
from app.services.client_service import ClientService
from app.schemas.client import ClientCreate, ClientUpdate
from app.utils.enums import ClientType


class TestClientService:
    """Tests para ClientService"""

    @pytest.mark.asyncio
    async def test_create_client_natural(
        self, db_session, mock_email_service, test_user
    ):
        """Test crear cliente persona natural"""
        service = ClientService(db_session, test_user.id)

        client_data = ClientCreate(
            client_type=ClientType.NATURAL,
            contact_name="Juan Perez",
            phone="+584241234567",
            address="Calle 123",
        )

        client = await service.create_client(client_data)

        assert client.id is not None
        assert client.contact_name == "Juan Perez"
        assert client.phone == "+584241234567"
        assert client.client_type == ClientType.NATURAL
        assert client.company_name is None

    @pytest.mark.asyncio
    async def test_create_client_juridical(
        self, db_session, mock_email_service, test_user
    ):
        """Test crear cliente persona jurídica"""
        service = ClientService(db_session, test_user.id)

        client_data = ClientCreate(
            client_type=ClientType.JURIDICAL,
            contact_name="Carlos Lopez",
            company_name="Empresa CA",
            phone="+584251234567",
            address="Avenida Principal",
        )

        client = await service.create_client(client_data)

        assert client.id is not None
        assert client.contact_name == "Carlos Lopez"
        assert client.company_name == "Empresa CA"
        assert client.client_type == ClientType.JURIDICAL

    @pytest.mark.asyncio
    async def test_create_client_juridical_without_company_fails(
        self, db_session, mock_email_service, test_user
    ):
        """Test que cliente jurídico sin nombre de empresa falla"""
        service = ClientService(db_session, test_user.id)

        client_data = ClientCreate(
            client_type=ClientType.JURIDICAL,
            contact_name="Maria Garcia",
            company_name=None,
            phone="+584261234567",
            address="Calle Secundaria",
        )

        with pytest.raises(
            ValueError, match="Company name is required for juridical clients"
        ):
            await service.create_client(client_data)

    @pytest.mark.asyncio
    async def test_create_client_duplicate_phone_fails(
        self, db_session, mock_email_service, test_user, test_client
    ):
        """Test que no se puede crear cliente con teléfono duplicado"""
        service = ClientService(db_session, test_user.id)

        client_data = ClientCreate(
            client_type=ClientType.NATURAL,
            contact_name="Nuevo Cliente",
            phone=test_client.phone,  # Teléfono ya existente
            address="Nueva Direccion",
        )

        with pytest.raises(ValueError, match="already exists"):
            await service.create_client(client_data)

    @pytest.mark.asyncio
    async def test_get_client_by_phone(self, db_session, test_user, test_client):
        """Test obtener cliente por teléfono"""
        service = ClientService(db_session, test_user.id)

        client = await service.get_by_phone("+584121234567")

        assert client is not None
        assert client.id == test_client.id

    @pytest.mark.asyncio
    async def test_get_client_by_phone_not_found(self, db_session, test_user):
        """Test obtener cliente por teléfono que no existe"""
        service = ClientService(db_session, test_user.id)

        client = await service.get_by_phone("+999999999999")

        assert client is None

    @pytest.mark.asyncio
    async def test_search_clients_by_name(self, db_session, test_user, test_client):
        """Test buscar clientes por nombre"""
        service = ClientService(db_session, test_user.id)

        clients = await service.search_by_name("John")

        assert len(clients) > 0
        assert any(c.contact_name == "John Doe" for c in clients)

    @pytest.mark.asyncio
    async def test_search_clients_by_company_name(
        self, db_session, test_user, test_client_juridical
    ):
        """Test buscar clientes por nombre de empresa"""
        service = ClientService(db_session, test_user.id)

        clients = await service.search_by_name("Tech")

        assert len(clients) > 0

    @pytest.mark.asyncio
    async def test_update_client(self, db_session, test_user, test_client):
        """Test actualizar cliente"""
        service = ClientService(db_session, test_user.id)

        update_data = ClientUpdate(
            contact_name="Juan Actualizado",
            address="Nueva Direccion 456",
        )

        updated = await service.update_client(test_client.id, update_data)

        assert updated.contact_name == "Juan Actualizado"
        assert updated.address == "Nueva Direccion 456"

    @pytest.mark.asyncio
    async def test_update_client_phone_unique(self, db_session, test_user, test_client):
        """Test que no se puede cambiar a teléfono duplicado"""
        # Crear segundo cliente
        service = ClientService(db_session, test_user.id)
        client2_data = ClientCreate(
            client_type=ClientType.NATURAL,
            contact_name="Cliente Dos",
            phone="+584299999999",
            address="Direccion 2",
        )
        client2 = await service.create_client(client2_data)

        # Intentar cambiar al teléfono del primer cliente
        update_data = ClientUpdate(phone=test_client.phone)

        with pytest.raises(ValueError, match="already exists"):
            await service.update_client(client2.id, update_data)

    @pytest.mark.asyncio
    async def test_advanced_search_by_phone(self, db_session, test_user, test_client):
        """Test búsqueda avanzada por teléfono"""
        service = ClientService(db_session, test_user.id)

        clients = await service.advanced_search(phone="+584121234567")

        assert len(clients) == 1
        assert clients[0].id == test_client.id

    @pytest.mark.asyncio
    async def test_advanced_search_by_client_type(
        self, db_session, test_user, test_client, test_client_juridical
    ):
        """Test búsqueda avanzada por tipo de cliente"""
        service = ClientService(db_session, test_user.id)

        clients = await service.advanced_search(client_type="juridical")

        assert len(clients) >= 1
        assert all(c.client_type == ClientType.JURIDICAL for c in clients)

    @pytest.mark.asyncio
    async def test_check_client_exists_by_phone(
        self, db_session, test_user, test_client
    ):
        """Test verificar si cliente existe por teléfono"""
        service = ClientService(db_session, test_user.id)

        exists = await service.check_client_exists(phone="+584121234567")

        assert exists is not None
        assert exists.id == test_client.id

    @pytest.mark.asyncio
    async def test_check_client_exists_not_found(self, db_session, test_user):
        """Test verificar si cliente existe - no encontrado"""
        service = ClientService(db_session, test_user.id)

        exists = await service.check_client_exists(phone="+999999999999")

        assert exists is None

    @pytest.mark.asyncio
    async def test_delete_client(self, db_session, test_user, test_client):
        """Test eliminar cliente"""
        service = ClientService(db_session, test_user.id)

        await service.delete(test_client.id)

        deleted = await service.get_by_id(test_client.id)
        assert deleted is None
