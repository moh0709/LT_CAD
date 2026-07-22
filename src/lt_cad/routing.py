"""Orthogonal pipe routing helpers with rounded bends and collision checks."""

from __future__ import annotations

from math import hypot
from typing import Iterable

Point = tuple[float, float]
Rect = tuple[float, float, float, float]


def rounded_orthogonal_path(points: list[Point], radius: float = 4.0) -> str:
    """Return an SVG path for orthogonal points using quadratic rounded corners."""
    if len(points) < 2:
        raise ValueError("A route requires at least two points.")
    for first, second in zip(points, points[1:]):
        if first[0] != second[0] and first[1] != second[1]:
            raise ValueError(f"Route segment is not orthogonal: {first} -> {second}")

    commands = [f"M {points[0][0]} {points[0][1]}"]
    for index in range(1, len(points) - 1):
        previous, corner, following = points[index - 1], points[index], points[index + 1]
        incoming = (corner[0] - previous[0], corner[1] - previous[1])
        outgoing = (following[0] - corner[0], following[1] - corner[1])
        if incoming[0] * outgoing[1] == incoming[1] * outgoing[0]:
            commands.append(f"L {corner[0]} {corner[1]}")
            continue
        bend = min(radius, hypot(*incoming) / 2, hypot(*outgoing) / 2)
        before = (
            corner[0] - (incoming[0] / hypot(*incoming)) * bend,
            corner[1] - (incoming[1] / hypot(*incoming)) * bend,
        )
        after = (
            corner[0] + (outgoing[0] / hypot(*outgoing)) * bend,
            corner[1] + (outgoing[1] / hypot(*outgoing)) * bend,
        )
        commands.append(f"L {before[0]:g} {before[1]:g}")
        commands.append(f"Q {corner[0]:g} {corner[1]:g} {after[0]:g} {after[1]:g}")
    commands.append(f"L {points[-1][0]} {points[-1][1]}")
    return " ".join(commands)


def drying_air_circuit_routes(
    dfd_supply: Point,
    dfd_return: Point,
    dh_supply: Point,
    dh_return: Point,
) -> dict[str, list[Point]]:
    """Route the standard two-pipe DFD/DH drying-air circuit.

    DFD connections are on the cabinet top and therefore leave vertically. DH
    connections are on the side facing the DFD and therefore enter horizontally.
    The horizontal leg automatically stretches when machine spacing changes.
    """
    return {
        "supply": [dfd_supply, (dfd_supply[0], dh_supply[1]), dh_supply],
        "return": [dh_return, (dfd_return[0], dh_return[1]), dfd_return],
    }


def route_direction_arrow(points: list[Point], length: float = 6.0) -> tuple[Point, Point]:
    """Place a direction arrow on the longest horizontal segment of a route."""
    horizontal = [
        (start, end)
        for start, end in zip(points, points[1:])
        if start[1] == end[1] and start[0] != end[0]
    ]
    if not horizontal:
        raise ValueError("A direction arrow requires a horizontal route segment.")
    start, end = max(horizontal, key=lambda segment: abs(segment[1][0] - segment[0][0]))
    direction = 1.0 if end[0] > start[0] else -1.0
    midpoint_x = (start[0] + end[0]) / 2
    half = min(length / 2, abs(end[0] - start[0]) / 4)
    y = start[1]
    return (
        (midpoint_x - direction * half, y),
        (midpoint_x + direction * half, y),
    )


def route_collisions(
    points: list[Point],
    obstacles: dict[str, Rect],
    ignore: Iterable[str] = (),
    clearance: float = 0.0,
) -> list[str]:
    """Return obstacle IDs intersected by route segments, excluding endpoint tangency."""
    ignored = set(ignore)
    collisions: list[str] = []
    for obstacle_id, (x, y, width, height) in obstacles.items():
        if obstacle_id in ignored:
            continue
        left, right = x - clearance, x + width + clearance
        top, bottom = y - clearance, y + height + clearance
        hit = False
        for start, end in zip(points, points[1:]):
            if start[0] == end[0]:
                sx = start[0]
                low, high = sorted((start[1], end[1]))
                hit = left < sx < right and max(low, top) < min(high, bottom)
            else:
                sy = start[1]
                low, high = sorted((start[0], end[0]))
                hit = top < sy < bottom and max(low, left) < min(high, right)
            if hit:
                break
        if hit:
            collisions.append(obstacle_id)
    return collisions
