import re
import json
import uuid
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlencode, urlparse
from urllib.request import Request, urlopen



IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".gif", ".tif", ".tiff", ".jfif"}
FEISHU_BASE_URL = "https://open.feishu.cn"


class FeishuUploader:
    def __init__(self, session: Any | None = None):
        self.session = session or UrllibSession()

    def preview_folder_mapping(self, upload_root: Path, row_range: str) -> dict[str, Any]:
        row_numbers = parse_row_range(row_range)
        folders = list_child_folders(upload_root)
        mappings = []
        for row_number, folder in zip(row_numbers, folders):
            images = list_images(folder)
            mappings.append({
                "row_number": row_number,
                "folder": str(folder),
                "folder_name": folder.name,
                "image_count": len(images),
                "images": [image.name for image in images],
            })
        return {
            "row_numbers": row_numbers,
            "folder_count": len(folders),
            "upload_count": len(mappings),
            "skipped_folder_count": max(0, len(folders) - len(mappings)),
            "mappings": mappings,
        }

    def test_connection(self, request: dict[str, str]) -> dict[str, Any]:
        token = self._tenant_access_token(request["app_id"], request["app_secret"])
        app_token, table_id = parse_bitable_url(request["bitable_url"])
        fields = self._list_fields(token, app_token, table_id)
        field_names = {field.get("field_name") for field in fields}
        field_name = request.get("field_name") or "图片编辑"
        if field_name not in field_names:
            raise ValueError(f"飞书表格里找不到附件字段：{field_name}")
        records = self._list_records(token, app_token, table_id)
        return {"ok": True, "field_name": field_name, "record_count": len(records)}

    def upload_by_folders(
        self,
        request: dict[str, str],
        progress_callback: Any | None = None,
    ) -> dict[str, Any]:
        token = self._tenant_access_token(request["app_id"], request["app_secret"])
        app_token, table_id = parse_bitable_url(request["bitable_url"])
        field_name = request.get("field_name") or "图片编辑"
        row_numbers = parse_row_range(request["row_range"])
        folders = list_child_folders(Path(request["upload_root"]))
        records = self._list_records(token, app_token, table_id)
        results = []
        total = min(len(row_numbers), len(folders))
        for index, (row_number, folder) in enumerate(zip(row_numbers, folders), start=1):
            if row_number < 1 or row_number > len(records):
                raise ValueError(f"飞书第 {row_number} 行不存在，当前表格只有 {len(records)} 行")
            record_id = records[row_number - 1]["record_id"]
            images = list_images(folder)
            file_tokens = [self._upload_file(token, app_token, image) for image in images]
            self._update_attachment_field(token, app_token, table_id, record_id, field_name, file_tokens)
            result = {
                "row_number": row_number,
                "record_id": record_id,
                "folder": str(folder),
                "folder_name": folder.name,
                "image_count": len(images),
                "images": [image.name for image in images],
            }
            results.append(result)
            if progress_callback:
                progress_callback(index, total, f"正在上传第 {row_number} 行：{folder.name}")
        return {
            "uploaded": results,
            "upload_count": len(results),
            "skipped_folder_count": max(0, len(folders) - len(results)),
            "field_name": field_name,
        }

    def _tenant_access_token(self, app_id: str, app_secret: str) -> str:
        response = self.session.post(
            f"{FEISHU_BASE_URL}/open-apis/auth/v3/tenant_access_token/internal",
            json={"app_id": app_id, "app_secret": app_secret},
            timeout=30,
        )
        data = _json(response)
        token = data.get("tenant_access_token")
        if not token:
            raise ValueError(data.get("msg") or "获取飞书 tenant_access_token 失败")
        return token

    def _list_records(self, token: str, app_token: str, table_id: str) -> list[dict[str, Any]]:
        records: list[dict[str, Any]] = []
        page_token = ""
        while True:
            params = {"page_size": 500}
            if page_token:
                params["page_token"] = page_token
            response = self.session.get(
                f"{FEISHU_BASE_URL}/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records",
                headers=_headers(token),
                params=params,
                timeout=30,
            )
            data = _json(response).get("data", {})
            records.extend(data.get("items", []))
            if not data.get("has_more"):
                break
            page_token = data.get("page_token", "")
        return records

    def _list_fields(self, token: str, app_token: str, table_id: str) -> list[dict[str, Any]]:
        fields: list[dict[str, Any]] = []
        page_token = ""
        while True:
            params = {"page_size": 100}
            if page_token:
                params["page_token"] = page_token
            response = self.session.get(
                f"{FEISHU_BASE_URL}/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/fields",
                headers=_headers(token),
                params=params,
                timeout=30,
            )
            data = _json(response).get("data", {})
            fields.extend(data.get("items", []))
            if not data.get("has_more"):
                break
            page_token = data.get("page_token", "")
        return fields

    def _upload_file(self, token: str, app_token: str, image: Path) -> str:
        with image.open("rb") as file:
            response = self.session.post(
                f"{FEISHU_BASE_URL}/open-apis/drive/v1/medias/upload_all",
                headers={"Authorization": f"Bearer {token}"},
                data={
                    "file_name": image.name,
                    "parent_type": "bitable_file",
                    "parent_node": app_token,
                    "size": str(image.stat().st_size),
                },
                files={"file": (image.name, file)},
                timeout=120,
            )
        data = _json(response).get("data", {})
        file_token = data.get("file_token")
        if not file_token:
            raise ValueError(f"上传附件失败：{image.name}")
        return file_token

    def _update_attachment_field(
        self,
        token: str,
        app_token: str,
        table_id: str,
        record_id: str,
        field_name: str,
        file_tokens: list[str],
    ) -> None:
        response = self.session.put(
            f"{FEISHU_BASE_URL}/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records/{record_id}",
            headers=_headers(token),
            json={"fields": {field_name: [{"file_token": file_token} for file_token in file_tokens]}},
            timeout=30,
        )
        _json(response)


