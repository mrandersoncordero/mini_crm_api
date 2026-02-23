import pytest
from datetime import datetime, timedelta
from app.services.lead_service import LeadService
from app.schemas.lead import LeadCreate, LeadUpdate
from app.utils.enums import Channel, LeadStatus


class TestLeadService:
    """Tests para LeadService"""

    @pytest.mark.asyncio
    async def test_create_lead(
        self, db_session, mock_email_service, test_client, test_user
    ):
        """Test crear lead"""
        service = LeadService(db_session, test_user.id)

        lead_data = LeadCreate(
            client_id=test_client.id,
            channel=Channel.WEB,
            status=LeadStatus.NEW,
        )

        lead = await service.create_lead(lead_data)

        assert lead.id is not None
        assert lead.client_id == test_client.id
        assert lead.channel == Channel.WEB
        assert lead.status == LeadStatus.NEW
        assert lead.created_by_id == test_user.id

    @pytest.mark.asyncio
    async def test_create_lead_whatsapp_channel(
        self, db_session, mock_email_service, test_client, test_user
    ):
        """Test crear lead por WhatsApp"""
        service = LeadService(db_session, test_user.id)

        lead_data = LeadCreate(
            client_id=test_client.id,
            channel=Channel.WHATSAPP,
            status=LeadStatus.NEW,
        )

        lead = await service.create_lead(lead_data)

        assert lead.channel == Channel.WHATSAPP

    @pytest.mark.asyncio
    async def test_get_lead_by_id(self, db_session, test_user, test_lead):
        """Test obtener lead por ID"""
        service = LeadService(db_session, test_user.id)

        lead = await service.get_by_id(test_lead.id)

        assert lead is not None
        assert lead.id == test_lead.id

    @pytest.mark.asyncio
    async def test_get_lead_with_details(self, db_session, test_user, test_lead):
        """Test obtener lead con detalles del cliente"""
        service = LeadService(db_session, test_user.id)

        lead = await service.get_lead_with_details(test_lead.id)

        assert lead is not None
        assert lead.client is not None

    @pytest.mark.asyncio
    async def test_update_lead(self, db_session, test_user, test_lead):
        """Test actualizar lead"""
        service = LeadService(db_session, test_user.id)

        update_data = LeadUpdate(
            admin_notes="Nueva nota de administración",
            sales_notes="Nueva nota de ventas",
        )

        updated = await service.update_lead(test_lead.id, update_data)

        assert updated.admin_notes == "Nueva nota de administración"
        assert updated.sales_notes == "Nueva nota de ventas"

    @pytest.mark.asyncio
    async def test_update_lead_status(
        self, db_session, mock_email_service, test_user, test_lead
    ):
        """Test actualizar estado del lead"""
        service = LeadService(db_session, test_user.id)

        updated = await service.update_status(test_lead.id, LeadStatus.CONTACTED)

        assert updated.status == LeadStatus.CONTACTED

    @pytest.mark.asyncio
    async def test_update_lead_status_closes(
        self, db_session, mock_email_service, test_user, test_lead
    ):
        """Test cambiar estado a cerrado"""
        service = LeadService(db_session, test_user.id)

        updated = await service.update_status(test_lead.id, LeadStatus.CLOSED)

        assert updated.status == LeadStatus.CLOSED

    @pytest.mark.asyncio
    async def test_update_lead_status_same_no_notification(
        self, db_session, mock_email_service, test_user, test_lead
    ):
        """Test que no envía notificación si el estado no cambia"""
        service = LeadService(db_session, test_user.id)

        # Ya está en NEW, volver a设置 NEW
        updated = await service.update_status(test_lead.id, LeadStatus.NEW)

        # No debería enviar notificación porque no cambió
        # mock_email_service no debería haber sido llamado
        mock_email_service.notify_lead_status_change.assert_not_called()

    @pytest.mark.asyncio
    async def test_assign_lead(self, db_session, test_user, test_lead, test_user_sales):
        """Test asignar lead a usuario"""
        service = LeadService(db_session, test_user.id)

        updated = await service.assign_lead(test_lead.id, test_user_sales.id)

        assert updated.assigned_to_id == test_user_sales.id

    @pytest.mark.asyncio
    async def test_list_leads(self, db_session, test_user, test_lead):
        """Test listar leads"""
        service = LeadService(db_session, test_user.id)

        leads = await service.list_leads()

        assert len(leads) > 0

    @pytest.mark.asyncio
    async def test_list_leads_with_filters(self, db_session, test_user, test_lead):
        """Test listar leads con filtros"""
        service = LeadService(db_session, test_user.id)

        leads = await service.list_leads(status=LeadStatus.NEW)

        assert all(l.status == LeadStatus.NEW for l in leads)

    @pytest.mark.asyncio
    async def test_list_leads_by_channel(self, db_session, test_user, test_lead):
        """Test listar leads por canal"""
        service = LeadService(db_session, test_user.id)

        leads = await service.list_leads(channel="web")

        assert all(l.channel == Channel.WEB for l in leads)

    @pytest.mark.asyncio
    async def test_advanced_search_by_status(self, db_session, test_user, test_lead):
        """Test búsqueda avanzada por estado"""
        service = LeadService(db_session, test_user.id)

        leads = await service.advanced_search(status=LeadStatus.NEW)

        assert len(leads) >= 1

    @pytest.mark.asyncio
    async def test_advanced_search_by_client_id(
        self, db_session, test_user, test_client, test_lead
    ):
        """Test búsqueda avanzada por ID de cliente"""
        service = LeadService(db_session, test_user.id)

        leads = await service.advanced_search(client_id=test_client.id)

        assert len(leads) >= 1
        assert all(l.client_id == test_client.id for l in leads)

    @pytest.mark.asyncio
    async def test_advanced_search_by_date_range(
        self, db_session, test_user, test_lead
    ):
        """Test búsqueda avanzada por rango de fechas"""
        service = LeadService(db_session, test_user.id)

        now = datetime.utcnow()
        date_from = now - timedelta(days=1)
        date_to = now + timedelta(days=1)

        leads = await service.advanced_search(date_from=date_from, date_to=date_to)

        assert len(leads) >= 1

    @pytest.mark.asyncio
    async def test_get_stats_by_status(self, db_session, test_user, test_lead):
        """Test obtener estadísticas por estado"""
        service = LeadService(db_session, test_user.id)

        stats = await service.get_stats_by_status()

        assert "new" in stats
        assert stats["new"] >= 1

    @pytest.mark.asyncio
    async def test_get_stats_by_channel(self, db_session, test_user, test_lead):
        """Test obtener estadísticas por canal"""
        service = LeadService(db_session, test_user.id)

        stats = await service.get_stats_by_channel()

        assert "web" in stats

    @pytest.mark.asyncio
    async def test_get_recent_leads(self, db_session, test_user, test_lead):
        """Test obtener leads recientes"""
        service = LeadService(db_session, test_user.id)

        leads = await service.get_recent_leads(hours=24)

        assert len(leads) >= 1

    @pytest.mark.asyncio
    async def test_get_leads_by_client(
        self, db_session, test_user, test_client, test_lead
    ):
        """Test obtener leads por cliente"""
        service = LeadService(db_session, test_user.id)

        leads = await service.get_leads_by_client(test_client.id)

        assert len(leads) >= 1

    @pytest.mark.asyncio
    async def test_delete_lead(self, db_session, test_user, test_lead):
        """Test eliminar lead"""
        service = LeadService(db_session, test_user.id)
        lead_id = test_lead.id

        await service.delete(lead_id)

        deleted = await service.get_by_id(lead_id)
        assert deleted is None
