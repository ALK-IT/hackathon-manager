from fastapi import Request

from src.auth.config import get_trust_proxy_headers


def get_client_ip(request: Request) -> str:
    client_ip = request.client.host if request.client else "unknown-client"
    if get_trust_proxy_headers():
        proxy_ip = request.headers.get("X-Real-IP", "").strip()
        if proxy_ip:
            return proxy_ip
    return client_ip
