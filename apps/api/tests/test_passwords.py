"""Argon2id hashing helpers."""

from __future__ import annotations

from ozzb2b_api.security.passwords import hash_password, verify_password


def test_hash_is_salted() -> None:
    a = hash_password("correct-horse-battery-staple")
    b = hash_password("correct-horse-battery-staple")
    assert a != b, "Argon2id must produce a fresh salt per hash"


def test_verify_accepts_correct_password() -> None:
    h = hash_password("p@ssw0rd-long-enough")
    assert verify_password("p@ssw0rd-long-enough", h) is True


def test_verify_rejects_wrong_password() -> None:
    h = hash_password("p@ssw0rd-long-enough")
    assert verify_password("wrong", h) is False


def test_hash_looks_like_argon2id() -> None:
    h = hash_password("whatever-long-enough")
    assert h.startswith("$argon2id$"), h
