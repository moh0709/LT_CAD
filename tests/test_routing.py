import pytest

from lt_cad.routing import rounded_orthogonal_path, route_collisions


def test_rounded_route_uses_quadratic_bend() -> None:
    path = rounded_orthogonal_path([(0, 0), (20, 0), (20, 20)], radius=4)
    assert path == "M 0 0 L 16 0 Q 20 0 20 4 L 20 20"


def test_diagonal_segment_is_rejected() -> None:
    with pytest.raises(ValueError, match="not orthogonal"):
        rounded_orthogonal_path([(0, 0), (10, 10)])


def test_route_through_machine_is_detected() -> None:
    obstacles = {"ext": (20, 20, 30, 30)}
    assert route_collisions([(10, 30), (60, 30)], obstacles) == ["ext"]


def test_route_around_machine_is_clear() -> None:
    obstacles = {"ext": (20, 20, 30, 30)}
    route = [(10, 60), (15, 60), (15, 10), (60, 10)]
    assert route_collisions(route, obstacles, clearance=2) == []


def test_port_route_starts_horizontally_before_bend() -> None:
    route = [(20, 30), (30, 30), (30, 50)]
    assert route[0][1] == route[1][1]
    assert "Q 30 30" in rounded_orthogonal_path(route, radius=4)
