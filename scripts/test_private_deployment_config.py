import re
from pathlib import Path


def test_frontend_nginx_allows_backend_upload_limit():
    nginx_conf = Path("frontend/nginx.conf").read_text(encoding="utf-8")
    match = re.search(r"client_max_body_size\s+(\d+)([mMgG]?)\s*;", nginx_conf)

    assert match, "frontend nginx must set client_max_body_size for document uploads"

    value = int(match.group(1))
    unit = match.group(2).lower()
    bytes_by_unit = {"": 1, "m": 1024 * 1024, "g": 1024 * 1024 * 1024}

    assert value * bytes_by_unit[unit] >= 50 * 1024 * 1024
