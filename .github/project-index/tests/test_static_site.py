import datetime as dt
import json
import os
from contextlib import contextmanager

import pytest

from project_index.adapters.static_site import StaticSite
from project_index.metadata import IndexedProject, ProjectMetadata, ProjectPath
from project_index.ports import SiteUnwritable

PROJECT = IndexedProject(
    ProjectPath("ia", "mlx", "mlx-vs-pytorch"),
    ProjectMetadata("MLX", ("Vlor999",), "Compare.", dt.date(2026, 3, 11), "https://n.so/x", ("python",)),
)


@pytest.fixture
def template(tmp_path):
    folder = tmp_path / "template"
    folder.mkdir()
    (folder / "index.html").write_text("<html></html>")
    return folder


def test_writes_page_and_projects(tmp_path, template):
    out = tmp_path / "site"
    StaticSite(template, out).publish([PROJECT])
    assert (out / "index.html").read_text() == "<html></html>"
    assert json.loads((out / "projects.json").read_text()) == [{
        "theme": "ia", "sujet": "mlx", "projet": "mlx-vs-pytorch", "path": "ia/mlx/mlx-vs-pytorch",
        "titre": "MLX", "auteurs": ["Vlor999"], "description": "Compare.", "date": "2026-03-11",
        "session": "https://n.so/x", "stack": ["python"],
    }]


def test_rebuild_replaces_previous_build(tmp_path, template):
    out = tmp_path / "site"
    StaticSite(template, out).publish([PROJECT])
    (out / "stale.txt").write_text("old")
    StaticSite(template, out).publish([])
    assert not (out / "stale.txt").exists()
    assert json.loads((out / "projects.json").read_text()) == []


def test_empty_existing_folder_is_used(tmp_path, template):
    out = tmp_path / "site"
    out.mkdir()
    StaticSite(template, out).publish([])
    assert (out / "index.html").exists()


def test_refuses_a_folder_it_did_not_build(tmp_path, template):
    out = tmp_path / "repo"
    out.mkdir()
    (out / "precious.txt").write_text("keep me")
    with pytest.raises(SiteUnwritable, match="not built by project_index"):
        StaticSite(template, out).publish([])
    assert (out / "precious.txt").read_text() == "keep me"


needs_permissions = pytest.mark.skipif(os.geteuid() == 0, reason="root ignores file permissions")


@contextmanager
def mode(path, value):
    """Set the permission bits of a path for the duration of a block."""
    previous = path.stat().st_mode
    path.chmod(value)
    try:
        yield
    finally:
        path.chmod(previous)


@needs_permissions
def test_rerun_after_a_failure_halfway(tmp_path, template):
    unreadable = template / "z-unreadable.js"
    unreadable.write_text("x")
    out = tmp_path / "site"
    with mode(unreadable, 0o000), pytest.raises(SiteUnwritable):
        StaticSite(template, out).publish([PROJECT])
    StaticSite(template, out).publish([PROJECT])
    assert (out / "index.html").read_text() == "<html></html>"


@needs_permissions
def test_rerun_after_clearing_failed_halfway(tmp_path, template):
    out = tmp_path / "site"
    StaticSite(template, out).publish([PROJECT])
    locked = out / "vendor"
    locked.mkdir()
    (locked / "lib.js").write_text("x")
    with mode(locked, 0o500), pytest.raises(SiteUnwritable):
        StaticSite(template, out).publish([])
    StaticSite(template, out).publish([])
    assert json.loads((out / "projects.json").read_text()) == []
    assert not locked.exists()


@needs_permissions
def test_unsearchable_parent_is_unwritable(tmp_path, template):
    parent = tmp_path / "parent"
    parent.mkdir()
    with mode(parent, 0o000), pytest.raises(SiteUnwritable):
        StaticSite(template, parent / "site").publish([])


def test_refuses_a_dangling_symlink(tmp_path, template):
    link = tmp_path / "link"
    link.symlink_to(tmp_path / "missing")
    with pytest.raises(SiteUnwritable, match="is a symbolic link"):
        StaticSite(template, link).publish([])


def test_refuses_a_symlink(tmp_path, template):
    target = tmp_path / "target"
    target.mkdir()
    link = tmp_path / "link"
    link.symlink_to(target)
    with pytest.raises(SiteUnwritable, match="is a symbolic link"):
        StaticSite(template, link).publish([])


def test_refuses_a_file(tmp_path, template):
    out = tmp_path / "file"
    out.write_text("x")
    with pytest.raises(SiteUnwritable, match="not a folder"):
        StaticSite(template, out).publish([])
