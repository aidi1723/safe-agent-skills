from __future__ import annotations

import os
import stat
from contextlib import ExitStack, contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterator


READ_CHUNK_SIZE = 64 * 1024
_OPEN_SUPPORTS_DIR_FD = os.open in getattr(os, "supports_dir_fd", ())
_STAT_SUPPORTS_DIR_FD = os.stat in getattr(os, "supports_dir_fd", ())
_STAT_SUPPORTS_NOFOLLOW = os.stat in getattr(os, "supports_follow_symlinks", ())
_SCANDIR_SUPPORTS_FD = os.scandir in getattr(os, "supports_fd", ())


class UnsafeDescriptorAccessError(ValueError):
    """Raised when descriptor-bound filesystem access cannot be guaranteed."""


@dataclass(frozen=True)
class DirectoryEntry:
    name: str
    stat_result: os.stat_result


def require_descriptor_capabilities() -> None:
    required_flags = ("O_DIRECTORY", "O_NOFOLLOW", "O_CLOEXEC", "O_NONBLOCK")
    flags = [getattr(os, name, None) for name in required_flags]
    read_only = getattr(os, "O_RDONLY", None)
    if (
        type(read_only) is not int
        or read_only < 0
        or any(type(value) is not int or value <= 0 for value in flags)
        or not _OPEN_SUPPORTS_DIR_FD
        or not _STAT_SUPPORTS_DIR_FD
        or not _STAT_SUPPORTS_NOFOLLOW
        or not _SCANDIR_SUPPORTS_FD
        or not callable(getattr(os, "fstat", None))
        or not callable(getattr(os, "read", None))
    ):
        raise UnsafeDescriptorAccessError("descriptor-bound filesystem access is unavailable")


def directory_open_flags() -> int:
    require_descriptor_capabilities()
    return os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC


def file_open_flags() -> int:
    require_descriptor_capabilities()
    return os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC


def safe_component(name: object) -> str:
    if (
        not isinstance(name, str)
        or not name
        or name in {".", ".."}
        or "/" in name
        or "\0" in name
    ):
        raise UnsafeDescriptorAccessError("unsafe filesystem component")
    return name


def same_object(left: os.stat_result, right: os.stat_result) -> bool:
    return (left.st_dev, left.st_ino) == (right.st_dev, right.st_ino)


def same_state(left: os.stat_result, right: os.stat_result) -> bool:
    return same_object(left, right) and (
        left.st_size,
        left.st_mtime_ns,
        left.st_ctime_ns,
    ) == (
        right.st_size,
        right.st_mtime_ns,
        right.st_ctime_ns,
    )


def named_stat(parent_fd: int, name: str) -> os.stat_result:
    safe_component(name)
    return os.stat(name, dir_fd=parent_fd, follow_symlinks=False)


@contextmanager
def open_root(path: Path, *, missing_ok: bool = False) -> Iterator[int | None]:
    try:
        fd = os.open(path, directory_open_flags())
    except FileNotFoundError as exc:
        if missing_ok:
            yield None
            return
        raise UnsafeDescriptorAccessError("descriptor root is missing") from exc
    except (OSError, TypeError, ValueError) as exc:
        raise UnsafeDescriptorAccessError("descriptor root is unsafe") from exc
    try:
        opened = os.fstat(fd)
        if not stat.S_ISDIR(opened.st_mode):
            raise UnsafeDescriptorAccessError("descriptor root is not a directory")
        yield fd
        finished = os.fstat(fd)
        current = os.stat(path, follow_symlinks=False)
        if (
            not stat.S_ISDIR(current.st_mode)
            or not same_state(opened, finished)
            or not same_object(finished, current)
        ):
            raise UnsafeDescriptorAccessError("descriptor root changed during access")
    except UnsafeDescriptorAccessError:
        raise
    except (OSError, TypeError, ValueError) as exc:
        raise UnsafeDescriptorAccessError("descriptor root access failed") from exc
    finally:
        os.close(fd)


@contextmanager
def open_directory_at(
    parent_fd: int,
    name: str,
    expected: os.stat_result | None = None,
) -> Iterator[int]:
    name = safe_component(name)
    try:
        expected = expected if expected is not None else named_stat(parent_fd, name)
        if not stat.S_ISDIR(expected.st_mode):
            raise UnsafeDescriptorAccessError("expected directory is unsafe")
        fd = os.open(name, directory_open_flags(), dir_fd=parent_fd)
    except UnsafeDescriptorAccessError:
        raise
    except (OSError, TypeError, ValueError) as exc:
        raise UnsafeDescriptorAccessError("directory open failed") from exc
    try:
        opened = os.fstat(fd)
        current = named_stat(parent_fd, name)
        if (
            not stat.S_ISDIR(opened.st_mode)
            or not stat.S_ISDIR(current.st_mode)
            or not same_object(expected, opened)
            or not same_object(opened, current)
        ):
            raise UnsafeDescriptorAccessError("directory changed before access")
        yield fd
        finished = os.fstat(fd)
        current = named_stat(parent_fd, name)
        if (
            not stat.S_ISDIR(current.st_mode)
            or not same_state(opened, finished)
            or not same_object(finished, current)
        ):
            raise UnsafeDescriptorAccessError("directory changed during access")
    except UnsafeDescriptorAccessError:
        raise
    except (OSError, TypeError, ValueError) as exc:
        raise UnsafeDescriptorAccessError("directory access failed") from exc
    finally:
        os.close(fd)


