"""DNA input normalization and validation helpers."""

from fastapi import HTTPException

MAX_SEQUENCE_LENGTH = 2_000_000
_ALPHABET = frozenset("ACGTN")
_COMPLEMENT = {"A": "T", "C": "G", "G": "C", "T": "A", "N": "N"}


def normalize_sequence(value: str) -> str:
    """Remove FASTA headers and whitespace, then uppercase a sequence."""
    lines = value.splitlines()
    sequence = "".join(
        character
        for line in lines
        if not line.startswith(">")
        for character in line
        if not character.isspace()
    ).upper()
    return sequence


def validate_sequence(value: str, label: str = "sequence") -> str:
    """Normalize and validate non-empty DNA input up to two million bases."""
    sequence = normalize_sequence(value)
    if not sequence:
        raise HTTPException(status_code=422, detail=f"{label} must not be empty")
    if len(sequence) > MAX_SEQUENCE_LENGTH:
        raise HTTPException(
            status_code=422,
            detail=f"{label} must be at most {MAX_SEQUENCE_LENGTH} characters",
        )
    invalid = next((character for character in sequence if character not in _ALPHABET), None)
    if invalid is not None:
        raise HTTPException(
            status_code=422,
            detail=f"{label} contains invalid character {invalid!r}; allowed characters are A, C, G, T, and N",
        )
    return sequence


def reverse_complement(sequence: str) -> str:
    """Return the DNA reverse complement in O(n) time and O(n) output space."""
    return "".join(_COMPLEMENT[character] for character in reversed(sequence))
