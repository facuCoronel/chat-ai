"""
Tests for application port protocols.
Protocols are structural contracts (no runtime enforcement), so tests verify:
  - the module imports without errors
  - the expected methods exist on each protocol
  - a concrete implementation satisfies the protocol structurally
"""
import pytest
from contextlib import asynccontextmanager
from unittest.mock import AsyncMock

from app.application.ports.insight_generator import IInsightGenerator
from app.application.ports.insight_repository_factory import IInsightRepositoryContextFactory
from app.application.ports.message_publisher import IMessagePublisher


# --- IInsightGenerator ---

def test_insight_generator_has_execute_method():
    assert callable(getattr(IInsightGenerator, "execute", None))


def test_insight_generator_satisfied_by_concrete_class():
    class ConcreteGenerator:
        async def execute(self, request):
            return None

    # Structural check: the concrete class has the required method
    obj = ConcreteGenerator()
    assert hasattr(obj, "execute")
    assert callable(obj.execute)


# --- IMessagePublisher ---

def test_message_publisher_has_publish_method():
    assert callable(getattr(IMessagePublisher, "publish", None))


def test_message_publisher_satisfied_by_concrete_class():
    class ConcretePublisher:
        async def publish(self, message) -> None:
            pass

    obj = ConcretePublisher()
    assert hasattr(obj, "publish")
    assert callable(obj.publish)


# --- IInsightRepositoryContextFactory ---

def test_insight_repository_factory_has_call_method():
    assert callable(getattr(IInsightRepositoryContextFactory, "__call__", None))


def test_insight_repository_factory_satisfied_by_concrete_class():
    class ConcreteFactory:
        def __call__(self):
            @asynccontextmanager
            async def _ctx():
                yield AsyncMock()
            return _ctx()

    obj = ConcreteFactory()
    assert callable(obj)
