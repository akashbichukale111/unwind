"""Who is allowed to be whom, enforced across a whole bench rather than a pair.

Task 3 needed one separation: the assessor must not grade a re-derivation it
produced. Task 4's court needs the general form, because ruling 1.10 is
non-negotiable and the failure it prevents is the one that would hollow out the
entire project:

    IF THE ARBITER SHARES A PRINCIPAL WITH AN OWNER, AN ASSESSOR OR A
    RE-DERIVER, THIS IS NOT A MULTI-AGENT SYSTEM. It is one model talking to
    itself in different voices, and the separation of arguing party from
    deciding party -- the reason courts are not run by the defendant -- is
    decoration.

So separation is checked over a SET of role assignments, not a pair, and a
collision anywhere in the bench raises. The check is total, it is cheap, and
`tests/test_court.py` includes a vacuity case for every role pair that matters:
a guard nobody has ever seen fire is a guard nobody should trust (Task 3,
ruling 1.6).

This module deliberately imports nothing from `judgment/`, `court/` or
`spine/`. It is the shared vocabulary those three agree on, so putting it in
any of them would make the other two import a peer.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from enum import Enum


class PrincipalSeparationError(RuntimeError):
    """Two roles that must be held by different principals are held by one.

    Canonical for the whole repository. `judgment.assessor` re-exports it so a
    caller catching the assessor's error also catches the court's -- two
    exception types for one concept is how a handler silently misses half the
    cases.
    """


class Role(str, Enum):
    """The roles whose separation is load-bearing.

    OWNER is plural: a repair has N of them, discovered at runtime.
    """

    REDERIVER = "rederiver"
    ASSESSOR = "assessor"
    ARBITER = "arbiter"
    OWNER = "owner"


#: Pairs that must never collapse into one principal, with the reason each
#: exists. Stated as data so the error message can explain WHY rather than just
#: reporting that two strings matched.
_WHY: dict[frozenset[Role], str] = {
    frozenset({Role.ARBITER, Role.OWNER}): (
        "an owner ruling on its own commitment is the defendant judging the case"
    ),
    frozenset({Role.ARBITER, Role.ASSESSOR}): (
        "the arbiter would be ratifying the materiality call it is meant to weigh"
    ),
    frozenset({Role.ARBITER, Role.REDERIVER}): (
        "the arbiter would be ruling on an alternative it authored itself"
    ),
    frozenset({Role.ASSESSOR, Role.REDERIVER}): (
        "grading your own re-derivation makes 'nothing changed' the cheapest "
        "self-consistent answer, and that answer is invisible when wrong"
    ),
    frozenset({Role.ASSESSOR, Role.OWNER}): (
        "an owner grading its own commitment's materiality has an interest in finding it immaterial"
    ),
    frozenset({Role.REDERIVER, Role.OWNER}): (
        "an owner re-deriving its own commitment will re-derive the answer it already holds"
    ),
}


def assert_separate_principals(bench: Mapping[Role, str | Iterable[str]]) -> None:
    """Every role in `bench` must be held by a principal no other role holds.

    `bench` maps a role to one principal, or -- for OWNER -- to many. Roles the
    caller does not supply are simply not checked, so a court that has no
    assessor in play does not have to invent one.

    Raises `PrincipalSeparationError` naming both roles, the shared principal,
    and why that particular collision matters.
    """
    holders: dict[Role, set[str]] = {}
    for role, value in bench.items():
        principals = {value} if isinstance(value, str) else set(value)
        # An empty owner set is legitimate: a radius with no surviving material
        # commitment convenes no court. It is not a separation failure.
        if principals:
            holders[role] = principals

    roles = sorted(holders, key=lambda r: r.value)
    for i, left in enumerate(roles):
        for right in roles[i + 1 :]:
            shared = holders[left] & holders[right]
            if shared:
                why = _WHY.get(frozenset({left, right}), "these roles must stay distinct")
                raise PrincipalSeparationError(
                    f"{left.value} and {right.value} are both held by {sorted(shared)!r}: {why}."
                )

    # Two owners sharing a principal is FINE and must not raise -- one team can
    # legitimately own several commitments. Only cross-role collisions matter.


def assert_arbiter_is_third(
    arbiter: str,
    *,
    owners: Iterable[str],
    assessor: str | None = None,
    rederiver: str | None = None,
) -> None:
    """Ruling 1.10 as a single call, for the common case.

    Convenience over `assert_separate_principals`, not a second implementation:
    it builds the bench and delegates, so there is one rule and one place to fix.
    """
    bench: dict[Role, str | Iterable[str]] = {Role.ARBITER: arbiter, Role.OWNER: list(owners)}
    if assessor is not None:
        bench[Role.ASSESSOR] = assessor
    if rederiver is not None:
        bench[Role.REDERIVER] = rederiver
    assert_separate_principals(bench)
