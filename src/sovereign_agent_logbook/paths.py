"""Where the logbook file lives.

A fixed path is fine for one agent on one project. A server installed for a
whole machine is started by every agent host on it, so a fixed path makes
every project write into the same file. Placeholders keep projects apart:

    {project}   name of the project folder: the nearest parent of the working
                directory that holds a .git folder, else the working directory
    {cwd}       the working directory itself, as an absolute path

Example: LOGBOOK_PATH=~/logbooks/{project}.jsonl gives each project its own file.
"""

from __future__ import annotations

import os
import re
from pathlib import Path

_UNSAFE = re.compile(r"[^A-Za-z0-9._-]+")


def project_root(cwd: Path) -> Path:
    """Nearest folder at or above cwd that contains .git; cwd if there is none."""
    cwd = cwd.resolve()
    for folder in (cwd, *cwd.parents):
        if (folder / ".git").exists():
            return folder
    return cwd


def project_name(cwd: Path) -> str:
    name = _UNSAFE.sub("-", project_root(cwd).name).strip("-.")
    return name or "default"


def resolve_path(template: str, cwd: Path | None = None) -> Path:
    """Turn a path template into a concrete path. Plain paths are returned as given."""
    cwd = Path.cwd() if cwd is None else cwd
    text = template
    if "{project}" in text:
        text = text.replace("{project}", project_name(cwd))
    if "{cwd}" in text:
        text = text.replace("{cwd}", str(cwd.resolve()))
    return Path(os.path.expanduser(text))
