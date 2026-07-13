import hashlib
import json
from pathlib import Path

from jsonschema import Draft202012Validator
from jsonschema import validators
from referencing import Registry
from referencing import Resource


ROUTER_SCHEMA_V1_SHAPE_SHA256 = "c44cfd737c181a670152ee5400379c3686d428c877d2ba823b71d326804185e2"


def normalized_payload_shape(value):
    if isinstance(value, dict):
        return {
            key: normalized_payload_shape(item)
            for key, item in sorted(value.items())
            if key != "generated_at"
        }
    if isinstance(value, list):
        return [normalized_payload_shape(item) for item in value]
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "bool"
    if isinstance(value, int):
        return "int"
    if isinstance(value, float):
        return "float"
    if isinstance(value, str):
        return "str"
    raise TypeError(f"unsupported payload value: {type(value).__name__}")


def payload_shape_sha256(payload):
    normalized = normalized_payload_shape(payload)
    encoded = json.dumps(normalized, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def validate_task_pack_v2(payload):
    schema = json.loads(Path("schemas/task-pack-v2.schema.json").read_text(encoding="utf-8"))
    intent_schema = json.loads(Path("schemas/intent-graph.schema.json").read_text(encoding="utf-8"))
    selected_skill_schema = json.loads(
        Path("schemas/task-pack-v2-selected-skill.schema.json").read_text(encoding="utf-8")
    )
    contract_schema = json.loads(Path("schemas/contract-v2.schema.json").read_text(encoding="utf-8"))
    manifest_schema = json.loads(
        Path("schemas/skill-manifest.schema.json").read_text(encoding="utf-8")
    )
    registry = Registry().with_resources(
        [
            (intent_schema["$id"], Resource.from_contents(intent_schema)),
            (selected_skill_schema["$id"], Resource.from_contents(selected_skill_schema)),
            (contract_schema["$id"], Resource.from_contents(contract_schema)),
            (manifest_schema["$id"], Resource.from_contents(manifest_schema)),
        ]
    )
    Draft202012Validator.check_schema(schema)
    Draft202012Validator.check_schema(selected_skill_schema)
    strict_type_checker = Draft202012Validator.TYPE_CHECKER.redefine(
        "integer", lambda checker, value: isinstance(value, int) and not isinstance(value, bool)
    )
    strict_validator = validators.extend(Draft202012Validator, type_checker=strict_type_checker)
    strict_validator(schema, registry=registry).validate(payload)
