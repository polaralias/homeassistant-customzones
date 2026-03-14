"""Test configuration for Custom Zone."""

import asyncio

import pytest


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable loading integrations from the repository under test."""
    yield


@pytest.fixture(autouse=True)
def auto_enable_socket(socket_enabled):
    """Allow event-loop socketpair creation on Windows-based test runs."""
    yield


@pytest.fixture
def event_loop_policy(socket_enabled):
    """Allow socket access before pytest-asyncio creates the event loop."""
    return asyncio.get_event_loop_policy()
