"""T26: the pid-namespace hole in `DirectoryLock`, reproduced and closed.

`docs/DEPLOYMENT.md` section 9 carried this as `[inference, unreproduced]` for
eleven releases, with a note that it must not become a threat-model row on the
strength of reasoning alone. It was reproduced on 2026-09-10 and the reasoning
was right: a holder at pid 483 in the host namespace, a second process under
`unshare --pid --fork` against the same directory, `os.kill(483, 0)` raising
`ProcessLookupError` because that namespace has no pid 483, and the second
process taking the lock as stale.

**The first test below is the one that matters, and it needs no namespaces.**
The defect was never really about containers: it was that liveness of a number
written in a file was the whole exclusion, and any process can write that file.
Pin that and the container case follows. The namespace test is kept because the
entry asked for the literal reproduction, and it skips where `unshare` cannot
run - on a laptop, and in any CI without the capability - which is why it is
not the load-bearing one.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from mavo.backfill import DirectoryBusy, DirectoryLock

CHILD = r'''
import pathlib, sys
sys.path.insert(0, sys.argv[2])
from mavo.backfill import DirectoryLock, DirectoryBusy
try:
    DirectoryLock(pathlib.Path(sys.argv[1])).acquire()
    print("TOOK")
except DirectoryBusy:
    print("REFUSED")
'''


def test_a_dead_pid_in_the_file_does_not_release_a_held_lock(tmp_path: Path) -> None:
    """The red direction, and it is red against every implementation before this.

    The holder is live and holds the descriptor. The *contents* of the lock file
    then say a pid that does not exist - which is what a second pid namespace
    makes true without anybody writing anything. The old implementation read
    that number, tested it with `os.kill`, found it dead and took the lock. The
    lock is now the kernel's, so the number is a label and changing it changes
    nothing.
    """
    held = DirectoryLock(tmp_path)
    held.acquire()
    (tmp_path / ".backfill.lock").write_text("999999", encoding="utf-8")
    with pytest.raises(DirectoryBusy):
        DirectoryLock(tmp_path).acquire()
    held.release()


def test_the_lock_is_free_once_the_holder_releases_it(tmp_path: Path) -> None:
    """Exclusion that never lets go is a lock file people delete by reflex."""
    first = DirectoryLock(tmp_path)
    first.acquire()
    first.release()
    second = DirectoryLock(tmp_path)
    second.acquire()
    assert (tmp_path / ".backfill.lock").read_text(encoding="utf-8") == str(os.getpid())
    second.release()


def test_a_holder_that_dies_does_not_leave_a_lock_behind(tmp_path: Path) -> None:
    """No takeover rule is needed, because the kernel drops the descriptor.

    The previous implementation needed one - a dead pid had to be detected and
    the lock reclaimed - and that rule was the hole. A child process takes the
    lock and is killed; the parent then acquires without any liveness test
    existing anywhere in the module.
    """
    holder = subprocess.Popen(
        [sys.executable, "-c",
         "import pathlib, sys, time\n"
         "sys.path.insert(0, sys.argv[2])\n"
         "from mavo.backfill import DirectoryLock\n"
         "DirectoryLock(pathlib.Path(sys.argv[1])).acquire()\n"
         "print('held', flush=True)\n"
         "time.sleep(30)\n",
         str(tmp_path), str(Path(__file__).resolve().parent.parent)],
        stdout=subprocess.PIPE, text=True)
    assert holder.stdout is not None
    assert holder.stdout.readline().strip() == "held"
    with pytest.raises(DirectoryBusy):
        DirectoryLock(tmp_path).acquire()
    holder.kill()
    holder.wait(timeout=10)
    holder.stdout.close()
    survivor = DirectoryLock(tmp_path)
    survivor.acquire()
    survivor.release()


def test_no_liveness_test_survives_in_the_module() -> None:
    """The heuristic is gone rather than merely unused.

    A dead `_alive` left in place is an invitation to call it again, and this
    defect was a call to it.
    """
    source = (Path(__file__).resolve().parent.parent / "mavo" / "backfill.py")
    text = source.read_text(encoding="utf-8")
    body = text.split('"""', 2)[-1] if text.count('"""') >= 2 else text
    assert "_alive" not in body
    assert "def _alive" not in text
    # `os.kill` may survive in the docstring that records why it was removed;
    # what must not survive is a call to it.
    assert "os.kill(" not in text.replace("`os.kill(483, 0)`", "")


@pytest.mark.skipif(shutil.which("unshare") is None,
                    reason="pid namespaces need `unshare`; absent on macOS and "
                           "on CI runners without the capability")
def test_a_second_pid_namespace_cannot_take_the_lock(tmp_path: Path) -> None:
    """The literal reproduction the entry asked for, where it can run."""
    held = DirectoryLock(tmp_path)
    held.acquire()
    root = str(Path(__file__).resolve().parent.parent)
    result = subprocess.run(
        ["unshare", "--pid", "--fork", "--mount-proc",
         sys.executable, "-c", CHILD, str(tmp_path), root],
        capture_output=True, text=True)
    if result.returncode != 0:
        pytest.skip(f"unshare unavailable in this environment: {result.stderr.strip()}")
    assert "REFUSED" in result.stdout, result.stdout
    held.release()


def test_two_holders_cannot_appear_through_a_recreated_lock_file(
        tmp_path: Path) -> None:
    """F162, and it is red against the first `flock` version of this class.

    That version kept the `unlink` the pid design had needed. `flock` binds to
    an inode, not to a path, so unlinking the path while another descriptor is
    open on it splits the lock in two: the old inode keeps its lock and has no
    name, and the next `open(O_CREAT)` makes a new inode that can be locked
    independently. Two holders, each correct, each wrong about being alone.

    The sequence below is the race made deterministic rather than raced for.
    """
    import fcntl

    lock = tmp_path / ".backfill.lock"
    first = DirectoryLock(tmp_path)
    first.acquire()
    contender = os.open(lock, os.O_CREAT | os.O_RDWR, 0o644)
    try:
        first.release()
        fcntl.flock(contender, fcntl.LOCK_EX | fcntl.LOCK_NB)
        third = DirectoryLock(tmp_path)
        with pytest.raises(DirectoryBusy):
            third.acquire()
        assert os.fstat(contender).st_ino == lock.stat().st_ino, (
            "the holder's inode and the inode on disk have parted, which is "
            "the split that lets a second holder appear"
        )
    finally:
        os.close(contender)


def test_the_lock_file_survives_release_because_it_is_not_the_lock(
        tmp_path: Path) -> None:
    """Deliberate, and the opposite of what this module did before 0.54.6.0."""
    held = DirectoryLock(tmp_path)
    held.acquire()
    held.release()
    assert (tmp_path / ".backfill.lock").exists()
