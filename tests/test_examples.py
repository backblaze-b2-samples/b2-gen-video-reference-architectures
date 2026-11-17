"""Guardrails for the B2 configuration templates in examples/."""
from __future__ import annotations

import json

import pytest

import generate_catalog as gc

EXAMPLES = gc.ROOT / "examples"
LIFECYCLE_FILES = sorted(EXAMPLES.glob("lifecycle-*.json"))
# Prefixes that hold assets awaiting review; an age-based hide rule there deletes unreviewed work.
REVIEW_PREFIXES = ("staging/", "inbox/")


def load(path):
    return json.loads(path.read_text())


@pytest.mark.parametrize("path", sorted(EXAMPLES.glob("*.json")), ids=lambda p: p.name)
def test_examples_are_valid_json(path):
    load(path)


@pytest.mark.parametrize("path", LIFECYCLE_FILES, ids=lambda p: p.name)
def test_lifecycle_rules_use_b2_shape(path):
    for rule in load(path):
        required = {"fileNamePrefix", "daysFromUploadingToHiding", "daysFromHidingToDeleting"}
        assert required <= set(rule) <= required | {"daysFromStartingToCancelingUnfinishedLargeFiles"}
        if "daysFromStartingToCancelingUnfinishedLargeFiles" in rule:
            assert rule["daysFromStartingToCancelingUnfinishedLargeFiles"] >= 1
        assert rule["daysFromHidingToDeleting"] is None or rule["daysFromHidingToDeleting"] >= 1


def test_no_lifecycle_example_hides_review_prefixes_by_age():
    for path in LIFECYCLE_FILES:
        for rule in load(path):
            if any(p in rule["fileNamePrefix"] for p in REVIEW_PREFIXES):
                assert rule["daysFromUploadingToHiding"] is None, f"{path.name}: {rule['fileNamePrefix']}"


def test_event_notification_prefix_matches_staging_lifecycle():
    rule = load(EXAMPLES / "event-notifications-staging.json")["eventNotificationRules"][0]
    staging = load(EXAMPLES / "lifecycle-staging-hidden.json")[0]
    assert rule["objectNamePrefix"] == staging["fileNamePrefix"]


def test_object_lock_example_uses_native_request_fields():
    # isFileLockEnabled is a response field; requests use fileLockEnabled, and default retention is an update.
    body = load(EXAMPLES / "object-lock-governance.json")
    assert body["b2_create_bucket"] == {"fileLockEnabled": True}
    assert body["b2_update_bucket"]["defaultRetention"]["mode"] == "governance"
    assert "isFileLockEnabled" not in json.dumps(body)


def test_every_example_is_documented():
    readme = (EXAMPLES / "README.md").read_text()
    for path in EXAMPLES.glob("*.json"):
        assert f"`{path.name}`" in readme, path.name


def test_provider_input_expiry_does_not_remove_run_outputs():
    rules = load(EXAMPLES / "lifecycle-provider-inputs.json")
    assert rules and all(rule["fileNamePrefix"] == "inputs/" for rule in rules)
    assert all(rule["daysFromUploadingToHiding"] >= 1 for rule in rules)
