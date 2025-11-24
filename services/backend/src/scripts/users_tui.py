#!/usr/bin/env python3
import os, sys, getpass, shutil, time
from datetime import datetime
from typing import Optional

from src.auth.session_manager import Sessions
from src.auth.passwords import validate_password, hash_password

# RUN "python -m src.scripts.users_tui" inside running container as admin to manage users.
# ---------- UI helpers ----------
def _supports_color() -> bool:
    return sys.stdout.isatty() and not os.environ.get("NO_COLOR")


C = _supports_color()


def c(s, code):
    if not C: return s
    colors = {
        "ok": "\033[32m", "warn": "\033[33m", "err": "\033[31m",
        "info": "\033[36m", "bold": "\033[1m", "dim": "\033[2m", "r": "\033[0m"
    }
    return f"{colors.get(code, '')}{s}{colors['r']}"


def clear():
    if sys.stdout.isatty():
        os.system("clear" if os.name != "nt" else "cls")


def pause(msg="Press Enter to continue…"):
    try:
        input(c(msg, "dim"))
    except EOFError:
        pass


def line(ch="─"):
    w = shutil.get_terminal_size((100, 20)).columns
    return ch * max(20, min(w, 120))


def header(title):
    clear()
    print(c(title, "bold"))
    print(c(line(), "dim"))


def table(rows, headers):
    if not rows:
        print(c("No users found.", "dim"))
        return
    widths = [len(h) for h in headers]
    for r in rows:
        for i, cell in enumerate(r):
            widths[i] = max(widths[i], len(str(cell)))
    fmt = "  ".join("{:" + str(w) + "}" for w in widths)
    print(c(fmt.format(*headers), "bold"))
    print(c(line(), "dim"))
    for r in rows:
        print(fmt.format(*[str(x) for x in r]))


def prompt_bool(label, default: Optional[bool] = None) -> bool:
    d = " [Y/n]" if default is True else (" [y/N]" if default is False else " [y/n]")
    while True:
        try:
            s = input(c(f"{label}{d}: ", "bold")).strip().lower()
        except EOFError:
            return bool(default)
        if not s and default is not None:
            return default
        if s in ("y", "yes"): return True
        if s in ("n", "no"): return False
        print(c("Please answer y/n.", "warn"))


def prompt_str(label, default: Optional[str] = None, allow_empty=False) -> str:
    suffix = f" [{default}]" if default else ""
    while True:
        try:
            s = input(c(f"{label}{suffix}: ", "bold"))
        except EOFError:
            return default or ""
        if s == "" and default is not None:
            return default
        if s == "" and not allow_empty:
            print(c("Value cannot be empty.", "warn"));
            continue
        return s


def prompt_password(twice=True) -> str:
    if not sys.stdin.isatty():
        raise RuntimeError("TTY required for password prompt.")
    p1 = getpass.getpass("New password: ")
    if twice:
        p2 = getpass.getpass("Repeat password: ")
        if p1 != p2:
            raise ValueError("Passwords do not match.")
    ok, err = validate_password(p1)
    if not ok:
        raise ValueError(f"Invalid password: {err}")
    return p1


# ---------- Sessions helpers ----------
def normalize_users():
    out = []
    for u in Sessions.list_users():
        if isinstance(u, dict):
            out.append({
                "username": u.get("username") or u.get("user"),
                "full_name": u.get("full_name") or "",
                "is_admin": bool(u.get("is_admin", False)),
                "is_active": bool(u.get("is_active", True)),
                "created_at": u.get("created_at") or "-",
                "last_login": u.get("last_login") or "-",
            })
        else:
            out.append({
                "username": str(u), "full_name": "", "is_admin": False,
                "is_active": True, "created_at": "-", "last_login": "-",
            })
    return out


