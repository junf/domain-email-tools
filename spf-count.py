# Count the DNS lookups an SPF record needs,
# following include: and redirect=.
# The limit is 10 (RFC 7208 4.6.4).
# Usage: python3 spf-count.py example.com
# To check a record before you set it in DNS,
# give the record as the second argument:
#   python3 spf-count.py example.com "v=spf1 ..."
# Needs the dig command.
import re
import subprocess
import sys

LOOKUP = ("include", "a", "mx", "ptr", "exists")
total = 0
void = 0
errors = 0


def dig(name, rtype):
    try:
        out = subprocess.run(
            ["dig", "+short", rtype, name],
            capture_output=True, text=True,
        ).stdout
    except FileNotFoundError:
        sys.exit("dig not found. Install dig first.")
    return [s for s in out.splitlines() if s]


def spf_of(name):
    found = []
    lines = dig(name, "TXT")
    for line in lines:
        # "v=spf1 ..." "more" -> one string
        parts = re.findall(r'"((?:[^"\\]|\\.)*)"', line)
        s = "".join(parts)
        if s.lower().startswith("v=spf1"):
            found.append(s)
    return found, len(lines)


def check(name, pad, draft=None):
    global total, void, errors
    if draft is not None:
        recs, n = [draft], 1
    else:
        recs, n = spf_of(name)
    if n == 0:
        void += 1
    if len(recs) != 1:
        if not pad and not recs:
            print(name, "has no SPF record")
            sys.exit(1)
        if pad:
            # include: or redirect= target
            errors += 1
        if not recs:
            print(pad + name, "(no SPF record)")
        else:
            print(pad + name, "(more than one SPF)")
        return
    if draft is not None:
        print(name, "(record not in DNS yet)")
    else:
        print(pad + name)
    terms = recs[0].split()[1:]
    has_all = any(t.lstrip("+-~?").lower() == "all"
                  for t in terms)
    for t in terms:
        m = re.match(r"[+\-~?]?([a-z]+)[:=/]?(.*)",
                     t, re.I)
        if not m:
            continue
        key = m.group(1).lower()
        arg = m.group(2)
        if key == "redirect" and has_all:
            continue  # ignored when all is present
        if key not in LOOKUP and key != "redirect":
            continue
        total += 1
        print(pad + str(total).rjust(2), t)
        if "%" in arg:
            print(pad + "   (macro: not followed)")
        elif key in ("include", "redirect"):
            check(arg, pad + "    ")
        elif key in ("a", "mx"):
            target = arg.split("/")[0] or name
            rtype = "A" if key == "a" else "MX"
            if (not dig(target, rtype) and
                    not (key == "a" and
                         dig(target, "AAAA"))):
                void += 1
                print(pad + "   (no record)")


draft = None
if len(sys.argv) > 2:
    draft = sys.argv[2]
    if not draft.lower().startswith("v=spf1"):
        sys.exit("The record must start with v=spf1")
check(sys.argv[1], "", draft)
print()
print("DNS lookups:  ", total, "/ 10")
print("Empty answers:", void, "/ 2")
if errors:
    print("A target is broken: SPF gives permerror")
elif total > 10 or void > 2:
    print("Over the limit: SPF gives permerror")
else:
    print("Within the limit")
