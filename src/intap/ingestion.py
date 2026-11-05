"""Read bounded Python source files without importing or executing them."""

from __future__ import annotations

import ast
import hashlib
import io
import os
import tokenize
from dataclasses import dataclass
from pathlib import Path

from intap.config import Config


@dataclass(frozen=True)
class SourceFile:
    path: str
    sha256: str
    tree: ast.Module


def collect_sources(config: Config) -> tuple[list[SourceFile], list[dict[str, str]]]:
    root = config.source_root.resolve()
    if not root.is_dir():
        raise ValueError(f"Source root is not a directory: {root}")
    sources: list[SourceFile] = []
    skipped: list[dict[str, str]] = []
    candidates = 0

    def walk_error(error: OSError) -> None:
        raise error

    for directory, dirs, names in os.walk(root, followlinks=False, onerror=walk_error):
        dirs[:] = sorted(
            name for name in dirs
            if not name.startswith(".")
            and name not in config.exclude_dirs
            and not (Path(directory) / name).is_symlink()
        )
        for name in sorted(names):
            if name.startswith(".") or not name.endswith(".py"):
                continue
            candidates += 1
            if candidates > config.max_files:
                raise ValueError(f"Source exceeds the {config.max_files} Python file limit")
            path = Path(directory) / name
            relative = path.relative_to(root).as_posix()
            if path.is_symlink():
                skipped.append({"path": relative, "reason": "symlink"})
                continue
            if not path.is_file():
                skipped.append({"path": relative, "reason": "not a regular file"})
                continue
            # Bounded read also covers files that grow after discovery.
            with path.open("rb") as handle:
                raw = handle.read(config.max_file_bytes + 1)
            if len(raw) > config.max_file_bytes:
                skipped.append({"path": relative, "reason": "file size limit"})
                continue
            try:
                encoding, _ = tokenize.detect_encoding(io.BytesIO(raw).readline)
                tree = ast.parse(raw.decode(encoding), filename=relative)
            except (SyntaxError, UnicodeError, LookupError, ValueError, RecursionError):
                skipped.append({"path": relative, "reason": "unparseable Python"})
                continue
            sources.append(SourceFile(relative, hashlib.sha256(raw).hexdigest(), tree))
    return sorted(sources, key=lambda source: source.path), skipped
