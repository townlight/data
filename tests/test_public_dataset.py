import csv
import io
import json

import pytest

from townlight_data.public_dataset import PublicField, build_public_dataset


def _fields():
    return [
        PublicField(name="id", data_type="integer", description="Row identifier"),
        PublicField(name="name", data_type="text", description="Display name"),
    ]


def test_deterministic_csv_and_json_with_unicode_quoting():
    fields = _fields()
    rows = [
        {"id": 1, "name": "Zoë, Jr."},
        {"id": 2, "name": "李雷"},
    ]
    first = build_public_dataset(fields, rows)
    second = build_public_dataset(fields, rows)

    assert first["dataset.csv"] == second["dataset.csv"]
    assert first["dataset.json"] == second["dataset.json"]

    csv_bytes = first["dataset.csv"]
    assert isinstance(csv_bytes, bytes)
    # Comma-containing unicode value must be quoted (and preserved verbatim).
    assert b'"Zo\xc3\xab, Jr."' in csv_bytes

    parsed = list(csv.DictReader(io.StringIO(csv_bytes.decode("utf-8"))))
    assert [row["name"] for row in parsed] == ["Zoë, Jr.", "李雷"]
    assert [row["id"] for row in parsed] == ["1", "2"]

    json_rows = json.loads(first["dataset.json"])
    assert [row["name"] for row in json_rows] == ["Zoë, Jr.", "李雷"]


def test_allowlist_filters_private_fields_and_dictionary_records_source():
    fields = _fields()
    rows = [{"id": 7, "name": "Ada", "secret": "top-secret", "email": "a@b.c"}]

    out = build_public_dataset(fields, rows)
    csv_bytes = out["dataset.csv"]
    json_bytes = out["dataset.json"]

    for token in (b"secret", b"top-secret", b"a@b.c"):
        assert token not in csv_bytes
        assert token not in json_bytes

    dictionary = json.loads(out["data-dictionary.json"])
    assert isinstance(dictionary, list)
    by_name = {entry["field_name"]: entry for entry in dictionary}
    assert set(by_name) == {field.name for field in fields}
    for field in fields:
        entry = by_name[field.name]
        assert set(entry.keys()) == {
            "field_name",
            "source_name",
            "data_type",
            "description",
            "publication_notes",
        }
        assert entry["field_name"] == field.name
        assert entry["data_type"] == field.data_type
        assert entry["description"] == field.description


def test_rejects_formula_prefixes_and_embedded_cr():
    fields = [PublicField(name="label", data_type="text", description="Label")]

    for bad_value in ("=cmd", "+cmd", "-cmd", "@cmd"):
        with pytest.raises(ValueError):
            build_public_dataset(fields, [{"label": bad_value}])

    with pytest.raises(ValueError):
        build_public_dataset(fields, [{"label": "line1\rline2"}])


def test_rejects_email_field_bool_integer_and_malformed_date():
    with pytest.raises(ValueError):
        build_public_dataset(
            [PublicField(name="email", data_type="text", description="email")],
            [{"email": "a@b.c"}],
        )

    int_field = PublicField(name="count", data_type="integer", description="Count")
    with pytest.raises(ValueError):
        build_public_dataset([int_field], [{"count": True}])

    date_field = PublicField(name="when", data_type="date", description="When")
    with pytest.raises(ValueError):
        build_public_dataset([date_field], [{"when": "not-a-date"}])
