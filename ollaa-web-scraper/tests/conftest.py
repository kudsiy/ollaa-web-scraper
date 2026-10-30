"""
Offline guard for every test (task W2): a test may never visit a website, open the database
or start a browser. Any attempt fails the test at once. Live website checks are in tools/
and are run only with the owner's approval.
"""
import ipaddress
import socket

import playwright.async_api
import psycopg2
import pytest

_real_getaddrinfo = socket.getaddrinfo
_real_connect = socket.socket.connect


def _is_local(host) -> bool:
    if isinstance(host, bytes):
        host = host.decode()
    if host in (None, "localhost"):
        return True
    try:
        return ipaddress.ip_address(host).is_loopback
    except ValueError:
        return False


def _offline_getaddrinfo(host, *args, **kwargs):
    if not _is_local(host):
        raise RuntimeError(f"Tests must stay offline: tried to look up {host}")
    return _real_getaddrinfo(host, *args, **kwargs)


def _offline_connect(sock, address):
    host = address[0] if isinstance(address, tuple) else address
    if not _is_local(host):
        raise RuntimeError(f"Tests must stay offline: tried to connect to {host}")
    return _real_connect(sock, address)


def _no_database(*args, **kwargs):
    raise RuntimeError("Tests must not open the database")


def _no_browser(*args, **kwargs):
    raise RuntimeError("Tests must not start a browser")


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    # Local addresses stay allowed: Python itself uses them on Windows (asyncio). The
    # database is blocked separately, because psycopg2 does not use Python's sockets.
    monkeypatch.setattr(socket, "getaddrinfo", _offline_getaddrinfo)
    monkeypatch.setattr(socket.socket, "connect", _offline_connect)
    monkeypatch.setattr(psycopg2, "connect", _no_database)
    monkeypatch.setattr(playwright.async_api, "async_playwright", _no_browser)
