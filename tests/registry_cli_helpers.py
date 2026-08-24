import hashlib
import json
from pathlib import Path

from jsonschema import Draft202012Validator
from referencing import Registry
from referencing import Resource


ROUTER_SCHEMA_V1_SHAPE_SHA256 = "a002afb33e923d2ef8b0c47506d6dfa5c09386d8cda661ee688204caef539b85"


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
    registry = Registry().with_resource(intent_schema["$id"], Resource.from_contents(intent_schema))
    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema, registry=registry).validate(payload)
