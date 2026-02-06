"""
Pytest configuration and fixtures
"""
import pytest
from django.conf import settings


def pytest_configure(config):
    """Configure pytest Django settings"""
    settings.DEBUG = False
    settings.TESTING = True


@pytest.fixture(autouse=True)
def enable_db_access_for_all_tests(db):
    """Allow all tests to access database"""
    pass
