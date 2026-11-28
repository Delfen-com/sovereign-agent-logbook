"""Optional time stamp for an anchor (RFC 3161). Not part of the logbook core.

A time stamping authority (TSA) signs "this fingerprint existed at this time".
`logbook timestamp` sends the SHA-256 of the last anchor line, and nothing
else, to a TSA you name, and keeps the signed answer in a file next to the
anchor file. `logbook timestamp-verify` checks that the stored answer still
belongs to that anchor line.

This module uses only the standard library and is imported only when one of
the two commands runs, so the core (chain, store, cli) never loads an HTTP
client. It talks to the network only inside `request_token`, to the URL you
pass.

What the check does: it proves the stored token covers the current anchor
line. It does not check the TSA's signature; `openssl ts -verify` does that
(see README). A free TSA gives a trustworthy time, not the legal "qualified"
status under eIDAS; that needs a qualified provider.
"""

from __future__ import annotations

import hashlib
import secrets
from pathlib import Path

SHA256_OID = bytes.fromhex("608648016503040201")  # 2.16.840.1.101.3.4.2.1
TSTINFO_OID = bytes.fromhex("2a864886f70d0109100104")  # 1.2.840.113549.1.9.16.1.4


class TimestampError(Exception):
    """A plain-English reason the stamp could not be made or checked."""


# --- minimal DER writer / reader -------------------------------------------

def _der(tag: int, body: bytes) -> bytes:
    n = len(body)
    if n < 128:
        length = bytes([n])
    else:
        raw = n.to_bytes((n.bit_length() + 7) // 8, "big")
        length = bytes([0x80 | len(raw)]) + raw
    return bytes([tag]) + length + body


def _read(buf: bytes, pos: int = 0) -> tuple[int, bytes, int]:
    """Return (tag, body, next position) of the DER element at pos."""
    try:
        tag = buf[pos]
        first = buf[pos + 1]
        pos += 2
        if first < 128:
            n = first
        else:
            k = first & 0x7F
            n = int.from_bytes(buf[pos:pos + k], "big")
            pos += k
        if pos + n > len(buf):
            raise IndexError
        return tag, buf[pos:pos + n], pos + n
    except IndexError:
        raise TimestampError("the answer is not a valid time stamp (cut off)") from None


def _children(body: bytes) -> list[tuple[int, bytes]]:
    out, pos = [], 0
    while pos < len(body):
        tag, inner, pos = _read(body, pos)
        out.append((tag, inner))
    return out


# --- request and response ---------------------------------------------------

def digest_of_line(line: str) -> bytes:
    """SHA-256 of the anchor line (without the trailing newline)."""
    return hashlib.sha256(line.rstrip("\r\n").encode("utf-8")).digest()


def build_request(digest: bytes, nonce: int) -> bytes:
    """A TimeStampReq for a SHA-256 digest: version 1, nonce, certReq true."""
    algo = _der(0x30, _der(0x06, SHA256_OID) + _der(0x05, b""))
    imprint = _der(0x30, algo + _der(0x04, digest))
    nonce_bytes = nonce.to_bytes(nonce.bit_length() // 8 + 1, "big")  # minimal, positive
    return _der(0x30, _der(0x02, b"\x01") + imprint + _der(0x02, nonce_bytes) + _der(0x01, b"\xff"))


def parse_response(data: bytes) -> dict:
    """Read a TimeStampResp. Returns digest (bytes), nonce (int or None), gen_time (str).

    Raises TimestampError if the service refused or the answer is malformed.
    """
    tag, resp, _ = _read(data)
    if tag != 0x30:
        raise TimestampError("the answer is not a time stamp response")
    parts = _children(resp)
    if not parts or parts[0][0] != 0x30:
        raise TimestampError("the answer is not a time stamp response")
    status_fields = _children(parts[0][1])
    status = int.from_bytes(status_fields[0][1], "big") if status_fields else -1
    if status not in (0, 1):
        raise TimestampError(f"the time stamp service refused the request (status {status})")
    if len(parts) < 2:
        raise TimestampError("the answer holds no time stamp token")
    try:
        content = _children(parts[1][1])  # ContentInfo: OID, [0] SignedData
        signed = _children(_children(content[1][1])[0][1])  # SignedData fields
        encap = _children(next(b for t, b in signed if t == 0x30 and TSTINFO_OID in b[:16]))
        octets = _children(encap[1][1])[0][1]  # OCTET STRING holding TSTInfo
        _, tst_body, _ = _read(octets)
        tst = _children(tst_body)
        imprint = _children(tst[2][1])
        digest = imprint[1][1]
        gen_time = tst[4][1].decode("ascii")
        nonce = None
        for t, b in tst[5:]:
            if t == 0x02:
                nonce = int.from_bytes(b, "big")
    except (IndexError, StopIteration, UnicodeDecodeError):
        raise TimestampError("could not read the time stamp token") from None
    return {"digest": digest, "nonce": nonce, "gen_time": gen_time}


def request_token(url: str, digest: bytes, timeout: float = 30.0) -> bytes:
    """Send one request to the TSA at url and return the raw answer.

    The only network call in the package. Only the digest leaves the machine.
    """
    import urllib.error
    import urllib.request

    if not url.lower().startswith(("http://", "https://")):
        raise TimestampError("--tsa must be an http:// or https:// address")
    nonce = secrets.randbits(63)
    req = urllib.request.Request(
        url,
        data=build_request(digest, nonce),
        headers={"Content-Type": "application/timestamp-query"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310
            answer = resp.read()
    except (urllib.error.URLError, OSError) as exc:
        raise TimestampError(f"could not reach the time stamp service: {exc}") from None
    info = parse_response(answer)
    if info["digest"] != digest:
        raise TimestampError("the service stamped a different fingerprint than the one sent")
    if info["nonce"] != nonce:
        raise TimestampError("the answer does not match this request (wrong nonce)")
    return answer


# --- files next to the anchor file -----------------------------------------

def last_anchor_line(anchor_path: Path) -> tuple[int, str]:
    """(line number, text) of the last non-empty line of the anchor file."""
    if not anchor_path.exists():
        raise TimestampError(f"anchor file not found: {anchor_path}")
    last = None
    for no, line in enumerate(anchor_path.read_text(encoding="utf-8").splitlines(), 1):
        if line.strip():
            last = (no, line)
    if last is None:
        raise TimestampError(f"anchor file is empty: {anchor_path}")
    return last


def token_path(anchor_path: Path, lineno: int) -> Path:
    return anchor_path.with_name(f"{anchor_path.name}.{lineno}.tsr")


def stamp(anchor_path: Path, tsa_url: str) -> Path:
    """Stamp the last anchor line; write the token next to the anchor file."""
    lineno, line = last_anchor_line(anchor_path)
    token = request_token(tsa_url, digest_of_line(line))
    out = token_path(anchor_path, lineno)
    out.write_bytes(token)
    return out


def check(anchor_path: Path) -> tuple[bool, str]:
    """Does the stored token cover the last anchor line as it is now?"""
    lineno, line = last_anchor_line(anchor_path)
    tok = token_path(anchor_path, lineno)
    if not tok.exists():
        return False, f"no time stamp token for anchor line {lineno} (expected {tok.name})"
    info = parse_response(tok.read_bytes())
    if info["digest"] != digest_of_line(line):
        return False, f"anchor line {lineno} was changed after it was stamped"
    return True, f"anchor line {lineno} matches the token, stamped {info['gen_time']}"
