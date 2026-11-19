"""Shared fixtures. The real Moj Elektro API is never called."""

from __future__ import annotations

from collections.abc import Generator
from datetime import date
from unittest.mock import patch

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.mojelektro_plus.const import (
    CONF_HISTORY_MONTHS,
    CONF_METER_ID,
    CONF_REFRESH_HOURS,
    CONF_SIDEBAR,
    CONF_TOKEN,
    DOMAIN,
)

from .fake_api import METER, TOKEN, FakeMojElektro

# 2026-04-10 10:00 local time; the recent window crosses the March DST change.
NOW = "2026-04-10T08:00:00+00:00"
TODAY = date(2026, 4, 10)


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    yield


@pytest.fixture(autouse=True)
def fast_timing() -> Generator[None]:
    with (
        patch("custom_components.mojelektro_plus.api.MIN_SPACING", 0),
        patch("custom_components.mojelektro_plus.api.DEFAULT_BACKOFF", 0),
        patch("custom_components.mojelektro_plus.coordinator.BACKFILL_PAUSE", 0),
    ):
        yield


@pytest.fixture
def frozen(freezer):
    freezer.move_to(NOW)
    return freezer


@pytest.fixture
def fake_api(aioclient_mock, frozen) -> FakeMojElektro:
    fake = FakeMojElektro(TODAY)
    fake.attach(aioclient_mock)
    return fake


def make_entry(history: int = 2, sidebar: bool = True, meter: str = METER, **kw) -> MockConfigEntry:
    return MockConfigEntry(
        domain=DOMAIN,
        title=kw.pop("title", f"Moj Elektro {meter}"),
        unique_id=meter,
        data={CONF_TOKEN: TOKEN, CONF_METER_ID: meter},
        options={CONF_HISTORY_MONTHS: history, CONF_REFRESH_HOURS: 6.0, CONF_SIDEBAR: sidebar},
        **kw,
    )


@pytest.fixture
def entry() -> MockConfigEntry:
    return make_entry()
