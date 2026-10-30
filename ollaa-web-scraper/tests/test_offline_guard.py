"""
The offline guard in conftest.py really blocks the internet, the database and the browser.

The addresses used here reach nobody even if the guard broke: 192.0.2.1 is a documentation
address (TEST-NET-1) and ".invalid" names never exist.
"""
import socket

import psycopg2
import pytest
import requests


def test_no_internet_lookup():
    with pytest.raises(RuntimeError, match="offline"):
        socket.getaddrinfo("example.invalid", 443)


def test_no_internet_connection():
    with pytest.raises(RuntimeError, match="offline"):
        socket.create_connection(("192.0.2.1", 80), timeout=1)


def test_no_website_request():
    session = requests.Session()
    session.trust_env = False  # ignore any proxy settings on the computer
    with pytest.raises(RuntimeError, match="offline"):
        session.get("http://192.0.2.1/", timeout=1)


def test_no_database():
    with pytest.raises(RuntimeError, match="database"):
        psycopg2.connect("host=192.0.2.1 connect_timeout=1")


def test_no_browser():
    from playwright.async_api import async_playwright
    with pytest.raises(RuntimeError, match="browser"):
        async_playwright()