def parse_row_range(value: str) -> list[int]:
    single = re.fullmatch(r"\s*(\d+)\s*", value or "")
    if single:
        row = int(single.group(1))
        if row < 1:
            raise ValueError("行号必须大于等于 1")
        return [row]
    match = re.fullmatch(r"\s*(\d+)\s*-\s*(\d+)\s*", value or "")
    if not match:
        raise ValueError("行范围格式应为 2-5")
    start = int(match.group(1))
    end = int(match.group(2))
    if start < 1 or end < start:
        raise ValueError("行范围无效，结束行必须大于等于开始行")
    return list(range(start, end + 1))


def parse_bitable_url(value: str) -> tuple[str, str]:
    parsed = urlparse(value)
    query = parse_qs(parsed.query)
    table_id = (query.get("table") or query.get("table_id") or [""])[0]
    path_parts = [part for part in parsed.path.split("/") if part]
    app_token = ""
    for marker in ("base", "bitable"):
        if marker in path_parts:
            index = path_parts.index(marker)
            if index + 1 < len(path_parts):
                app_token = path_parts[index + 1]
                break
    if not app_token and path_parts:
        app_token = path_parts[-1]
    if not app_token:
        raise ValueError("无法从多维表格链接解析 app_token")
    if not table_id:
        raise ValueError("无法从多维表格链接解析 table 参数，请复制打开具体数据表后的链接")
    return app_token, table_id


def list_child_folders(upload_root: Path) -> list[Path]:
    if not upload_root.exists() or not upload_root.is_dir():
        raise ValueError(f"上传总文件夹不存在：{upload_root}")
    return sorted(
        [item for item in upload_root.iterdir() if item.is_dir()],
        key=lambda path: natural_key(path.name),
    )


def list_images(folder: Path) -> list[Path]:
    return sorted(
        [item for item in folder.iterdir() if item.is_file() and item.suffix.lower() in IMAGE_EXTENSIONS],
        key=lambda path: natural_key(path.name),
    )


def natural_key(value: str) -> list[Any]:
    return [int(part) if part.isdigit() else part.casefold() for part in re.split(r"(\d+)", value)]


def _headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json; charset=utf-8"}


def _json(response: Any) -> dict[str, Any]:
    response.raise_for_status()
    data = response.json()
    if data.get("code", 0) != 0:
        raise ValueError(data.get("msg") or f"飞书接口错误：{data.get('code')}")
    return data


class UrllibResponse:
    def __init__(self, status: int, payload: bytes):
        self.status = status
        self.payload = payload

    def raise_for_status(self) -> None:
        if self.status >= 400:
            raise ValueError(f"HTTP {self.status}: {self.payload.decode('utf-8', errors='ignore')}")

    def json(self) -> dict[str, Any]:
        return json.loads(self.payload.decode("utf-8"))


class UrllibSession:
    def get(self, url: str, **kwargs: Any) -> UrllibResponse:
        params = kwargs.get("params") or {}
        if params:
            url = f"{url}?{urlencode(params)}"
        return self._request("GET", url, headers=kwargs.get("headers") or {})

    def put(self, url: str, **kwargs: Any) -> UrllibResponse:
        return self._request("PUT", url, json_body=kwargs.get("json"), headers=kwargs.get("headers") or {})

    def post(self, url: str, **kwargs: Any) -> UrllibResponse:
        if kwargs.get("files"):
            return self._multipart_post(url, kwargs)
        return self._request("POST", url, json_body=kwargs.get("json"), headers=kwargs.get("headers") or {})

    def _request(
        self,
        method: str,
        url: str,
        json_body: Any | None = None,
        headers: dict[str, str] | None = None,
    ) -> UrllibResponse:
        body = None
        request_headers = dict(headers or {})
        if json_body is not None:
            body = json.dumps(json_body).encode("utf-8")
            request_headers.setdefault("Content-Type", "application/json; charset=utf-8")
        with urlopen(Request(url, data=body, headers=request_headers, method=method), timeout=120) as response:
            return UrllibResponse(response.status, response.read())

    def _multipart_post(self, url: str, kwargs: dict[str, Any]) -> UrllibResponse:
        boundary = f"----xhs-{uuid.uuid4().hex}"
        parts: list[bytes] = []
        for key, value in (kwargs.get("data") or {}).items():
            parts.extend([
                f"--{boundary}\r\n".encode("utf-8"),
                f'Content-Disposition: form-data; name="{key}"\r\n\r\n'.encode("utf-8"),
                str(value).encode("utf-8"),
                b"\r\n",
            ])
        for key, file_value in kwargs["files"].items():
            filename, file_obj = file_value
            content = file_obj.read()
            parts.extend([
                f"--{boundary}\r\n".encode("utf-8"),
                f'Content-Disposition: form-data; name="{key}"; filename="{filename}"\r\n'.encode("utf-8"),
                b"Content-Type: application/octet-stream\r\n\r\n",
                content,
                b"\r\n",
            ])
        parts.append(f"--{boundary}--\r\n".encode("utf-8"))
        headers = dict(kwargs.get("headers") or {})
        headers["Content-Type"] = f"multipart/form-data; boundary={boundary}"
        with urlopen(Request(url, data=b"".join(parts), headers=headers, method="POST"), timeout=120) as response:
            return UrllibResponse(response.status, response.read())