# ---------- Actions ----------
def action_list():
    header("Users · List")
    users = normalize_users()
    rows = []
    for u in users:
        rows.append([
            u["username"], u["full_name"] or "-",
            "yes" if u["is_admin"] else "no",
            "active" if u["is_active"] else "inactive",
            u["created_at"], u["last_login"],
        ])
    table(rows, headers=["Username", "Name", "Admin", "Status", "Created", "Last login"])
    pause()


def action_create():
    header("Users · Create")
    username = prompt_str("Username")
    if Sessions.user_exists(username):
        print(c("User already exists.", "err"));
        pause();
        return
    fullname = prompt_str("Full name", allow_empty=True)
    admin = prompt_bool("Is admin?", False)
    active = prompt_bool("Active?", True)
    try:
        pwd = prompt_password(twice=True)
    except Exception as e:
        print(c(str(e), "err"));
        pause();
        return
    Sessions.create_user(username, hash_password(pwd), fullname, admin, active)
    print(c(f"✔ Created '{username}'", "ok"))
    pause()


def action_delete():
    header("Users · Delete")
    username = prompt_str("Username")
    if not Sessions.user_exists(username):
        print(c("User not found.", "err"));
        pause();
        return
    print(c("Danger: this permanently deletes the user and sessions.", "warn"))
    typed = prompt_str(f"Type the username '{username}' to confirm", allow_empty=False)
    if typed != username:
        print(c("Confirmation mismatch. Aborted.", "warn"));
        pause();
        return
    Sessions.delete_user(username)
    print(c(f"✔ Deleted '{username}'", "ok"))
    pause()


def action_update():
    header("Users · Update")
    username = prompt_str("Username")
    if not Sessions.user_exists(username):
        print(c("User not found.", "err"));
        pause();
        return
    # Select which fields
    if prompt_bool("Change full name?", False):
        name = prompt_str("New full name", allow_empty=True)
    else:
        name = None
    if prompt_bool("Change admin flag?", False):
        admin = prompt_bool("Is admin now?", None)
    else:
        admin = None
    if prompt_bool("Change active flag?", False):
        active = prompt_bool("Is active now?", None)
    else:
        active = None
    change_pwd = prompt_bool("Change password?", False)
    fields = {}
    if name is not None: fields["full_name"] = name
    if admin is not None: fields["is_admin"] = bool(admin)
    if active is not None: fields["is_active"] = bool(active)
    if change_pwd:
        try:
            pwd = prompt_password(twice=True)
        except Exception as e:
            print(c(str(e), "err"));
            pause();
            return
        fields["hashed_password"] = hash_password(pwd)
    if not fields:
        print(c("No changes selected.", "warn"));
        pause();
        return
    print(c("Changes to apply:", "info"))
    for k, v in fields.items():
        print(f"  - {k}: {'<changed>' if k == 'hashed_password' else v}")
    if not prompt_bool("Apply?"):
        print(c("Aborted.", "warn"));
        pause();
        return
    Sessions.update_user(username, **fields)
    print(c(f"✔ Updated '{username}'", "ok"))
    pause()


# ---------- Main menu ----------
MENU = [
    ("List users", action_list),
    ("Create user", action_create),
    ("Update user", action_update),
    ("Delete user", action_delete),
    ("Exit", None),
]


def menu_loop():
    while True:
        header("User Management Console (dev)")
        for i, (title, _) in enumerate(MENU, start=1):
            print(f"[{i}] {title}")
        print()
        try:
            choice = input(c("Select option: ", "bold")).strip()
        except EOFError:
            print();
            return
        if not choice.isdigit():
            print(c("Enter a number.", "warn"));
            time.sleep(0.9);
            continue
        idx = int(choice) - 1
        if idx < 0 or idx >= len(MENU):
            print(c("Invalid option.", "warn"));
            time.sleep(0.9);
            continue
        title, action = MENU[idx]
        if action is None:
            header("Goodbye");
            return
        action()


def main():
    if not sys.stdin.isatty() or not sys.stdout.isatty():
        print("This console requires an interactive TTY.", file=sys.stderr)
        sys.exit(2)
    menu_loop()


if __name__ == "__main__":
    main()
