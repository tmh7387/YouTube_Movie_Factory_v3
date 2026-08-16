"""
Job 3 — a user can actually supply the reference pictures.

The pipeline has been able to consume a character's ref_sheet_url since the wiring
pass, but nothing wrote that field: the bible generator emits null, and the only
upload endpoint appended to a shared pile rather than attaching to an entity. In
practice every scene took the "no references" path — the fallback the reference work
existed to replace.
"""
import uuid

import pytest
from sqlalchemy import select

from app.models import PreProductionBible

pytestmark = pytest.mark.smoke


CHARACTERS = [
    {"name": "The Diver", "physical": "tall", "wardrobe": "navy wetsuit", "ref_sheet_url": None},
    {"name": "The Elder", "physical": "stooped", "wardrobe": "oilskin", "ref_sheet_url": None},
]
ENVIRONMENTS = [
    {"name": "Kelp Forest", "description": "green cathedral", "ref_sheet_url": None},
]


@pytest.fixture
def stub_storage(monkeypatch):
    """Supabase is the network edge here; the endpoint logic is what is under test."""
    uploaded = []

    async def _upload_file(file_bytes, filename, folder, bucket=None):
        uploaded.append({"filename": filename, "folder": folder, "size": len(file_bytes)})
        return {"public_url": f"https://storage.test/{folder}/{filename}"}

    from app.services.supabase_storage_service import supabase_storage

    monkeypatch.setattr(supabase_storage, "upload_file", _upload_file)
    return uploaded


@pytest.fixture
async def bible(api):
    """A draft bible with two characters and one environment."""
    created = await api.post("/api/bible/", json={
        "name": "Reference test bible",
        "characters": CHARACTERS,
        "environments": ENVIRONMENTS,
    })
    assert created.status_code in (200, 201), created.text
    return created.json()


def _png() -> bytes:
    return b"\x89PNG\r\n\x1a\n" + b"reference bytes"


# --- attaching ---------------------------------------------------------------

async def test_a_sheet_attaches_to_the_named_character(api, bible, stub_storage):
    response = await api.post(
        f"/api/bible/{bible['id']}/characters/0/reference",
        files={"file": ("diver.png", _png(), "image/png")},
    )
    assert response.status_code == 200, response.text

    characters = response.json()["characters"]
    assert characters[0]["ref_sheet_url"] == "https://storage.test/bibles/{}/characters/0/diver.png".format(bible["id"])
    # The other character is untouched — this is per-entity, not a shared pile.
    assert characters[1]["ref_sheet_url"] is None
    assert stub_storage[0]["folder"].endswith("/characters/0")


async def test_the_change_survives_a_reload(api, bible, stub_storage):
    """
    SQLAlchemy does not notice an in-place edit of a JSONB list, so writing
    `bible.characters[0]["ref_sheet_url"] = url` commits nothing. The endpoint has to
    reassign the whole list — this test is what catches a regression to the in-place form.
    """
    await api.post(
        f"/api/bible/{bible['id']}/characters/0/reference",
        files={"file": ("diver.png", _png(), "image/png")},
    )

    from app.db.session import AsyncSessionLocal

    async with AsyncSessionLocal() as session:
        row = (await session.execute(
            select(PreProductionBible).where(PreProductionBible.id == uuid.UUID(bible["id"]))
        )).scalar_one()

    assert row.characters[0]["ref_sheet_url"] is not None
    assert row.characters[1]["ref_sheet_url"] is None


async def test_environments_work_the_same_way(api, bible, stub_storage):
    response = await api.post(
        f"/api/bible/{bible['id']}/environments/0/reference",
        files={"file": ("kelp.png", _png(), "image/png")},
    )
    assert response.status_code == 200, response.text
    assert response.json()["environments"][0]["ref_sheet_url"].endswith("kelp.png")


async def test_attaching_is_recorded_in_the_process_log(api, bible, stub_storage):
    response = await api.post(
        f"/api/bible/{bible['id']}/characters/1/reference",
        files={"file": ("elder.png", _png(), "image/png")},
    )
    log = response.json()["process_log"]
    assert any("The Elder" in entry["action"] for entry in log), log


