from __future__ import annotations

import re
import bcrypt
import os

MIN_LEN = int(os.getenv("MIN_PASSWORD_LENGTH", "8"))
REQ_UP = os.getenv("REQUIRE_UPPERCASE", "true").lower() == "true"
REQ_LOW = os.getenv("REQUIRE_LOWERCASE", "true").lower() == "true"
REQ_DIG = os.getenv("REQUIRE_DIGITS", "true").lower() == "true"
REQ_SPC = os.getenv("REQUIRE_SPECIAL", "true").lower() == "true"


def validate_password(pw: str) -> tuple[bool, str | None]:
    if len(pw) < MIN_LEN: return False, f"Password must be at least {MIN_LEN} characters"
    if REQ_UP and not re.search(r"[A-Z]", pw): return False, "Password needs an uppercase letter"
    if REQ_LOW and not re.search(r"[a-z]", pw): return False, "Password needs a lowercase letter"
    if REQ_DIG and not re.search(r"\d", pw):   return False, "Password needs a digit"
    if REQ_SPC and not re.search(r"[^\w\s]", pw): return False, "Password needs a special character"
    return True, None


def hash_password(pw: str) -> str:
    return bcrypt.hashpw(pw.encode("utf-8"), bcrypt.gensalt(rounds=12)).decode("utf-8")


def verify_password(pw: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(pw.encode("utf-8"), hashed.encode("utf-8"))
    except Exception:
        return False
