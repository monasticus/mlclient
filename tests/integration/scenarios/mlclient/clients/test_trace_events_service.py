from __future__ import annotations

from uuid import uuid4

import pytest

from mlclient import MLClient
from mlclient.exceptions import MarkLogicError
from mlclient.services import TraceEventsService


@pytest.fixture(scope="class")
def ml_client():
    with MLClient() as ml:
        yield ml


class TestTraceEventsService:
    GROUP = "Default"

    @pytest.mark.ml_access
    def test_activation_round_trip_preserves_events(self, ml_client):
        service = TraceEventsService(ml_client.rest)
        original = service.get(group=self.GROUP)
        try:
            changed = service.set_activated(
                value=not original.activated,
                group=self.GROUP,
                timeout=5,
            )
            assert changed.activated is not original.activated
            assert changed.events == original.events
            assert service.get(group=self.GROUP) == changed
            assert (
                service.set_activated(
                    value=changed.activated,
                    group=self.GROUP,
                )
                == changed
            )
        finally:
            service.set_activated(value=original.activated, group=self.GROUP)
        assert service.get(group=self.GROUP) == original

    @pytest.mark.ml_access
    def test_event_round_trip_is_idempotent_and_preserves_other_settings(
        self,
        ml_client,
    ):
        service = TraceEventsService(ml_client.rest)
        original = service.get(group=self.GROUP)
        event = f"MLClient integration {uuid4()}"
        try:
            added = service.set_event(event, enabled=True, group=self.GROUP, timeout=5)
            assert added.activated == original.activated
            assert added.events == tuple(sorted((*original.events, event)))
            assert service.get(group=self.GROUP) == added
            assert service.set_event(event, enabled=True, group=self.GROUP) == added
            assert service.set_event(event, enabled=False, group=self.GROUP) == original
            assert service.set_event(event, enabled=False, group=self.GROUP) == original
        finally:
            service.set_event(event, enabled=False, group=self.GROUP)
        assert service.get(group=self.GROUP) == original

    @pytest.mark.ml_access
    def test_missing_group_surfaces_a_marklogic_error(self, ml_client):
        service = TraceEventsService(ml_client.rest)
        with pytest.raises(MarkLogicError):
            service.get(group=f"MLClient missing group {uuid4()}")