async def test_replacing_a_sheet_overwrites_rather_than_appends(api, bible, stub_storage):
    for name in ("first.png", "second.png"):
        response = await api.post(
            f"/api/bible/{bible['id']}/characters/0/reference",
            files={"file": (name, _png(), "image/png")},
        )
    assert response.json()["characters"][0]["ref_sheet_url"].endswith("second.png")


# --- clearing ----------------------------------------------------------------

async def test_a_sheet_can_be_detached(api, bible, stub_storage):
    await api.post(
        f"/api/bible/{bible['id']}/characters/0/reference",
        files={"file": ("diver.png", _png(), "image/png")},
    )
    response = await api.delete(f"/api/bible/{bible['id']}/characters/0/reference")
    assert response.status_code == 200, response.text
    assert response.json()["characters"][0]["ref_sheet_url"] is None


# --- rejections --------------------------------------------------------------

async def test_an_out_of_range_index_is_a_404(api, bible, stub_storage):
    response = await api.post(
        f"/api/bible/{bible['id']}/characters/9/reference",
        files={"file": ("x.png", _png(), "image/png")},
    )
    assert response.status_code == 404
    assert "index 9" in response.json()["detail"]


async def test_an_unknown_entity_is_a_404(api, bible, stub_storage):
    response = await api.post(
        f"/api/bible/{bible['id']}/props/0/reference",
        files={"file": ("x.png", _png(), "image/png")},
    )
    assert response.status_code == 404


async def test_an_empty_file_is_rejected(api, bible, stub_storage):
    response = await api.post(
        f"/api/bible/{bible['id']}/characters/0/reference",
        files={"file": ("empty.png", b"", "image/png")},
    )
    assert response.status_code == 422


async def test_a_locked_bible_rejects_changes(api, bible, stub_storage):
    await api.put(f"/api/bible/{bible['id']}/lock")
    response = await api.post(
        f"/api/bible/{bible['id']}/characters/0/reference",
        files={"file": ("x.png", _png(), "image/png")},
    )
    assert response.status_code == 409
    assert "locked" in response.json()["detail"].lower()


async def test_a_storage_failure_is_reported_not_swallowed(api, bible, monkeypatch):
    async def _fail(**_kw):
        return {"error": "bucket does not exist"}

    from app.services.supabase_storage_service import supabase_storage

    monkeypatch.setattr(supabase_storage, "upload_file", _fail)

    response = await api.post(
        f"/api/bible/{bible['id']}/characters/0/reference",
        files={"file": ("x.png", _png(), "image/png")},
    )
    assert response.status_code == 502
    assert "bucket" in response.json()["detail"]


# --- the point of all of it --------------------------------------------------

async def test_an_attached_sheet_reaches_the_generator(api, bible, stub_storage):
    """
    Close the loop: once a sheet is attached, the resolver that scene generation uses
    picks it up for a scene tagged with that character.
    """
    import tasks.production as production

    response = await api.post(
        f"/api/bible/{bible['id']}/characters/0/reference",
        files={"file": ("diver.png", _png(), "image/png")},
    )
    stored = response.json()

    from types import SimpleNamespace

    fake_bible = SimpleNamespace(
        characters=stored["characters"],
        environments=stored["environments"],
        character_sheet_urls=[],
        environment_sheet_urls=[],
    )
    scene = SimpleNamespace(bible_character="The Diver", bible_environment=None)

    urls, character = production._collect_reference_urls(fake_bible, scene)
    assert urls == [stored["characters"][0]["ref_sheet_url"]]
    assert character["name"] == "The Diver"


async def test_a_character_without_a_sheet_still_falls_back_to_the_pile(api, bible, stub_storage):
    from types import SimpleNamespace

    import tasks.production as production

    fake_bible = SimpleNamespace(
        characters=CHARACTERS,
        environments=ENVIRONMENTS,
        character_sheet_urls=["https://storage.test/pile/shared.png"],
        environment_sheet_urls=[],
    )
    scene = SimpleNamespace(bible_character="The Diver", bible_environment=None)

    urls, _ = production._collect_reference_urls(fake_bible, scene)
    assert urls == ["https://storage.test/pile/shared.png"]
