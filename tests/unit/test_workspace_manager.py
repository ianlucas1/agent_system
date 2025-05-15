# pytest import removed
# import os (unused)
from src.shared.workspace import WorkspaceManager


def test_temp_dir_cleanup(tmp_path, monkeypatch):
    # Redirect BASE_DIR to tmp_path for isolation
    monkeypatch.setattr(WorkspaceManager, 'BASE_DIR', tmp_path)
    with WorkspaceManager.temp_dir('AgentX') as d:
        assert d.exists()
        # create a file inside
        file_path = d / 'test.txt'
        file_path.write_text('content')
        assert file_path.read_text() == 'content'
    # after context exit, directory should be removed
    assert not d.exists()


def test_unique_temp_dirs(tmp_path, monkeypatch):
    monkeypatch.setattr(WorkspaceManager, 'BASE_DIR', tmp_path)
    with WorkspaceManager.temp_dir('AgentY') as d1, WorkspaceManager.temp_dir('AgentY') as d2:
        assert d1.exists() and d2.exists()
        assert d1 != d2
        assert str(d1) != str(d2) 