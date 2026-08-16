"""
db_state decides what a human runs against a live database. That decision is tested.

A wrong stamp target is the one mistake here that cannot be undone by running the tool
again: it tells Alembic a change was applied when it was not, and every later migration
then builds on a table that lacks a column. So the rule — stamp only to the last
revision with nothing absent before it — is pinned rather than trusted.
"""
import db_state
from db_state import CHAIN, COMPLETE, GAP, PARTIAL, decide

DETECTABLE = [rev for rev, _l, _t, _c, detectable in CHAIN if detectable]


def split_at(index: int):
    """Present up to index, absent after it."""
    return DETECTABLE[:index], DETECTABLE[index:]


def test_a_clean_stop_stamps_to_the_last_applied_revision():
    applied, missing = split_at(len(DETECTABLE) - 2)
    verdict, target, still, gap = decide(applied, missing)

    assert verdict == PARTIAL
    assert target == applied[-1]
    assert still == missing
    assert gap == []


def test_everything_present_stamps_to_head_and_asks_for_no_upgrade():
    verdict, target, still, gap = decide(list(DETECTABLE), [])

    assert verdict == COMPLETE
    assert target == CHAIN[-1][0], "head is the last entry in the chain"
    assert still == [] and gap == []


def test_a_later_revision_present_over_an_earlier_one_absent_is_a_gap():
    """No single stamp describes this. The tool must refuse rather than pick one."""
    applied = DETECTABLE[:3] + [DETECTABLE[5]]
    missing = [DETECTABLE[3], DETECTABLE[4]] + DETECTABLE[6:]

    verdict, target, _still, gap = decide(applied, missing)

    assert verdict == GAP
    assert target == "", "a gap must not offer a stamp target"
    assert gap == [DETECTABLE[5]]


def test_an_empty_database_stamps_to_base_not_to_nothing():
    verdict, target, still, gap = decide([], list(DETECTABLE))

    assert verdict == PARTIAL
    assert target == "base"
    assert still == DETECTABLE and gap == []


def test_the_reconciling_migration_is_never_treated_as_evidence():
    """
    b7c8d9e0f1a2 adopts columns something else already made, with ADD COLUMN IF NOT
    EXISTS. Its columns being present says nothing about whether it ran. Counting them
    invented a gap on a database that had none.
    """
    undetectable = [rev for rev, _l, _t, _c, detectable in CHAIN if not detectable]

    assert undetectable == ["b7c8d9e0f1a2"]
    assert "b7c8d9e0f1a2" not in DETECTABLE

    # The live case that exposed it: applied up to the animation migration, with the
    # reconciling migration's columns already in place.
    applied = DETECTABLE[:DETECTABLE.index("d1e2f3a4b5c6") + 1]
    missing = DETECTABLE[DETECTABLE.index("d1e2f3a4b5c6") + 1:]

    verdict, target, _still, gap = decide(applied, missing)

    assert verdict == PARTIAL and gap == []
    assert target == "d1e2f3a4b5c6"


def test_every_chain_entry_names_a_real_migration_file():
    """A fingerprint for a revision that no longer exists would go quietly stale."""
    from pathlib import Path

    versions = Path(db_state.__file__).resolve().parent / "alembic" / "versions"
    on_disk = {p.name.split("_", 1)[0] for p in versions.glob("*.py")}
    in_chain = {rev for rev, *_ in CHAIN}

    assert in_chain == on_disk, "db_state's chain and alembic/versions have drifted apart"
