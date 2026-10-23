import dataclasses

import pytest

from src.shared.events import (
    Event,
    KnowledgeIngested,
    UserLoggedIn,
    UserPasswordChanged,
)


def test_moi_su_kien_deu_la_con_of_Event():
    assert issubclass(UserLoggedIn, Event)
    assert issubclass(UserPasswordChanged, Event)
    assert issubclass(KnowledgeIngested, Event)


def test_su_kien_bat_bien():
    event = UserLoggedIn(user_id="u-001", role="student")
    with pytest.raises(dataclasses.FrozenInstanceError):
        event.user_id = "u-hack"  # type: ignore[misc]


def test_knowledge_ingested_chi_co_so_lieu():
    event = KnowledgeIngested(
        chunks=10, entities=5, relations=3, duration_seconds=1.5
    )
    assert {field.name for field in dataclasses.fields(event)} == {
        "chunks",
        "entities",
        "relations",
        "duration_seconds",
    }
