"""Optional RFC 3161 time stamp for an anchor, with a fake stamping server."""

import hashlib
import subprocess
import sys
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

from sovereign_agent_logbook import Event, Logbook
from sovereign_agent_logbook import timestamp as T
from sovereign_agent_logbook.cli import main

der = T._der


def _fake_response(request: bytes, gen_time=b"20261127051000Z") -> bytes:
    """A TimeStampResp (granted, unsigned) that echoes the request's digest and nonce."""
    _, body, _ = T._read(request)
    parts = T._children(body)
    imprint = der(0x30, parts[1][1])
    nonce = der(0x02, parts[2][1])
    tst = der(0x30, der(0x02, b"\x01") + der(0x06, b"\x2a\x03\x04") + imprint
              + der(0x02, b"\x07") + der(0x18, gen_time) + nonce)
    encap = der(0x30, der(0x06, T.TSTINFO_OID) + der(0xA0, der(0x04, tst)))
    signed = der(0x30, der(0x02, b"\x03") + der(0x31, b"") + encap)
    token = der(0x30, der(0x06, bytes.fromhex("2a864886f70d010702")) + der(0xA0, signed))
    return der(0x30, der(0x30, der(0x02, b"\x00")) + token)


@pytest.fixture
def tsa():
    seen = []

    class H(BaseHTTPRequestHandler):
        def do_POST(self):
            data = self.rfile.read(int(self.headers["Content-Length"]))
            seen.append((self.headers["Content-Type"], data))
            out = _fake_response(data)
            self.send_response(200)
            self.send_header("Content-Length", str(len(out)))
            self.end_headers()
            self.wfile.write(out)

        def log_message(self, *a):
            pass

    srv = HTTPServer(("127.0.0.1", 0), H)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{srv.server_port}/tsr", seen
    srv.shutdown()


def _anchor(tmp_path):
    lb = Logbook(tmp_path / "log.jsonl")
    for i in range(2):
        lb.append(Event(agent_id="a", model="m", action=f"s{i}", reason="very-private-reason"))
    anchors = tmp_path / "anchors.jsonl"
    main(["--path", str(lb.path), "anchor", "--to", str(anchors)])
    return lb, anchors


def test_only_the_fingerprint_is_sent_and_token_is_stored(tmp_path, tsa, capsys):
    url, seen = tsa
    lb, anchors = _anchor(tmp_path)
    line = anchors.read_text(encoding="utf-8").splitlines()[-1]
    assert main(["timestamp", "--anchor", str(anchors), "--tsa", url]) == 0
    assert len(seen) == 1
    ctype, sent = seen[0]
    assert ctype == "application/timestamp-query"
    digest = hashlib.sha256(line.encode()).digest()
    assert digest in sent
    # nothing but the request structure and the fingerprint: no log or anchor text
    assert len(sent) < 80
    for text in (b"very-private-reason", b"log.jsonl", b"anchor"):
        assert text not in sent
    token = tmp_path / "anchors.jsonl.1.tsr"
    assert token.exists()
    assert T.parse_response(token.read_bytes())["digest"] == digest
    capsys.readouterr()
    assert main(["timestamp-verify", "--anchor", str(anchors)]) == 0
    assert "stamped 20261127051000Z" in capsys.readouterr().out


def test_changed_anchor_line_fails_verify(tmp_path, tsa, capsys):
    url, _ = tsa
    _, anchors = _anchor(tmp_path)
    main(["timestamp", "--anchor", str(anchors), "--tsa", url])
    text = anchors.read_text(encoding="utf-8")
    anchors.write_text(text.replace('"seq":2', '"seq":1'), encoding="utf-8")
    capsys.readouterr()
    assert main(["timestamp-verify", "--anchor", str(anchors)]) == 1
    assert "changed after it was stamped" in capsys.readouterr().out


def test_verify_without_token_fails(tmp_path, capsys):
    _, anchors = _anchor(tmp_path)
    assert main(["timestamp-verify", "--anchor", str(anchors)]) == 1
    assert "no time stamp token" in capsys.readouterr().out


def test_unreachable_service_is_a_plain_error(tmp_path, capsys):
    _, anchors = _anchor(tmp_path)
    assert main(["timestamp", "--anchor", str(anchors), "--tsa", "http://127.0.0.1:9/x"]) == 1
    assert "could not reach" in capsys.readouterr().out
    assert not list(tmp_path.glob("*.tsr"))


def test_refused_status_is_reported():
    refused = der(0x30, der(0x30, der(0x02, b"\x02")))
    with pytest.raises(T.TimestampError, match="refused"):
        T.parse_response(refused)


def test_request_is_read_by_openssl(tmp_path):
    """openssl itself parses our hand-built request and finds our digest and nonce."""
    import shutil
    if not shutil.which("openssl"):
        pytest.skip("openssl not installed")
    d = hashlib.sha256(b"x").digest()
    f = tmp_path / "req.tsq"
    f.write_bytes(T.build_request(d, 0x1234))
    shown = subprocess.run(
        ["openssl", "ts", "-query", "-in", str(f), "-text"], capture_output=True, check=True
    ).stdout.decode()
    import re
    block = shown.split("Message data:")[1].split("Policy")[0]
    hexdump = "".join(re.findall(r"\b([0-9a-f]{2})\b", "\n".join(
        ln[7:ln.index("  ", 7) if "  " in ln[7:] else None] for ln in block.splitlines() if ln.strip()
    ).replace("-", " ")))
    assert "Hash Algorithm: sha256" in shown
    assert "Nonce: 0x1234" in shown
    assert "Certificate required: yes" in shown
    assert hexdump == d.hex()


def test_timestamp_module_not_loaded_by_core():
    code = (
        "import sys, sovereign_agent_logbook.cli, sovereign_agent_logbook.store;"
        "bad={'sovereign_agent_logbook.timestamp','urllib.request','http.client'}&set(sys.modules);"
        "sys.exit(1 if bad else 0)"
    )
    assert subprocess.run([sys.executable, "-c", code]).returncode == 0
