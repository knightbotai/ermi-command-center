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


def test_ingest_rejects_paths_outside_allowed_directories(tmp_path: Path) -> None:
    root = tmp_path / "archive"
    root.mkdir()

    # Write a dummy setup.json to simulate an allowed source directory
    setup_file = root / "setup.json"
    allowed_source_dir = tmp_path / "allowed_source"
    allowed_source_dir.mkdir()
    setup_file.write_text(
        json.dumps({"chatgpt_source": str(allowed_source_dir / "conversations.json")}),
        encoding="utf-8",
    )

    app = create_app(root)
    client = TestClient(app)

    # Valid path inside root
    valid_path_root = root / "some_export.json"
    valid_path_root.touch()
    response = client.post("/api/ingest", json={"source": str(valid_path_root)})
    assert response.status_code != 403

    # Valid path inside allowed chatgpt_source parent dir
    valid_path_allowed = allowed_source_dir / "conversations.json"
    valid_path_allowed.touch()
    response = client.post("/api/ingest", json={"source": str(valid_path_allowed)})
    assert response.status_code != 403

    # Invalid path outside root and allowed directories
    invalid_path = tmp_path / "outside_folder" / "secrets.txt"
    invalid_path.parent.mkdir()
    invalid_path.touch()

    response = client.post("/api/ingest", json={"source": str(invalid_path)})
    assert response.status_code == 403
    assert "Source path is not within an allowed directory" in response.json()["detail"]

def test_export_chatgpt_csv_rejects_paths_outside_allowed_directories(tmp_path: Path) -> None:
    root = tmp_path / "archive"
    root.mkdir()

    # Write a dummy setup.json
    setup_file = root / "setup.json"
    allowed_source_dir = tmp_path / "allowed_source"
    allowed_source_dir.mkdir()
    setup_file.write_text(
        json.dumps({"chatgpt_source": str(allowed_source_dir / "conversations.json")}),
        encoding="utf-8",
    )

    app = create_app(root)
    client = TestClient(app)

    # Valid source and target inside allowed dir
    valid_source = allowed_source_dir / "conversations.json"
    valid_source.touch()
    valid_target = root / "exports" / "chat_history.csv"
    valid_target.parent.mkdir(parents=True)

    # We expect 400 because export_chat_csv fails on dummy file (not json), but NOT 403.
    response = client.post("/api/export/chatgpt-csv", json={"source": str(valid_source), "target": str(valid_target)})
    assert response.status_code != 403

    # Invalid source outside
    invalid_source = tmp_path / "outside_source" / "conversations.json"
    invalid_source.parent.mkdir(exist_ok=True)
    response = client.post("/api/export/chatgpt-csv", json={"source": str(invalid_source), "target": str(valid_target)})
    assert response.status_code == 403
    assert "Source path is not within an allowed directory" in response.json()["detail"]

    # Invalid target outside (Arbitrary File Write)
    invalid_target = tmp_path / "outside_target" / "chat_history.csv"
    invalid_target.parent.mkdir(exist_ok=True)
    response = client.post("/api/export/chatgpt-csv", json={"source": str(valid_source), "target": str(invalid_target)})
    assert response.status_code == 403
    assert "Source path is not within an allowed directory" in response.json()["detail"]

def test_restore_rejects_paths_outside_allowed_directories(tmp_path: Path) -> None:
    root = tmp_path / "archive"
    root.mkdir()

    app = create_app(root)
    client = TestClient(app)

    invalid_source = tmp_path / "outside_source" / "backup.zip"
    response = client.post("/api/restore", json={"source": str(invalid_source)})
    assert response.status_code == 403
    assert "Source path is not within an allowed directory" in response.json()["detail"]
