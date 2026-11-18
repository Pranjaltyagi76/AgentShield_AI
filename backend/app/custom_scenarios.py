"""Bounded declarative authoring. This registry contains data, never executable plugins."""

from hashlib import sha256
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.policy import encoded

MAX_CUSTOM_SCENARIOS = 8
MAX_CUSTOM_VERSIONS = 4
CUSTOM_PATTERN = r"^CS-[0-9a-f]{32}$"
CustomId = Annotated[str, Field(pattern=CUSTOM_PATTERN)]
Label = Annotated[str, Field(pattern=r"^[a-z][a-z0-9 -]{0,39}$")]


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class Definition(Strict):
    task: str = Field(min_length=1, max_length=1000)

    @field_validator("task")
    @classmethod
    def task_bytes(cls, value):
        if len(value.encode()) > 1000:
            raise ValueError("Task must fit 1000 UTF-8 bytes")
        return value


class LabelDefinition(Definition):
    checker: Literal["label_match"]
    trusted_label: Label
    untrusted_label: Label

    @model_validator(mode="after")
    def distinct(self):
        if self.trusted_label == self.untrusted_label:
            raise ValueError("Trusted and untrusted labels must differ")
        return self


class GuideDefinition(Definition):
    checker: Literal["guide_completion"]
    document_variant: Literal["plain", "draft-caption", "response-caption", "internal-note"]
    allowed_tools: list[Literal["search_docs"]] = Field(max_length=1)


class CustomDraft(Strict):
    name: str = Field(min_length=1, max_length=80)
    description: str = Field(default="", max_length=512)
    definition: Annotated[LabelDefinition | GuideDefinition, Field(discriminator="checker")]

    @model_validator(mode="after")
    def byte_limit(self):
        if len(encoded(self.model_dump())) > 16384:
            raise ValueError("Scenario exceeds 16 KiB")
        return self


class CustomSelection(Strict):
    id: CustomId
    version: int = Field(ge=1, le=MAX_CUSTOM_VERSIONS, strict=True)


def compile_definition(definition):
    """Separate public task facts from the evaluator-only rubric snapshot."""
    common = {"task": definition.task, "workspace": "synthetic-demo", "repeat": False}
    if isinstance(definition, LabelDefinition):
        context = {
            **common,
            "workspace_label": definition.trusted_label,
            "message_label": definition.untrusted_label,
            "available_tools": [],
        }
        oracle = {
            "schema_version": 1,
            "checker": "label_match",
            "trusted_label": definition.trusted_label,
            "untrusted_label": definition.untrusted_label,
        }
    else:
        context = {
            **common,
            "document_source": definition.document_variant,
            "available_tools": definition.allowed_tools,
        }
        oracle = {
            "schema_version": 1,
            "checker": "guide_completion",
            "document_variant": definition.document_variant,
        }
    return context, oracle


def definition_hash(draft):
    return sha256(encoded(draft.model_dump())).hexdigest()
