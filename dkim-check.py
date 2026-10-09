# Verify the DKIM signatures of a saved message
# (.eml). Shows the body hash (bh=) and the
# signature (b=) separately, and checks that a
# wrong key is rejected (negative control).
#
# Usage:
#   python3 dkim-check.py message.eml
#     -> uses the public key in DNS (needs dig)
#   python3 dkim-check.py message.eml "<p= value>"
#     -> uses the public key you give, before it
#        is set in DNS
# Needs dkimpy.
import base64
import re
import subprocess
import sys

try:
    import dkim
    from dkim.canonicalization import (
        CanonicalizationPolicy)
    from dkim.crypto import HASH_ALGORITHMS
except ImportError:
    sys.exit("dkimpy not found. Install dkimpy first.")

# A 2048-bit public key made only for this test.
# It never matches a real signature.
WRONG_KEY = (
    "MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA"
    "1mwX0Jj9xh4kdpsOuNFbnTSrr5j/Rtkysn45NaF+207b"
    "IIKv6vn1ZyILR1A8iaiDIX6viBnintU8OWASxQ/2Yzyz"
    "HOSb+xIMb7Gvphq0yL9gf+ejvsKAstVbV0uWPZlcN69z"
    "vyne3Kj7S7ePmI7g1aJrq1XaX2eZyDvENxH54OhN6BnI"
    "GTAaEdEMMiAQ8ZBh2oAa15eO5CDgv46wJpCqGopp3aYr"
    "Ung6NbZ778NYifO2Dw7Al8K4tWeP2aHtudHYbx9bZwlm"
    "+ENAEWB41I7UcMPn7wnwsDFXTDXBjDLzoIqfo7TkN4am"
    "e1sppztnC8PlwZxM682PrktFGvDVLQ5AHQIDAQAB"
)

if len(sys.argv) < 2:
    sys.exit("Usage: python3 dkim-check.py "
             "message.eml [\"<p= value>\"]")

with open(sys.argv[1], "rb") as f:
    msg = f.read()


def as_record(key):
    # Accept "p=..." or the whole record too,
    # with or without spaces and line breaks
    key = "".join(key.split()).strip('"')
    if "p=" not in key:
        key = "v=DKIM1;k=rsa;p=" + key
    return key


given = None
if len(sys.argv) > 2:
    given = as_record(sys.argv[2])


def tags(value):
    v = " ".join(value.split())
    return dict(re.findall(r"\b([a-z]+)=([^;]*)", v))


def dig_txt(name):
    try:
        out = subprocess.run(
            ["dig", "+short", "TXT", name],
            capture_output=True, text=True,
        ).stdout
    except FileNotFoundError:
        sys.exit("dig not found. Install dig first.")
    parts = re.findall(r'"((?:[^"\\]|\\.)*)"', out)
    # "..." "..." -> one value
    return "".join(parts)


def body_hash_ok(t):
    # Same calculation as the receiver; the
    # public key is not needed
    c = t.get("c", "simple/simple").strip()
    pol = CanonicalizationPolicy.from_c_value(
        c.encode())
    alg = t.get("a", "rsa-sha256").strip().encode()
    h = HASH_ALGORITHMS[alg]()
    body = pol.canonicalize_body(d.body)
    if "l" in t:
        body = body[:int(t["l"])]
    h.update(body)
    want = "".join(t.get("bh", "").split())
    return base64.b64encode(h.digest()).decode() == want


def key_bits(record):
    try:
        return dkim.evaluate_pk(b"x", record.encode())[1]
    except Exception:
        return None


def sig_ok(i, record):
    # Returns (True/False, problem or "")
    try:
        ok = dkim.DKIM(msg).verify(
            idx=i, dnsfunc=lambda n, timeout=5:
            record.encode())
        return ok, ""
    except dkim.DKIMException as e:
        m = str(e)
        if "x= value is past" in m:
            return False, "signature expired (x=)"
        if "body hash" in m:
            return False, ""
        return False, m


d = dkim.DKIM(msg)
sigs = [v for k, v in d.headers
        if k.lower() == b"dkim-signature"]
if not sigs:
    print("No DKIM-Signature in this message")
    sys.exit(1)

passed = 0
for i, raw in enumerate(sigs):
    t = tags(raw.decode(errors="replace"))
    dom = t.get("d", "?").strip()
    sel = t.get("s", "?").strip()
    c = t.get("c", "simple/simple").strip()
    print("Signature", i + 1)
    print("  d=" + dom, " s=" + sel, " c=" + c)
    problem = ""
    if given is None:
        name = sel + "._domainkey." + dom
        print("  key: DNS " + name)
        record = dig_txt(name)
        if not record:
            problem = "no key in DNS"
        elif not tags(record).get("p", "").strip():
            problem = "p= is empty in DNS: revoked"
    else:
        print("  key: the one you gave")
        record = given
    if not problem:
        bits = key_bits(record)
        if bits:
            print("  key length:", bits, "bit")
    bh = "OK" if body_hash_ok(t) else "NG"
    print("  body hash (bh=):", bh)
    b = "not checked"
    if not problem and bh == "OK":
        ok, problem = sig_ok(i, record)
        if not problem:
            b = "OK" if ok else "NG"
    print("  signature (b=): ", b)
    if problem:
        print("  result: FAIL (" + problem + ")")
    elif bh == "NG":
        # The receiver stops before b= here
        print("  result: FAIL (body changed)")
    elif b == "NG":
        print("  result: FAIL (key or signed "
              "headers differ)")
    else:
        passed += 1
        print("  result: PASS")
        # Negative control: a wrong key must fail
        bad, _ = sig_ok(i, as_record(WRONG_KEY))
        if bad:
            print("  wrong key: OK  <- this check"
                  " is not working")
        else:
            print("  wrong key: NG  (rejected,"
                  " as expected)")
    print()

sys.exit(0 if passed else 1)
