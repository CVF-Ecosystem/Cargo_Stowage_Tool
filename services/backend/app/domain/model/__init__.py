"""M1 synthetic contract. Integer mm/g; no operational approval semantics."""
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StrictInt, model_serializer, model_validator

from ...vessel import PROFILE, CASES
from ...adapters.pipe_registry import DATASET, EXPECTED

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
    shape: Literal["BOX"] = "BOX"


class PipeSourceRef(Model):
    dataset_id: Literal["BALTIMORE-PIPE-V1-1"]
    workbook_sha256: str
    sheet: str
    group_id: str
    source_row: StrictInt
    bundle_index: StrictInt
    pieces: StrictInt
    dimension_warning: bool


class PipeSourceRefV2(Model):
    """Revision-derived bundle identity (scst.pipe-list.v2). Kept separate from
    PipeSourceRef so legacy v1 units serialize byte-identically."""
    dataset_id: Literal["BALTIMORE-PIPE-V1-1"]
    workbook_sha256: str
    sheet: str
    group_id: str
    source_row: StrictInt | None
    bundle_index: StrictInt
    pieces: StrictInt
    dimension_warning: bool
    revision_id: str = Field(pattern=r"^BALTIMORE-PIPE-V1-1@R[0-9]{4}$")
    confirmation: Literal["WORKBOOK", "UNVERIFIED", "CONFIRMED"]


class CargoRevisionRef(Model):
    dataset_id: Literal["BALTIMORE-PIPE-V1-1"]
    revision_id: str = Field(pattern=r"^BALTIMORE-PIPE-V1-1@R[0-9]{4}$")
    content_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")


class CargoUnit(Model):
    id: Identifier
    name: str = Field(min_length=1, max_length=100)
    kind: Literal["BAR_BUNDLE", "PIPE_BUNDLE"]
    requirement: Literal["required", "optional", "excluded"]
    length_mm: Dimension
    width_mm: Dimension
    height_mm: Dimension
    mass_g: Mass
    dimensions_um: tuple[StrictInt, StrictInt, StrictInt] | None = None
    source_ref: PipeSourceRef | PipeSourceRefV2 | None = None


class Placement(Model):
    unit_id: Identifier
    x_mm: Coordinate
    y_mm: Coordinate
    z_mm: Coordinate = 0
    layer: Annotated[StrictInt, Field(ge=0)] = 0
    supported_by: list[Identifier] = Field(default_factory=list, max_length=200)
    yaw_deg: StrictInt = Field(ge=0, le=270, multiple_of=90)


class Limits(Model):
    certificate_cargo_limit_g: Mass
    voyage_cargo_limit_g: Mass
    cargo_onboard_g: Annotated[StrictInt, Field(ge=0, le=1_000_000_000_000)] = 0

    @model_validator(mode="after")
    def relationships(self):
        if self.voyage_cargo_limit_g > self.certificate_cargo_limit_g:
            raise ValueError("Voyage limit exceeds certificate limit")
        if self.cargo_onboard_g > self.voyage_cargo_limit_g:
            raise ValueError("Onboard cargo exceeds voyage limit")
        return self


class VesselReference(Model):
    vessel_id: str = Field(pattern=r"^[A-Z0-9][A-Z0-9-]{1,31}$")
    case_id: str = Field(pattern=r"^[A-Z0-9][A-Z0-9-]{0,31}$")
    profile_version: Annotated[StrictInt, Field(ge=1)] | None = None
    profile_sha256: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")

    @model_serializer(mode="wrap")
    def omit_absent_profile(self, handler):
        # Built-in VINAFCO268 plans carry neither profile field; omit them so their JSON stays byte-identical.
        data = handler(self)
        if isinstance(data, dict):
            for key in ("profile_version", "profile_sha256"):
                if data.get(key) is None:
                    data.pop(key, None)
        return data


