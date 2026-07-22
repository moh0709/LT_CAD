"""Grid-based component placement and physical mounting constraints."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Box:
    x: float
    y: float
    width: float
    height: float

    @property
    def right(self) -> float:
        return self.x + self.width

    @property
    def bottom(self) -> float:
        return self.y + self.height

    @property
    def center_x(self) -> float:
        return self.x + self.width / 2

    def tuple(self) -> tuple[float, float, float, float]:
        return (self.x, self.y, self.width, self.height)


@dataclass(frozen=True)
class Grid:
    unit: float = 5.0
    tolerance: float = 1e-6

    def is_snapped(self, value: float) -> bool:
        return abs(value / self.unit - round(value / self.unit)) <= self.tolerance

    def box(self, x: float, y: float, width: float, height: float) -> Box:
        values = {"x": x, "y": y, "width": width, "height": height}
        unsnapped = [name for name, value in values.items() if not self.is_snapped(value)]
        if unsnapped:
            raise ValueError(f"Values are not snapped to {self.unit:g} mm grid: {unsnapped}")
        return Box(x, y, width, height)

    def mounted_on_top(
        self,
        host: Box,
        width: float,
        height: float,
        host_surface_offset: float = 0.0,
    ) -> Box:
        if not self.is_snapped(width) or not self.is_snapped(height):
            raise ValueError("Mounted component size must be grid-snapped.")
        x = host.center_x - width / 2
        if not self.is_snapped(host_surface_offset):
            raise ValueError("Host mounting-surface offset must be grid-snapped.")
        y = host.y + host_surface_offset - height
        if not self.is_snapped(x) or not self.is_snapped(y):
            raise ValueError("Centred mount does not land on the configured grid.")
        return Box(x, y, width, height)


def validate_top_mount(
    child: Box,
    host: Box,
    host_surface_offset: float = 0.0,
    tolerance: float = 1e-6,
) -> list[str]:
    errors: list[str] = []
    mount_y = host.y + host_surface_offset
    if abs(child.bottom - mount_y) > tolerance:
        errors.append("Mounted component bottom does not contact host mounting surface.")
    if abs(child.center_x - host.center_x) > tolerance:
        errors.append("Mounted component is not centred on host.")
    return errors
