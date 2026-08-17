#!/usr/bin/env python3
"""Gate: materialy nietechniczne nie moga byc sledzone w publicznym repo.

Blokuje pliki opisujace osoby, korespondencje i plan kontaktow. Uzasadnienie
w docs/DECISIONS.md. Uruchamiany z make verify, nie recznie.

Wynik 0: czysto. Wynik 1: znaleziono sledzony plik z listy zakazanej.
Wynik 2: repo w stanie, ktorego nie da sie sprawdzic (traktowac jak porazke).

Swiadome ograniczenie: kontrola jest po nazwie sciezki, nie po tresci.
Lista wzorcow tresci (nazwiska, adresy, telefony) NIE moze mieszkac w tym
pliku, bo publikowalaby dokladnie to, co chroni. Kontrola tresci nalezy do
lokalnego hooka pre-push z plikiem wzorcow poza repozytorium.
"""

from __future__ import annotations

import fnmatch
import subprocess
import sys
from pathlib import Path

# Wzorce dopasowywane do pelnej sciezki wzgledem korzenia repo ORAZ do samej
# nazwy pliku. Dopisujac pozycje, dopisz ja rowniez do .gitignore - gate
# sprawdza spojnosc obu list.
FORBIDDEN: tuple[str, ...] = (
    "OUTREACH.md",
    "LINKEDIN-POST.md",
    "LINKEDIN-*.md",
    "CONTACTS.md",
    "HANDOVER-*.md",
    "*-PITCH.md",
    "outreach/*",
)

GITIGNORE_REQUIRED: tuple[str, ...] = FORBIDDEN


def _git(*args: str) -> str:
    result = subprocess.run(
        ("git", *args),
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)}: {result.stderr.strip()}")
    return result.stdout


def tracked_files() -> list[str]:
    out = _git("ls-files", "-z")
    return [p for p in out.split("\0") if p]


def matches(path: str) -> str | None:
    name = path.rsplit("/", 1)[-1]
    for pattern in FORBIDDEN:
        if fnmatch.fnmatch(path, pattern) or fnmatch.fnmatch(name, pattern):
            return pattern
    return None


def gitignore_gaps(root: Path) -> list[str]:
    ignore = root / ".gitignore"
    if not ignore.is_file():
        return list(GITIGNORE_REQUIRED)
    present = {
        line.strip()
        for line in ignore.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.startswith("#")
    }
    return [p for p in GITIGNORE_REQUIRED if p not in present]


def main() -> int:
    try:
        root = Path(_git("rev-parse", "--show-toplevel").strip())
        tracked = tracked_files()
    except RuntimeError as exc:
        print(f"private-artifacts: NIE DA SIE SPRAWDZIC: {exc}", file=sys.stderr)
        return 2

    if not tracked:
        print("private-artifacts: zero sledzonych plikow, stan podejrzany", file=sys.stderr)
        return 2

    hits = [(p, pat) for p in tracked for pat in [matches(p)] if pat]
    gaps = gitignore_gaps(root)

    if hits:
        print("private-artifacts: BLAD, materialy nietechniczne sa sledzone:", file=sys.stderr)
        for path, pattern in hits:
            print(f"  {path}  (wzorzec: {pattern})", file=sys.stderr)
        print(
            "Usun z indeksu bez kasowania z dysku: git rm --cached <plik>\n"
            "Jesli plik byl juz wypchniety, historia nadal go niesie - "
            "sama zmiana HEAD nie wystarczy.",
            file=sys.stderr,
        )
        return 1

    if gaps:
        print("private-artifacts: BLAD, .gitignore nie pokrywa wzorcow:", file=sys.stderr)
        for pattern in gaps:
            print(f"  brak: {pattern}", file=sys.stderr)
        return 1

    print(f"private-artifacts: OK ({len(tracked)} sledzonych plikow, {len(FORBIDDEN)} wzorcow)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
