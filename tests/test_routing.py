import pytest

from lt_cad.routing import (
    drying_air_circuit_routes,
    rounded_orthogonal_path,
    route_collisions,
    route_direction_arrow,
)


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


def test_drying_air_circuit_uses_dfd_top_and_dh_side_connections() -> None:
    routes = drying_air_circuit_routes(
        dfd_supply=(40, 50),
        dfd_return=(50, 50),
        dh_supply=(10, 30),
        dh_return=(10, 20),
    )
    assert routes["supply"] == [(40, 50), (40, 30), (10, 30)]
    assert routes["return"] == [(10, 20), (50, 20), (50, 50)]
    supply_arrow = route_direction_arrow(routes["supply"])
    return_arrow = route_direction_arrow(routes["return"])
    assert supply_arrow[1][0] < supply_arrow[0][0]
    assert return_arrow[1][0] > return_arrow[0][0]


def test_drying_air_horizontal_leg_stretches_with_machine_spacing() -> None:
    near = drying_air_circuit_routes((40, 50), (50, 50), (10, 30), (10, 20))
    far = drying_air_circuit_routes((80, 50), (90, 50), (10, 30), (10, 20))
    near_length = abs(near["supply"][2][0] - near["supply"][1][0])
    far_length = abs(far["supply"][2][0] - far["supply"][1][0])
    assert far_length > near_length
