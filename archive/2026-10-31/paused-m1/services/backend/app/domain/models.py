"""M1 synthetic contract. Integer mm/g; no operational approval semantics."""
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StrictInt, model_validator

Dimension = Annotated[StrictInt, Field(gt=0, le=1_000_000)]
Mass = Annotated[StrictInt, Field(gt=0, le=1_000_000_000_000)]
Coordinate = Annotated[StrictInt, Field(ge=-1_000_000, le=1_000_000)]
Identifier = Annotated[str, Field(pattern=r"^[A-Z0-9][A-Z0-9_-]{0,39}$")]


class Model(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Hold(Model):
    id: Identifier
    name: str = Field(min_length=1, max_length=100)
    length_mm: Dimension
    width_mm: Dimension
    height_mm: Dimension
    cargo_limit_g: Mass
    shape: Literal["BOX"] = "BOX"


class CargoUnit(Model):
    id: Identifier
    name: str = Field(min_length=1, max_length=100)
    kind: Literal["BAR_BUNDLE", "PIPE_BUNDLE"]
    requirement: Literal["required", "optional", "excluded"]
    length_mm: Dimension
    width_mm: Dimension
    height_mm: Dimension
    mass_g: Mass


class Placement(Model):
    unit_id: Identifier
    x_mm: Coordinate
    y_mm: Coordinate
    z_mm: Coordinate = 0
    yaw_deg: StrictInt = Field(ge=0, le=270, multiple_of=90)


class Plan(Model):
    contract_version: Literal["scst.demo.v1"] = "scst.demo.v1"
    source: Literal["SYNTHETIC"] = "SYNTHETIC"
    hold: Hold
    units: list[CargoUnit] = Field(min_length=1, max_length=200)
    placements: list[Placement] = Field(max_length=200)

    @model_validator(mode="after")
    def identities(self):
        units = {u.id: u for u in self.units}
        if len(units) != len(self.units):
            raise ValueError("Unit IDs must be unique")
        placed = [p.unit_id for p in self.placements]
        if len(set(placed)) != len(placed):
            raise ValueError("A physical unit can only be placed once")
        if any(i not in units for i in placed):
            raise ValueError("Placement references an unknown unit")
        if any(units[i].requirement == "excluded" for i in placed):
            raise ValueError("Excluded cargo cannot be placed")
        return self


class Issue(Model):
    code: Literal["OVERWEIGHT", "OUT_OF_BOUNDS", "OVERLAP", "LAYER_UNSUPPORTED", "REQUIRED_UNPLACED"]
    unit_ids: list[str]
    message: str


class Summary(Model):
    manifest_mass_g: int
    placed_mass_g: int
    remaining_capacity_g: int
    placed_count: int
    unplaced_ids: list[str]
    excluded_ids: list[str]


class Evaluation(Model):
    plan: Plan
    summary: Summary
    basic_checks_passed: bool
    issues: list[Issue]
    unchecked: list[str]
    operational_eligible: Literal[False] = False
