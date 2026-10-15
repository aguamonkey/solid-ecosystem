import json
from collections.abc import Callable, Iterable
from dataclasses import asdict, dataclass
from types import MappingProxyType

from .domain import StoredReading
from .ports import ReadingPager


@dataclass(frozen=True)
class Artifact:
    body: str
    media_type: str


Renderer = Callable[[tuple[StoredReading, ...]], Artifact]


class Exporters:
    def __init__(self, registrations: Iterable[tuple[str, Renderer]]) -> None:
        captured: dict[str, Renderer] = {}
        for name, renderer in registrations:
            if not name.strip() or name in captured:
                raise ValueError("Blank or duplicate export format")
            captured[name] = renderer
        self._renderers = MappingProxyType(captured)

    def render(self, name: str, readings: tuple[StoredReading, ...]) -> Artifact:
        return self._renderers[name](readings)

    def formats(self) -> tuple[str, ...]:
        return tuple(self._renderers)


def json_export(readings: tuple[StoredReading, ...]) -> Artifact:
    return Artifact(
        json.dumps([asdict(row) for row in readings], allow_nan=False),
        "application/json",
    )


def text_export(readings: tuple[StoredReading, ...]) -> Artifact:
    lines = []
    for row in readings:
        value = row.observation
        station = json.dumps(value.station, ensure_ascii=False)
        lines.append(
            f"{row.sequence} / {value.identity} / {station}: {value.kelvin:.2f} K"
        )
    return Artifact("\n".join(lines), "text/plain")


def default_exports() -> Exporters:
    return Exporters((("json", json_export), ("text", text_export)))


def export_page(
    reader: ReadingPager, exporters: Exporters, name: str, after: int, limit: int
) -> tuple[Artifact, int | None]:
    page = reader.page(after, limit)
    return exporters.render(name, page.readings), page.next_cursor
