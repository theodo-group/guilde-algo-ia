"""Writes the index as a static site: the page template, its npm libraries and a JSON file of the projects."""

import json
import shutil
from collections.abc import Mapping
from pathlib import Path

from project_index.constants import LIBRARY_INSTALL_HINT, SITE_DATA_FILE, SITE_MARKER_FILE
from project_index.metadata import IndexedProject
from project_index.ports import SiteUnwritable


def project_record(project: IndexedProject) -> dict[str, object]:
    """Return the JSON record the page reads for one project."""
    meta = project.metadata
    return {
        "theme": project.path.theme,
        "sujet": project.path.sujet,
        "projet": project.path.projet,
        "path": str(project.path),
        "titre": meta.titre,
        "auteurs": list(meta.auteurs),
        "description": meta.description,
        "date": meta.date.isoformat() if meta.date else None,
        "session": meta.session,
        "stack": list(meta.stack),
    }


class StaticSite:
    """A site folder built from a page template folder and the installed libraries the page imports.

    The folder is replaced at each build. To keep a wrong path from deleting real files,
    an existing folder is only replaced when it is empty or carries the marker that every
    build writes first and never removes.
    """

    def __init__(
        self, template_dir: Path, out_dir: Path, *, libraries: Mapping[str, Path]
    ) -> None:
        """Take the template, the output folder and the libraries to copy, as site path -> installed file."""
        self.template_dir = template_dir
        self.out_dir = out_dir
        self.libraries = dict(libraries)

    def publish(self, projects: list[IndexedProject]) -> None:
        """Write the page and the JSON of the given projects. Raises SiteUnwritable."""
        try:
            self._refuse_missing_libraries()
            self._refuse_foreign_folder()
            self.out_dir.mkdir(parents=True, exist_ok=True)
            (self.out_dir / SITE_MARKER_FILE).touch()
            self._remove_previous_files()
            shutil.copytree(self.template_dir, self.out_dir, dirs_exist_ok=True)
            self._copy_libraries()
            data = json.dumps([project_record(p) for p in projects], ensure_ascii=False, indent=2)
            (self.out_dir / SITE_DATA_FILE).write_text(data, encoding="utf-8")
        except OSError as error:
            raise SiteUnwritable(f"cannot write the site to {self.out_dir}: {error}") from error

    def _refuse_missing_libraries(self) -> None:
        """Refuse before touching the folder when a library is not installed, so the last build stays."""
        missing = [str(source) for source in self.libraries.values() if not source.is_file()]
        if missing:
            raise SiteUnwritable(f"library files missing ({', '.join(missing)}): {LIBRARY_INSTALL_HINT}")

    def _copy_libraries(self) -> None:
        """Copy each installed library file to its path in the site."""
        for site_path, source in self.libraries.items():
            target = self.out_dir / site_path
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)

    def _remove_previous_files(self) -> None:
        """Remove everything an earlier build wrote except the marker, so a failure here can be retried."""
        for entry in self.out_dir.iterdir():
            if entry.name == SITE_MARKER_FILE:
                continue
            if entry.is_dir() and not entry.is_symlink():
                shutil.rmtree(entry)
            else:
                entry.unlink()

    def _refuse_foreign_folder(self) -> None:
        """Refuse a link, a file, or a non-empty folder without the marker. Lets OSError through to publish."""
        if self.out_dir.is_symlink():
            raise SiteUnwritable(f"{self.out_dir} is a symbolic link: give the real folder")
        if not self.out_dir.exists():
            return
        if not self.out_dir.is_dir():
            raise SiteUnwritable(f"{self.out_dir} exists and is not a folder")
        if not (self.out_dir / SITE_MARKER_FILE).exists() and any(self.out_dir.iterdir()):
            raise SiteUnwritable(
                f"{self.out_dir} is not empty and was not built by project_index: choose an empty or new folder"
            )
