from dataclasses import dataclass
from functools import cached_property
from pathlib import Path

import yaml

DEFAULT_PATH = Path(__file__).resolve().parents[1] / "configs" / "jd_spec.yaml"


@dataclass
class JDSpec:
    raw: dict

    @classmethod
    def load(cls, path: str | Path = DEFAULT_PATH) -> "JDSpec":
        with open(path, encoding="utf-8") as f:
            return cls(yaml.safe_load(f))

    @property
    def experience_band(self) -> dict:
        return self.raw["role"]["experience_band"]

    @cached_property
    def must_haves(self) -> dict[str, dict]:
        return {m["name"]: m for m in self.raw["must_haves"]}

    @cached_property
    def nice_to_haves(self) -> dict[str, dict]:
        return {m["name"]: m for m in self.raw["nice_to_haves"]}

    @cached_property
    def disqualifiers(self) -> dict[str, str]:
        return {d["name"]: d["description"] for d in self.raw["disqualifiers"]}

    @cached_property
    def consulting_companies(self) -> set[str]:
        return set(self.raw["companies"]["consulting"])

    @cached_property
    def product_companies(self) -> set[str]:
        return set(self.raw["companies"]["product"])

    @property
    def positive_domains(self) -> list[str]:
        return self.raw["domains"]["positive"]

    @property
    def negative_domains(self) -> list[str]:
        return self.raw["domains"]["negative"]

    @property
    def tier1_cities(self) -> list[str]:
        return self.raw["location"]["tier1_cities"]

    def skill_terms(self) -> dict[str, list[str]]:
        groups = self.raw["must_haves"] + self.raw["nice_to_haves"]
        return {g["name"]: g["terms"] for g in groups}
