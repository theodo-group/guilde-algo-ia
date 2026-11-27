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
    StaticSite(template, out, libraries={}).publish([PROJECT])
    assert (out / "index.html").read_text() == "<html></html>"
    assert json.loads((out / "projects.json").read_text()) == [{
        "theme": "ia", "sujet": "mlx", "projet": "mlx-vs-pytorch", "path": "ia/mlx/mlx-vs-pytorch",
        "titre": "MLX", "auteurs": ["Vlor999"], "description": "Compare.", "date": "2026-03-11",
        "session": "https://n.so/x", "stack": ["python"],
    }]


def test_rebuild_replaces_previous_build(tmp_path, template):
    out = tmp_path / "site"
    StaticSite(template, out, libraries={}).publish([PROJECT])
    (out / "stale.txt").write_text("old")
    StaticSite(template, out, libraries={}).publish([])
    assert not (out / "stale.txt").exists()
    assert json.loads((out / "projects.json").read_text()) == []


@pytest.fixture
def library(tmp_path):
    """An installed npm library: its ES module and its licence."""
    folder = tmp_path / "node_modules" / "lib"
    (folder / "dist").mkdir(parents=True)
    (folder / "dist" / "lib.es.js").write_text("export {};")
    (folder / "license.txt").write_text("BSD")
    return {"vendor/lib/lib.es.js": folder / "dist" / "lib.es.js", "vendor/lib/LICENSE": folder / "license.txt"}


def test_copies_the_libraries_into_the_site(tmp_path, template, library):
    out = tmp_path / "site"
    StaticSite(template, out, libraries=library).publish([])
    assert (out / "vendor" / "lib" / "lib.es.js").read_text() == "export {};"
    assert (out / "vendor" / "lib" / "LICENSE").read_text() == "BSD"


def test_missing_library_keeps_the_previous_build(tmp_path, template, library):
    out = tmp_path / "site"
    StaticSite(template, out, libraries=library).publish([PROJECT])
    library["vendor/lib/lib.es.js"].unlink()
    with pytest.raises(SiteUnwritable, match="run `npm ci` in .github/project-index"):
        StaticSite(template, out, libraries=library).publish([])
    assert len(json.loads((out / "projects.json").read_text())) == 1
    assert (out / "vendor" / "lib" / "lib.es.js").exists()


def test_empty_existing_folder_is_used(tmp_path, template):
    out = tmp_path / "site"
    out.mkdir()
    StaticSite(template, out, libraries={}).publish([])
    assert (out / "index.html").exists()


def test_refuses_a_folder_it_did_not_build(tmp_path, template):
    out = tmp_path / "repo"
    out.mkdir()
    (out / "precious.txt").write_text("keep me")
    with pytest.raises(SiteUnwritable, match="not built by project_index"):
        StaticSite(template, out, libraries={}).publish([])
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
        StaticSite(template, out, libraries={}).publish([PROJECT])
    StaticSite(template, out, libraries={}).publish([PROJECT])
    assert (out / "index.html").read_text() == "<html></html>"


@needs_permissions
def test_rerun_after_clearing_failed_halfway(tmp_path, template):
    out = tmp_path / "site"
    StaticSite(template, out, libraries={}).publish([PROJECT])
    locked = out / "vendor"
    locked.mkdir()
    (locked / "lib.js").write_text("x")
    with mode(locked, 0o500), pytest.raises(SiteUnwritable):
        StaticSite(template, out, libraries={}).publish([])
    StaticSite(template, out, libraries={}).publish([])
    assert json.loads((out / "projects.json").read_text()) == []
    assert not locked.exists()


@needs_permissions
def test_unsearchable_parent_is_unwritable(tmp_path, template):
    parent = tmp_path / "parent"
    parent.mkdir()
    with mode(parent, 0o000), pytest.raises(SiteUnwritable):
        StaticSite(template, parent / "site", libraries={}).publish([])


def test_refuses_a_dangling_symlink(tmp_path, template):
    link = tmp_path / "link"
    link.symlink_to(tmp_path / "missing")
    with pytest.raises(SiteUnwritable, match="is a symbolic link"):
        StaticSite(template, link, libraries={}).publish([])


def test_refuses_a_symlink(tmp_path, template):
    target = tmp_path / "target"
    target.mkdir()
    link = tmp_path / "link"
    link.symlink_to(target)
    with pytest.raises(SiteUnwritable, match="is a symbolic link"):
        StaticSite(template, link, libraries={}).publish([])


def test_refuses_a_file(tmp_path, template):
    out = tmp_path / "file"
    out.write_text("x")
    with pytest.raises(SiteUnwritable, match="not a folder"):
        StaticSite(template, out, libraries={}).publish([])


def test_rebuild_with_libraries_replaces_them(tmp_path, template, library):
    out = tmp_path / "site"
    StaticSite(template, out, libraries=library).publish([])
    (out / "vendor" / "lib" / "stale.js").write_text("old")
    StaticSite(template, out, libraries=library).publish([])
    assert sorted(p.name for p in (out / "vendor" / "lib").iterdir()) == ["LICENSE", "lib.es.js"]


@needs_permissions
def test_rerun_after_the_library_copy_failed(tmp_path, template, library):
    out = tmp_path / "site"
    source = library["vendor/lib/lib.es.js"]
    with mode(source, 0o000), pytest.raises(SiteUnwritable):
        StaticSite(template, out, libraries=library).publish([])
    StaticSite(template, out, libraries=library).publish([])
    assert (out / "vendor" / "lib" / "lib.es.js").read_text() == "export {};"
