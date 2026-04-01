from collections import defaultdict
from typing import Callable, Any
import asyncio
import logging

logger = logging.getLogger(__name__)


class EventBus:
    """
    Mediador interno en memoria.
    Los módulos publican eventos; otros módulos se suscriben.
    Nunca hay un import directo entre módulos.
    """

    def __init__(self):
        self._subscribers: dict[str, list[Callable]] = defaultdict(list)

    def subscribe(self, event_name: str, handler: Callable):
        self._subscribers[event_name].append(handler)
        logger.info(f"[EventBus] Suscriptor registrado: {event_name} → {handler.__name__}")

    async def publish(self, event_name: str, payload: dict[str, Any]):
        handlers = self._subscribers.get(event_name, [])
        if not handlers:
            logger.warning(f"[EventBus] Evento sin suscriptores: {event_name}")
            return

        # Ejecuta todos los handlers concurrentemente
        await asyncio.gather(
            *[handler(payload) for handler in handlers],
            return_exceptions=True  # no rompe si un handler falla
        )


# Singleton global — importado por cualquier módulo que necesite publicar/suscribir
event_bus = EventBus()