class Plan(Model):
    contract_version: Literal["scst.m1.v1", "scst.m2a.v1", "scst.pipe-list.v1", "scst.pipe-list.v2"] = "scst.m1.v1"
    source: Literal["SYNTHETIC", "MIXED_REFERENCE", "USER_ENTERED"] = "SYNTHETIC"
    cargo_source: Literal["SYNTHETIC", "USER_ENTERED", "DOCUMENT_CALCULATED"] | None = None
    vessel: VesselReference | None = None
    cargo_dataset: Literal["BALTIMORE-PIPE-V1-1"] | None = None
    cargo_revision: CargoRevisionRef | None = None
    # M3a D1: absent/None/SINGLE_LAYER keep today's single-layer rules; omitted from JSON when None.
    stacking: Literal["SINGLE_LAYER", "COLUMNS_V1"] | None = None
    hold: Hold
    limits: Limits
    units: list[CargoUnit] = Field(max_length=2000)
    placements: list[Placement] = Field(max_length=2000)

    @model_serializer(mode="wrap")
    def omit_absent_revision(self, handler):
        # Legacy contracts never carried cargo_revision; omit it when absent so
        # their JSON (responses and newly saved snapshots) stays byte-identical.
        data = handler(self)
        if isinstance(data, dict):
            for key in ("cargo_revision", "stacking"):
                if data.get(key) is None:
                    data.pop(key, None)
        return data

    @model_validator(mode="after")
    def identities(self):
        pipe = self.contract_version == "scst.pipe-list.v1"
        if self.contract_version != "scst.pipe-list.v2" and self.cargo_revision is not None:
            raise ValueError("Only scst.pipe-list.v2 carries a cargo revision")
        if self.contract_version == "scst.pipe-list.v2":
            # Structural checks only; exact revision binding needs the revision
            # store and is enforced by adapters.plan_binding at every entry point.
            if self.cargo_dataset != DATASET or self.cargo_source != "DOCUMENT_CALCULATED" or self.cargo_revision is None:
                raise ValueError("Pipe revision plan requires dataset, document source and cargo revision")
            if self.cargo_revision.dataset_id != self.cargo_dataset:
                raise ValueError("Cargo revision dataset does not match plan dataset")
            if any(not isinstance(u.source_ref, PipeSourceRefV2) or u.kind != "PIPE_BUNDLE" or u.dimensions_um is None for u in self.units):
                raise ValueError("Pipe revision units require revision source references")
        elif pipe:
            if self.cargo_dataset != DATASET or self.cargo_source != "DOCUMENT_CALCULATED" or len(self.units) != len(EXPECTED):
                raise ValueError("Pipe dataset and complete manifest required")
            for unit in self.units:
                expected = EXPECTED.get(unit.id)
                actual = unit.model_dump(mode="json")
                if expected is None or any(actual[k] != expected[k] for k in expected if k != "requirement"):
                    raise ValueError("Pipe source data does not match registry")
        else:
            if self.cargo_dataset is not None or self.cargo_source == "DOCUMENT_CALCULATED" or len(self.units)>200 or len(self.placements)>200:
                raise ValueError("Legacy plan cannot carry pipe dataset")
            if any(u.dimensions_um is not None or u.source_ref is not None for u in self.units):
                raise ValueError("Legacy plan cannot carry pipe source fields")
        if self.contract_version == "scst.m1.v1":
            if not self.units or self.source == "USER_ENTERED" or self.cargo_source is not None:
                raise ValueError("M1 requires cargo and synthetic or reference source")
        elif self.cargo_source is None:
            self.cargo_source = "SYNTHETIC"
        if self.source != "MIXED_REFERENCE":
            if self.vessel is not None:
                raise ValueError("Synthetic plan must not claim a vessel")
        else:
            if self.vessel is None:
                raise ValueError("Reference vessel and case required")
            ref = self.vessel
            if ref.profile_version is None and ref.profile_sha256 is None:
                if ref.vessel_id != PROFILE["id"] or ref.case_id not in CASES:
                    raise ValueError("Reference vessel must be VINAFCO268 with a known operating case")
                hold = PROFILE["hold"]
                expected = (hold["id"], hold["name"], hold["length_mm"], hold["width_mm"], hold["height_mm"], "BOX")
                actual = (self.hold.id, self.hold.name, self.hold.length_mm, self.hold.width_mm, self.hold.height_mm, self.hold.shape)
                if actual != expected or self.limits.certificate_cargo_limit_g != CASES[ref.case_id]["cargo_mass_g"]:
                    raise ValueError("Reference hold or cargo limit does not match profile")
            elif ref.profile_version is None or ref.profile_sha256 is None or ref.vessel_id == PROFILE["id"]:
                # User profiles: structural only; adapters.plan_binding checks the stored profile at every entry point.
                raise ValueError("A user vessel profile needs both profile_version and profile_sha256 and cannot be VINAFCO268")
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
    code: Literal["OVERWEIGHT", "OUT_OF_BOUNDS", "OVERLAP", "LAYER_UNSUPPORTED", "REQUIRED_UNPLACED", "EMPTY_MANIFEST",
                  "SUPPORT_MISSING", "SUPPORT_LEVEL_MISMATCH", "SUPPORT_AREA_LOW", "SUPPORT_CENTRE_UNSUPPORTED",
                  "LAYER_INDEX_INVALID"]
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
    status: Literal["DRAFT", "GEOMETRY_FEASIBLE", "RULES_CHECKED"]
    basic_checks_passed: bool
    issues: list[Issue]
    unchecked: list[str]
    operational_eligible: Literal[False] = False
    total_issues: int | None = None
    issues_truncated: bool | None = None
    affected_unit_ids: list[str] | None = None
