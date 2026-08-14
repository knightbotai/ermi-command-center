import pytest
from pathlib import Path
from unittest.mock import patch
import sqlite3

from ermi.ops import backup_archive, restore_archive, known_folder, open_folder

def test_backup_archive(tmp_path: Path):
    root = tmp_path / "archive"
    root.mkdir()

    # Create real sqlite db
    db_path = root / "ermi.sqlite3"
    conn = sqlite3.connect(db_path)
    conn.execute("CREATE TABLE test (id int);")
    conn.commit()
    conn.close()

    # Create other dummy files
    for name in ("graph.json", "watchers.json", "watch_state.json"):
        (root / name).write_text(f"dummy content {name}")

    # Create dummy folders
    for folder in ("raw", "vault"):
        (root / folder).mkdir()
        (root / folder / f"{folder}_file.txt").write_text(f"dummy {folder}")

    # Run backup
    target = tmp_path / "my_backup"
    backup_path = backup_archive(root, target)

    assert backup_path == target
    assert backup_path.exists()

    for name in ("ermi.sqlite3", "graph.json", "watchers.json", "watch_state.json", "CHANGELOG.md"):
        assert (backup_path / name).exists()
        if name not in ("ermi.sqlite3", "CHANGELOG.md"):
            assert (backup_path / name).read_text() == f"dummy content {name}"
        elif name == "CHANGELOG.md":
            assert (backup_path / name).read_text() == Path("CHANGELOG.md").read_text()

    for folder in ("raw", "vault"):
        assert (backup_path / folder / f"{folder}_file.txt").exists()

def test_restore_archive(tmp_path: Path):
    source = tmp_path / "backup"
    source.mkdir()

    # Create real sqlite db in backup
    db_path = source / "ermi.sqlite3"
    conn = sqlite3.connect(db_path)
    conn.execute("CREATE TABLE restored_test (id int);")
    conn.commit()
    conn.close()

    for name in ("graph.json", "watchers.json", "watch_state.json"):
        (source / name).write_text(f"backed up {name}")

    for folder in ("raw", "vault"):
        (source / folder).mkdir()
        (source / folder / f"{folder}_file.txt").write_text(f"backed up {folder}")

    root = tmp_path / "restored_archive"
    root.mkdir()

    restore_path = restore_archive(root, source)

    assert restore_path == root

    # Verify db was restored correctly
    restored_db_path = root / "ermi.sqlite3"
    assert restored_db_path.exists()
    conn = sqlite3.connect(restored_db_path)
    # Check our table is there to ensure it's the restored db, not the newly initialized one
    cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='restored_test';")
    assert cursor.fetchone() is not None
    conn.close()

    for name in ("graph.json", "watchers.json", "watch_state.json"):
        assert (root / name).exists()
        assert (root / name).read_text() == f"backed up {name}"

    for folder in ("raw", "vault"):
        assert (root / folder / f"{folder}_file.txt").exists()

def test_restore_archive_not_found(tmp_path: Path):
    with pytest.raises(FileNotFoundError):
        restore_archive(tmp_path / "archive", tmp_path / "non_existent")

def test_known_folder(tmp_path: Path):
    root = tmp_path / "archive"
    assert known_folder(root, "archive") == root.resolve()
    assert known_folder(root, "raw") == (root / "raw").resolve()
    assert known_folder(root, "vault") == (root / "vault").resolve()
    assert known_folder(root, "backups") == (root / "backups").resolve()
    assert known_folder(root, "exports") == (root / "exports").resolve()
    assert known_folder(root, "samples") == Path("sample_data").resolve()

    with pytest.raises(ValueError):
        known_folder(root, "unknown")

@patch("subprocess.Popen")
@patch("sys.platform", "win32")
def test_open_folder_win32(mock_popen, tmp_path: Path):
    root = tmp_path / "archive"
    target = open_folder(root, "raw")
    mock_popen.assert_called_once_with(["explorer", str(target)])

@patch("subprocess.Popen")
@patch("sys.platform", "darwin")
def test_open_folder_darwin(mock_popen, tmp_path: Path):
    root = tmp_path / "archive"
    target = open_folder(root, "vault")
    mock_popen.assert_called_once_with(["open", str(target)])

@patch("subprocess.Popen")
@patch("sys.platform", "linux")
def test_open_folder_linux(mock_popen, tmp_path: Path):
    root = tmp_path / "archive"
    target = open_folder(root, "backups")
    mock_popen.assert_called_once_with(["xdg-open", str(target)])
