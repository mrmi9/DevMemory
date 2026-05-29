import argparse
import json
import os
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path


def request_json(base_url, path, method="GET", token="", payload=None, headers=None):
    body = None
    request_headers = dict(headers or {})
    if payload is not None:
        body = json.dumps(payload).encode("utf-8")
        request_headers["Content-Type"] = "application/json"
    if token:
        request_headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(f"{base_url}{path}", data=body, method=method, headers=request_headers)
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def upload_file(base_url, course_id, token, path):
    boundary = f"----devmemory{int(time.time() * 1000)}"
    content = Path(path).read_bytes()
    filename = Path(path).name
    parts = [
        f"--{boundary}\r\n".encode("utf-8"),
        f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'.encode("utf-8"),
        b"Content-Type: text/markdown\r\n\r\n",
        content,
        f"\r\n--{boundary}--\r\n".encode("utf-8"),
    ]
    body = b"".join(parts)
    request = urllib.request.Request(
        f"{base_url}/courses/{course_id}/documents",
        data=body,
        method="POST",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": f"multipart/form-data; boundary={boundary}",
        },
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def assert_true(condition, message):
    if not condition:
        raise AssertionError(message)


def main():
    parser = argparse.ArgumentParser(description="Run DevMemory private deployment smoke checks.")
    parser.add_argument("--base-url", default=os.getenv("DEVMEMORY_API_BASE", "http://127.0.0.1:8000/api"))
    parser.add_argument("--username", default=os.getenv("STUDY_DEFAULT_USERNAME", "admin"))
    parser.add_argument("--password", default=os.getenv("STUDY_DEFAULT_PASSWORD", "changeme"))
    parser.add_argument("--timeout-seconds", type=int, default=60)
    args = parser.parse_args()

    course_id = ""
    token = ""
    try:
        login = request_json(
            args.base_url,
            "/auth/login",
            method="POST",
            payload={"username": args.username, "password": args.password},
        )
        token = login["access_token"]

        status = request_json(args.base_url, "/system/status")
        assert_true(status["status"] in {"ok", "degraded"}, "system status did not return a known state")

        course = request_json(
            args.base_url,
            "/courses",
            method="POST",
            token=token,
            payload={
                "title": "DevMemory Smoke Test",
                "description": "Temporary release verification course",
                "color": "#2563eb",
            },
        )
        course_id = course["id"]

        with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False, encoding="utf-8") as handle:
            handle.write(
                "# DevMemory Smoke Test Notes\n\n"
                "SNMP uses managers and agents to collect metrics from network devices.\n"
                "Important review terms include manager, agent, MIB, OID, GET, SET, and TRAP.\n"
            )
            temp_path = handle.name

        try:
            document = upload_file(args.base_url, course_id, token, temp_path)
        finally:
            Path(temp_path).unlink(missing_ok=True)

        document_id = document["id"]
        deadline = time.time() + args.timeout_seconds
        while time.time() < deadline:
            document = request_json(args.base_url, f"/documents/{document_id}", token=token)
            if document["status"] in {"ready", "failed"}:
                break
            time.sleep(1)

        assert_true(document["status"] == "ready", f"document did not become ready: {document}")
        assert_true(document["chunk_count"] > 0, "document did not produce chunks")

        chunks = request_json(args.base_url, f"/documents/{document_id}/chunks", token=token)
        assert_true(len(chunks) > 0, "chunk list is empty")

        chat = request_json(
            args.base_url,
            "/chat",
            method="POST",
            token=token,
            payload={
                "question": "Summarize the SNMP concepts in the uploaded notes.",
                "course_id": course_id,
                "session_id": None,
                "document_ids": [document_id],
            },
        )
        assert_true(chat.get("answer"), "chat did not return an answer")
        assert_true(chat.get("session_id"), "chat did not return a session id")
        assert_true(len(chat.get("citations", [])) > 0, "chat did not return citations")
        assert_true(
            chat.get("retrieval_confidence") in {"high", "medium", "weak", "none"},
            f"chat returned invalid retrieval confidence: {chat.get('retrieval_confidence')}",
        )
        assert_true(isinstance(chat.get("quality_notes"), list), "chat did not return quality notes")

        cards = request_json(
            args.base_url,
            "/study/cards",
            method="POST",
            token=token,
            payload={"topic": "SNMP", "course_id": course_id, "document_ids": [document_id], "count": 2},
        )
        assert_true(cards.get("content"), "card generation returned empty content")

        questions = request_json(
            args.base_url,
            "/study/questions",
            method="POST",
            token=token,
            payload={"topic": "SNMP", "course_id": course_id, "document_ids": [document_id], "count": 2},
        )
        assert_true(questions.get("content"), "question generation returned empty content")

        mindmap = request_json(
            args.base_url,
            "/mindmaps",
            method="POST",
            token=token,
            payload={"topic": "SNMP", "course_id": course_id, "document_ids": [document_id], "count": 1},
        )
        assert_true(mindmap.get("content"), "mindmap generation returned empty content")

        delete = request_json(args.base_url, f"/courses/{course_id}", method="DELETE", token=token)
        assert_true(delete.get("ok") is True, "course delete did not return ok")
        course_id = ""

        remaining = request_json(args.base_url, "/courses", token=token)
        assert_true(not any(course["title"] == "DevMemory Smoke Test" for course in remaining), "smoke course was not cleaned up")

        print(json.dumps({"ok": True, "base_url": args.base_url, "ai_mode": status["ai_mode"]}, ensure_ascii=False))
    except (AssertionError, KeyError, urllib.error.HTTPError, urllib.error.URLError) as exc:
        if course_id and token:
            try:
                request_json(args.base_url, f"/courses/{course_id}", method="DELETE", token=token)
            except Exception:
                pass
        raise SystemExit(f"Smoke test failed: {exc}") from exc


if __name__ == "__main__":
    main()