def directory_entries(directory_fd: int) -> tuple[DirectoryEntry, ...]:
    require_descriptor_capabilities()
    try:
        with os.scandir(directory_fd) as scanner:
            names = [safe_component(entry.name) for entry in scanner]
        entries = [DirectoryEntry(name, named_stat(directory_fd, name)) for name in names]
    except UnsafeDescriptorAccessError:
        raise
    except (OSError, TypeError, ValueError) as exc:
        raise UnsafeDescriptorAccessError("directory enumeration failed") from exc
    return tuple(sorted(entries, key=lambda entry: entry.name))


def iter_fd_chunks(fd: int) -> Iterator[bytes]:
    while True:
        chunk = os.read(fd, READ_CHUNK_SIZE)
        if not chunk:
            return
        yield chunk


def visit_regular_file(
    parent_fd: int,
    name: str,
    visitor: Callable[[int], None],
    expected: os.stat_result | None = None,
) -> None:
    name = safe_component(name)
    try:
        expected = expected if expected is not None else named_stat(parent_fd, name)
        if not stat.S_ISREG(expected.st_mode):
            raise UnsafeDescriptorAccessError("expected file is unsafe")
        fd = os.open(name, file_open_flags(), dir_fd=parent_fd)
    except UnsafeDescriptorAccessError:
        raise
    except (OSError, TypeError, ValueError) as exc:
        raise UnsafeDescriptorAccessError("file open failed") from exc
    try:
        opened = os.fstat(fd)
        current = named_stat(parent_fd, name)
        if (
            not stat.S_ISREG(opened.st_mode)
            or not stat.S_ISREG(current.st_mode)
            or not same_object(expected, opened)
            or not same_object(opened, current)
        ):
            raise UnsafeDescriptorAccessError("file changed before access")
        visitor(fd)
        finished = os.fstat(fd)
        current = named_stat(parent_fd, name)
        if (
            not stat.S_ISREG(current.st_mode)
            or not same_state(opened, finished)
            or not same_object(finished, current)
        ):
            raise UnsafeDescriptorAccessError("file changed during access")
    except UnsafeDescriptorAccessError:
        raise
    except (OSError, TypeError, ValueError) as exc:
        raise UnsafeDescriptorAccessError("file access failed") from exc
    finally:
        os.close(fd)


def read_file_at(root_fd: int, components: tuple[str, ...]) -> bytes:
    if not components:
        raise UnsafeDescriptorAccessError("file path is empty")
    safe_components = tuple(safe_component(component) for component in components)
    chunks: list[bytes] = []
    with ExitStack() as stack:
        parent_fd = root_fd
        for component in safe_components[:-1]:
            parent_fd = stack.enter_context(open_directory_at(parent_fd, component))
        visit_regular_file(
            parent_fd,
            safe_components[-1],
            lambda fd: chunks.extend(iter_fd_chunks(fd)),
        )
    return b"".join(chunks)


def visit_regular_tree(
    root_fd: int,
    roots: tuple[str, ...],
    visitor: Callable[[str, int], None],
) -> int:
    count = 0

    def walk(directory_fd: int, components: tuple[str, ...]) -> None:
        nonlocal count
        entries = directory_entries(directory_fd)
        ordered = sorted(
            entries,
            key=lambda entry: entry.name + ("/" if stat.S_ISDIR(entry.stat_result.st_mode) else ""),
        )
        for entry in ordered:
            relative_components = (*components, entry.name)
            if stat.S_ISDIR(entry.stat_result.st_mode):
                with open_directory_at(directory_fd, entry.name, entry.stat_result) as child_fd:
                    walk(child_fd, relative_components)
            elif stat.S_ISREG(entry.stat_result.st_mode):
                relative_path = "/".join(relative_components)
                visit_regular_file(
                    directory_fd,
                    entry.name,
                    lambda fd, path=relative_path: visitor(path, fd),
                    entry.stat_result,
                )
                count += 1
            else:
                raise UnsafeDescriptorAccessError("special filesystem entry is unsafe")

    root_entries = {entry.name: entry for entry in directory_entries(root_fd)}
    for root_name in sorted(safe_component(root) for root in roots):
        entry = root_entries.get(root_name)
        if entry is None:
            continue
        if not stat.S_ISDIR(entry.stat_result.st_mode):
            raise UnsafeDescriptorAccessError("auxiliary root is unsafe")
        with open_directory_at(root_fd, root_name, entry.stat_result) as directory_fd:
            walk(directory_fd, (root_name,))
    return count
