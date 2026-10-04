# Show only the header lines that matter for
# SPF / DKIM / DMARC, from a saved message (.eml).
# Usage: python3 headers.py message.eml
import email
import re
import sys
from email.utils import parseaddr

with open(sys.argv[1], "rb") as f:
    msg = email.message_from_binary_file(f)


def one(v):
    # Unfold a folded header into one line
    return " ".join(str(v).split())


def addr(name):
    v = msg.get(name)
    if v is None:
        return "(none)"
    return parseaddr(one(v))[1] or one(v)


print("From:           ", addr("From"))
print("Return-Path:    ", addr("Return-Path"))

for sig in msg.get_all("DKIM-Signature") or []:
    pat = r"\b([ds])=([^;\s]+)"
    tags = dict(re.findall(pat, one(sig)))
    d = tags.get("d", "?")
    sel = tags.get("s", "?")
    print("DKIM-Signature:  d=" + d, "s=" + sel)

n = len(msg.get_all("Received") or [])
print("Received:       ", n)

ar = msg.get_all("Authentication-Results")
print()
if not ar:
    print("Authentication-Results: (none)")
    sys.exit()
# The topmost one is from the last server
# that received the message
v = re.sub(r"\([^)]*\)", "", one(ar[0]))
parts = [p.strip() for p in v.split(";")]
if "=" in parts[0]:
    # Microsoft omits the server name
    print("Authentication-Results")
else:
    print("Authentication-Results",
          "(" + parts.pop(0) + ")")
for p in parts:
    m = re.match(r"(spf|dkim|dmarc)=(\S+)", p)
    if not m:
        continue
    keys = re.findall(
        r"(?:smtp\.mailfrom|header\.\w+)=\S+", p
    )
    keys = [k for k in keys
            if not k.startswith("header.b=")]
    print(" ", m.group(1).ljust(5),
          m.group(2).ljust(5), " ".join(keys))
