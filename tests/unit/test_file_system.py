import pytest
import os
import sys
from pathlib import Path
import shutil

# Add the project root to sys.path for src-based imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from src.tools import file_system

PROJECT_ROOT = Path(file_system.PROJECT_ROOT_DIR)
TMP_BASE_DIR = PROJECT_ROOT / 'tmp_tests'


def _make_test_path(tmp_path_factory, name: str) -> Path:
    """Return an absolute path inside PROJECT_ROOT for safe testing."""
    test_dir = TMP_BASE_DIR / tmp_path_factory.mktemp('fs').name
    test_dir.mkdir(parents=True, exist_ok=True)
    return test_dir / name


def teardown_module(module):  # noqa: D401, N802
    """Remove tmp_tests directory after all tests in this module run."""
    if TMP_BASE_DIR.exists():
        shutil.rmtree(TMP_BASE_DIR)


def test_resolve_path_blocks_escape():
    # Should raise ValueError for path traversal
    with pytest.raises(ValueError):
        file_system._resolve_path('../hack.txt')


def test_read_file_content_text(tmp_path_factory):
    file_path = _make_test_path(tmp_path_factory, 'foo.txt')
    file_path.write_text('hello world')
    content = file_system.read_file_content(str(file_path))
    assert 'hello world' in content


def test_read_file_content_binary(tmp_path_factory):
    file_path = _make_test_path(tmp_path_factory, 'foo.bin')
    # Write bytes that are invalid UTF-8 so decoding fails
    file_path.write_bytes(b'\xff\xfe\xfa\xfa')
    with pytest.raises(ValueError):
        file_system.read_file_content(str(file_path))


def test_list_directory_contents(tmp_path_factory):
    base_dir = _make_test_path(tmp_path_factory, 'dummy').parent  # create dir
    (base_dir / 'a.txt').write_text('a')
    (base_dir / 'b.txt').write_text('b')
    (base_dir / 'subdir').mkdir()
    listing = file_system.list_directory_contents(str(base_dir))
    assert '📁 subdir/' in listing
    assert '📄 a.txt' in listing
    assert '📄 b.txt' in listing


def test_write_content_to_file(tmp_path_factory):
    file_path = _make_test_path(tmp_path_factory, 'bar.txt')
    bytes_written = file_system.write_content_to_file(str(file_path), 'abc')
    assert bytes_written == 3
    assert file_path.read_text() == 'abc'


def test_write_content_to_file_overwrite(tmp_path_factory):
    file_path = _make_test_path(tmp_path_factory, 'baz.txt')
    file_path.write_text('old')
    bytes_written = file_system.write_content_to_file(str(file_path), 'new')
    assert bytes_written == 3
    assert file_path.read_text() == 'new'


def test_read_file_content_truncation(tmp_path_factory):
    file_path = _make_test_path(tmp_path_factory, 'big.txt')
    file_path.write_text('a' * 300)
    content = file_system.read_file_content(str(file_path), max_bytes=100, max_lines=10)
    assert '[...content truncated...]' in content 