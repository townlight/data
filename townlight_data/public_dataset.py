from collections.abc import Iterable, Mapping, Sequence
from csv import QUOTE_ALL, writer
from dataclasses import asdict, dataclass
from datetime import date
from decimal import Decimal, InvalidOperation
from io import StringIO
import json
import re

from .data_dictionary import draft_data_dictionary
from .redaction_review import review_fields_for_publication

_FIELD_NAME_RE = re.compile(r'[a-z][a-z0-9_]{0,63}', re.ASCII)
_DECIMAL_RE = re.compile(r'-?(?:0|[1-9][0-9]*)(?:[.][0-9]+)?', re.ASCII)
_DATE_RE = re.compile(r'[0-9]{4}-[0-9]{2}-[0-9]{2}', re.ASCII)
_ALLOWED_TYPES = frozenset({'text', 'integer', 'decimal', 'date'})
_FORMULA_STARTS = frozenset({'=', '+', '-', '@'})
_MAX_FIELDS = 32
_MAX_ROWS = 5000
_LINE_FEED = chr(10)


@dataclass(frozen=True)
class PublicField:
    name: str
    data_type: str
    description: str


def build_public_dataset(
    fields: Sequence[PublicField], rows: Iterable[Mapping[str, object]]
) -> dict[str, bytes]:
    field_list = _validated_fields(fields)
    records = _normalized_records(field_list, rows)
    return {
        'dataset.csv': _csv_bytes(field_list, records),
        'dataset.json': _json_bytes(records),
        'data-dictionary.json': _dictionary_bytes(field_list),
    }


def _validated_fields(fields: Sequence[PublicField]) -> list[PublicField]:
    field_list = list(fields)
    if not field_list:
        raise ValueError('Schema must contain at least one field.')
    if len(field_list) > _MAX_FIELDS:
        raise ValueError(f'Schema cannot exceed {_MAX_FIELDS} fields.')
    seen: set[str] = set()
    for field in field_list:
        if not _FIELD_NAME_RE.fullmatch(field.name):
            raise ValueError(f'Invalid field name: {field.name!r}.')
        if field.name in seen:
            raise ValueError(f'Duplicate field name: {field.name!r}.')
        if field.data_type not in _ALLOWED_TYPES:
            raise ValueError(f'Invalid data type for {field.name!r}: {field.data_type!r}.')
        if not field.description.strip():
            raise ValueError(f'Description required for field {field.name!r}.')
        seen.add(field.name)
    if not review_fields_for_publication([field.name for field in field_list]).ready_for_publication:
        raise ValueError('Review or remove flagged fields before creating a public dataset.')
    return field_list


def _normalized_records(
    fields: Sequence[PublicField], rows: Iterable[Mapping[str, object]]
) -> list[dict[str, object]]:
    records: list[dict[str, object]] = []
    for row_number, row in enumerate(rows, start=1):
        if row_number > _MAX_ROWS:
            raise ValueError(f'Dataset cannot exceed {_MAX_ROWS} rows.')
        record: dict[str, object] = {}
        for field in fields:
            if field.name not in row:
                raise ValueError(f'Row {row_number} missing field {field.name!r}.')
            record[field.name] = _validated_value(field, row[field.name], row_number)
        records.append(record)
    return records


def _validated_value(field: PublicField, value: object, row_number: int) -> object:
    if value is None:
        return None
    if field.data_type == 'text':
        if not isinstance(value, str):
            raise ValueError(f'Field {field.name!r} in row {row_number} must be text.')
        if _has_formula_prefix(value):
            raise ValueError(f'Field {field.name!r} in row {row_number} starts like a formula.')
        if any(ord(char) < 32 or ord(char) == 127 for char in value):
            raise ValueError(f'Field {field.name!r} in row {row_number} contains a control character.')
        return value
    if field.data_type == 'integer':
        if isinstance(value, bool) or not isinstance(value, int):
            raise ValueError(f'Field {field.name!r} in row {row_number} must be an integer.')
        return value
    if field.data_type == 'decimal':
        return _validated_decimal(field.name, value, row_number)
    return _validated_date(field.name, value, row_number)


def _validated_decimal(name: str, value: object, row_number: int) -> str:
    if not isinstance(value, str) or not _DECIMAL_RE.fullmatch(value):
        raise ValueError(f'Field {name!r} in row {row_number} must be a decimal string.')
    try:
        parsed = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError(
            f'Field {name!r} in row {row_number} must be a decimal string.'
        ) from exc
    if not parsed.is_finite():
        raise ValueError(f'Field {name!r} in row {row_number} must be finite.')
    return value


def _validated_date(name: str, value: object, row_number: int) -> str:
    if not isinstance(value, str) or not _DATE_RE.fullmatch(value):
        raise ValueError(f'Field {name!r} in row {row_number} must be a date string.')
    try:
        date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(
            f'Field {name!r} in row {row_number} must be a calendar date.'
        ) from exc
    return value


def _has_formula_prefix(value: str) -> bool:
    for char in value:
        if char.isspace() or ord(char) < 32 or ord(char) == 127:
            continue
        return char in _FORMULA_STARTS
    return False


def _csv_bytes(
    fields: Sequence[PublicField], records: list[dict[str, object]]
) -> bytes:
    output = StringIO(newline='')
    csv_writer = writer(output, lineterminator=_LINE_FEED, quoting=QUOTE_ALL)
    csv_writer.writerow([field.name for field in fields])
    for record in records:
        csv_writer.writerow([
            '' if record[field.name] is None else record[field.name] for field in fields
        ])
    return output.getvalue().encode('utf-8')


def _json_bytes(records: list[dict[str, object]]) -> bytes:
    return json.dumps(records, ensure_ascii=False, separators=(',', ':')).encode('utf-8')


def _dictionary_bytes(fields: Sequence[PublicField]) -> bytes:
    source_fields = [
        {'name': field.name, 'type': field.data_type, 'description': field.description}
        for field in fields
    ]
    dictionary = [asdict(entry) for entry in draft_data_dictionary(source_fields)]
    return json.dumps(dictionary, ensure_ascii=False, separators=(',', ':')).encode('utf-8')
