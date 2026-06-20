import json
from pathlib import Path

from fastapi.testclient import TestClient

from ermi.api import create_app


def test_open_folder_rejects_paths_outside_root(tmp_path: Path) -> None:
    root = tmp_path / "archive"
    root.mkdir()
    app = create_app(root)
    client = TestClient(app)

    # Check that a valid path works
    valid_path = root / "some_folder"
    response = client.post("/api/open-folder", json={"path": str(valid_path)})
    assert response.status_code == 200

    # Check that a path outside root is rejected
    invalid_path = tmp_path / "outside_folder"
    response = client.post("/api/open-folder", json={"path": str(invalid_path)})
    assert response.status_code == 400
    assert "Path must be within the archive root" in response.json()["detail"]
