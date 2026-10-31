"""Pydantic request and response schemas for the DNA analyzer API."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class SearchRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    text: str
    pattern: str
    algorithms: list[Literal["naive", "kmp", "rabin_karp"]] = Field(min_length=1)

    @field_validator("algorithms")
    @classmethod
    def algorithms_are_unique(cls, value: list[str]) -> list[str]:
        if len(value) != len(set(value)):
            raise ValueError("algorithms must not contain duplicates")
        return value


class SimilarityRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    seq_a: str
    seq_b: str


class BenchmarkRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    pattern_length: int = Field(ge=2, le=1000)
    text_sizes: list[int] = Field(min_length=1, max_length=8)
    preset: Literal["random", "worst_case"]

    @field_validator("text_sizes")
    @classmethod
    def sizes_in_range(cls, value: list[int]) -> list[int]:
        if any(size < 1 or size > 200_000 for size in value):
            raise ValueError("text_sizes values must be between 1 and 200000")
        return value

    @model_validator(mode="after")
    def sizes_fit_pattern(self):
        if any(size < self.pattern_length for size in self.text_sizes):
            raise ValueError("each text size must be at least pattern_length")
        return self


class SearchResult(BaseModel):
    matches: list[int]
    match_count: int
    time_ms: float
    comparisons: int


class SearchResponse(BaseModel):
    results: dict[str, SearchResult]
    kmp_lps: list[int] | None
    rabin_karp_stats: dict[str, int] | None
    text_length: int
    pattern_length: int


class GenerateResponse(BaseModel):
    sequence: str


class UploadResponse(BaseModel):
    sequence: str
    length: int
