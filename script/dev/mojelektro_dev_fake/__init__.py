"""DEVELOPMENT ONLY. Never install this in a real Home Assistant.

Replaces the Moj Elektro Plus HTTP layer with synthetic data so the setup
flow, entities and sidebar page can be exercised without a real token.
It is mounted only by script/dev-ha and is not part of the HACS package.
Any token is accepted except "invalid" (returns 401).
"""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
import math
from zoneinfo import ZoneInfo

LJ = ZoneInfo("Europe/Ljubljana")
IMPORT_RT = "32.0.2.4.1.2.12.0.0.0.0.0.0.0.0.3.72.0"
EXPORT_RT = "32.0.2.4.19.2.12.0.0.0.0.0.0.0.0.3.72.0"
METERS = {"4-93571", "9-12345"}


def _value(end: datetime, register: str, meter: str) -> float | None:
    local = (end - timedelta(minutes=15)).astimezone(LJ)
    hour = local.hour + local.minute / 60
    seed = (int(end.timestamp()) // 900) * 2654435761 % 1000 / 1000
    if register == "import":
        base = 0.06 + 0.05 * seed
        peak = 0.35 * math.exp(-((hour - 7.5) ** 2) / 1.5) + 0.55 * math.exp(
            -((hour - 19) ** 2) / 4
        )
        winter = 1.3 if local.month in (11, 12, 1, 2) else 1.0
        return round((base + peak) * winter, 3)
    if meter != "4-93571":
        return None
    sun = max(0.0, math.sin(math.pi * (hour - 6) / 14))
    season = 0.3 + 0.7 * math.sin(math.pi * (local.timetuple().tm_yday - 30) / 300) ** 2
    return round(max(0.0, 0.9 * sun * season - 0.15), 3)


def _readings(meter: str, start: date, end: date, options: list[str]) -> dict:
    now = datetime.now(UTC)
    published = datetime(
        now.astimezone(LJ).year, now.astimezone(LJ).month, now.astimezone(LJ).day, tzinfo=LJ
    )
    blocks = []
    for option in options:
        rt = option.split("=", 1)[1]
        register = {IMPORT_RT: "import", EXPORT_RT: "export"}.get(rt)
        if register is None or (register == "export" and meter != "4-93571"):
            continue
        moment = datetime(start.year, start.month, start.day, tzinfo=LJ).astimezone(
            UTC
        ) + timedelta(minutes=15)
        last = min(datetime(end.year, end.month, end.day, tzinfo=LJ), published).astimezone(UTC)
        items = []
        while moment <= last:
            epoch = int(moment.timestamp())
            item = {"timestamp": moment.astimezone(LJ).isoformat()}
            if epoch % (86400 * 9) not in range(3600 * 3, 3600 * 3 + 1800):  # occasional gaps
                item["value"] = str(_value(moment, register, meter))
            if epoch % (86400 * 5) == 3600 * 12:
                item["readingQualities"] = [{"readingQualityType": "DEV.ESTIMATED"}]
            items.append(item)
            moment += timedelta(minutes=15)
        blocks.append({"readingType": rt, "intervalReadings": items})
    return {
        "usagePoint": "000000000000000000",
        "messageCreated": now.isoformat(),
        "intervalBlocks": blocks,
    }


def _install() -> None:
    from custom_components.mojelektro_plus import api

    async def fake_request_once(self, url, params):
        from custom_components.mojelektro_plus.api import (
            AccessDenied,
            InvalidAuth,
            InvalidRequest,
        )

        self.request_count += 1
        if self._token == "invalid":
            raise InvalidAuth("Token rejected: E.4.001 (dev fake)")
        path = url.split("/mojelektro/v1", 1)[1]
        if path == "/reading-type":
            return [
                {
                    "oznaka": "A+",
                    "perioda": "15 min",
                    "vrsta": "KOLICINA",
                    "readingType": IMPORT_RT,
                },
                {
                    "oznaka": "A-",
                    "perioda": "15 min",
                    "vrsta": "KOLICINA",
                    "readingType": EXPORT_RT,
                },
            ]
        if path == "/reading-qualities":
            return [
                {"readingQualityType": "DEV.ESTIMATED", "description": "Synthetic estimated value"}
            ]
        if path.startswith("/merilno-mesto/"):
            if path.rsplit("/", 1)[1] not in METERS:
                raise AccessDenied("Access denied: E.4.003 (dev fake)")
            return {
                "identifikator": {"gsrn": "000000000000000000"},
                "merilneTocke": [{"gsrn": "000000000000000001", "vrsta": "OMTO"}],
                "tehnicniPodatki": {"tipStevca": "DEV-FAKE"},
            }
        if path == "/meter-readings":
            q = {}
            options = []
            for key, value in params:
                if key == "option":
                    options.append(value)
                else:
                    q[key] = value
            if q["usagePoint"] not in METERS:
                raise AccessDenied("Access denied (dev fake)")
            start, end = date.fromisoformat(q["startTime"]), date.fromisoformat(q["endTime"])
            if (end - start).days > 35 or not options:
                raise InvalidRequest("Invalid request (dev fake)")
            return _readings(q["usagePoint"], start, end, options)
        raise InvalidRequest("Unknown path (dev fake)")

    api.MojElektroClient._request_once = fake_request_once


_install()


async def async_setup(hass, config):
    return True
