import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CATALOGUE = ROOT / "component_library" / "manifest" / "catalogue_v0.json"


def test_catalogue_has_unique_component_ids() -> None:
    data = json.loads(CATALOGUE.read_text(encoding="utf-8"))
    ids = [component["id"] for component in data["components"]]
    assert len(ids) == len(set(ids))


def test_unapproved_components_have_no_anchors() -> None:
    data = json.loads(CATALOGUE.read_text(encoding="utf-8"))
    for component in data["components"]:
        if component["status"] == "needs_review":
            assert component["anchors"] == []


def test_source_is_millimetre_dxf() -> None:
    data = json.loads(CATALOGUE.read_text(encoding="utf-8"))
    assert data["source"]["units"] == "mm"
    assert data["source"]["format"].startswith("DXF")


def test_microscan_svs_is_registered_separately_from_lt_blower() -> None:
    data = json.loads(CATALOGUE.read_text(encoding="utf-8"))
    families = {component["family"] for component in data["components"]}
    assert {"LT", "SVS"} <= families
    svs = next(component for component in data["components"] if component["family"] == "SVS")
    assert svs["status"] == "approved"
    assert svs["model"] == "SVS-I/LT6-I"
