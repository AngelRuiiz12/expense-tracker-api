from datetime import UTC, datetime, timedelta
from typing import Annotated

from fastapi import Depends, HTTPException, Request, status

# Almacenamiento en memoria: {ip: {attemps: int, reset_at: datetime}}
_rate_limit_store: dict[str, dict[str, int | datetime]] = {}


def _get_client_ip(request: Request) -> str:
    """Extrae la IP del cliente del request."""
    return request.client.host or "unknown"


def _cleanup_expired_entries() -> None:
    """Limpia entradas expiradas del almacén."""
    now = datetime.now(UTC)
    expired_ips = [
        ip
        for ip, data in _rate_limit_store.items()
        if data.get("reset_at") and data["reset_at"] <= now
    ]

    for ip in expired_ips:
        del _rate_limit_store[ip]


def check_rate_limit(
    request: Request, max_attemps: int = 5, window_minutes: int = 1
) -> None:
    """Verifica si el cliente ha excedido el límite de intentos."""

    _cleanup_expired_entries()

    client_ip = _get_client_ip(request)
    now = datetime.now(UTC)

    # Si la IP no existe o su ventana expiró, crear nueva entrada
    if client_ip not in _rate_limit_store:
        _rate_limit_store[client_ip] = {
            "attemps": 1,
            "reset_at": now + timedelta(minutes=window_minutes),
        }
        return

    entry = _rate_limit_store[client_ip]
    reset_at = entry.get("reset_at")

    # Si la ventana expiró, resetear
    if reset_at and now >= reset_at:
        _rate_limit_store[client_ip] = {
            "attemps": 1,
            "reset_at": now + timedelta(minutes=window_minutes),
        }
        return

    # Incrementar intentos
    entry["attemps"] = entry.get("attemps", 0) + 1

    # Verificar si se excedió el límite
    if entry["attemps"] > max_attemps:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Demasiados intentos de login. Intenta de nuevo más tarde.",
            headers={"Retry-After": str(int((reset_at - now).total_seconds()))},
        )


async def _rate_limit_check(request: Request) -> None:
    check_rate_limit(request)


LoginRateLimit = Annotated[None, Depends(_rate_limit_check)]
