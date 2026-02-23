import pytest
from app.services.user_service import UserService
from app.schemas.user import UserCreate, UserUpdate
from app.utils.enums import UserRole


class TestUserService:
    """Tests para UserService"""

    @pytest.mark.asyncio
    async def test_create_user(self, db_session):
        """Test crear usuario"""
        service = UserService(db_session)

        user_data = UserCreate(
            username="newuser",
            email="newuser@example.com",
            password="password123",
            role=UserRole.SALES,
        )

        user = await service.create_user(user_data)

        assert user.id is not None
        assert user.username == "newuser"
        assert user.email == "newuser@example.com"
        assert user.role == UserRole.SALES
        assert user.hashed_password is not None

    @pytest.mark.asyncio
    async def test_create_user_duplicate_username(self, db_session, test_user):
        """Test que no se puede crear usuario con username duplicado"""
        service = UserService(db_session)

        user_data = UserCreate(
            username=test_user.username,  # Username ya existente
            email="other@example.com",
            password="password123",
            role=UserRole.SALES,
        )

        with pytest.raises(ValueError, match="already exists"):
            await service.create_user(user_data)

    @pytest.mark.asyncio
    async def test_create_user_duplicate_email(self, db_session, test_user):
        """Test que no se puede crear usuario con email duplicado"""
        service = UserService(db_session)

        user_data = UserCreate(
            username="newuser",
            email=test_user.email,  # Email ya existente
            password="password123",
            role=UserRole.SALES,
        )

        with pytest.raises(ValueError, match="already exists"):
            await service.create_user(user_data)

    @pytest.mark.asyncio
    async def test_authenticate_success(self, db_session, test_user):
        """Test autenticación exitosa"""
        service = UserService(db_session)

        user = await service.authenticate("testuser", "testpass123")

        assert user is not None
        assert user.username == "testuser"

    @pytest.mark.asyncio
    async def test_authenticate_wrong_password(self, db_session, test_user):
        """Test autenticación con contraseña incorrecta"""
        service = UserService(db_session)

        user = await service.authenticate("testuser", "wrongpassword")

        assert user is None

    @pytest.mark.asyncio
    async def test_authenticate_user_not_found(self, db_session):
        """Test autenticación con usuario que no existe"""
        service = UserService(db_session)

        user = await service.authenticate("nonexistent", "password")

        assert user is None

    @pytest.mark.asyncio
    async def test_get_by_username(self, db_session, test_user):
        """Test obtener usuario por username"""
        service = UserService(db_session)

        user = await service.get_by_username("testuser")

        assert user is not None
        assert user.id == test_user.id

    @pytest.mark.asyncio
    async def test_get_by_username_not_found(self, db_session):
        """Test obtener usuario por username que no existe"""
        service = UserService(db_session)

        user = await service.get_by_username("nonexistent")

        assert user is None

    @pytest.mark.asyncio
    async def test_get_by_id(self, db_session, test_user):
        """Test obtener usuario por ID"""
        service = UserService(db_session)

        user = await service.get_by_id(test_user.id)

        assert user is not None
        assert user.username == "testuser"

    @pytest.mark.asyncio
    async def test_update_user(self, db_session, test_user):
        """Test actualizar usuario"""
        service = UserService(db_session)

        update_data = UserUpdate(
            email="updated@example.com",
            role=UserRole.MANAGEMENT,
        )

        updated = await service.update_user(test_user.id, update_data)

        assert updated.email == "updated@example.com"
        assert updated.role == UserRole.MANAGEMENT

    @pytest.mark.asyncio
    async def test_update_user_password(self, db_session, test_user):
        """Test actualizar contraseña de usuario"""
        service = UserService(db_session)

        update_data = UserUpdate(password="newpassword456")

        updated = await service.update_user(test_user.id, update_data)

        assert updated.hashed_password is not None

        # Verificar que la nueva contraseña funciona
        user = await service.authenticate("testuser", "newpassword456")
        assert user is not None

    @pytest.mark.asyncio
    async def test_update_username_duplicate(self, db_session, test_user):
        """Test que no se puede actualizar a username duplicado"""
        # Crear segundo usuario
        service = UserService(db_session)
        user2_data = UserCreate(
            username="user2",
            email="user2@example.com",
            password="password123",
            role=UserRole.SALES,
        )
        user2 = await service.create_user(user2_data)

        # Intentar cambiar al username del primero
        update_data = UserUpdate(username=test_user.username)

        with pytest.raises(ValueError, match="already exists"):
            await service.update_user(user2.id, update_data)

    @pytest.mark.asyncio
    async def test_list_users(self, db_session, test_user):
        """Test listar usuarios"""
        service = UserService(db_session)

        users = await service.list_all()

        assert len(users) >= 1

    @pytest.mark.asyncio
    async def test_delete_user(self, db_session, test_user):
        """Test eliminar usuario"""
        service = UserService(db_session)

        await service.delete(test_user.id)

        deleted = await service.get_by_id(test_user.id)
        assert deleted is None
