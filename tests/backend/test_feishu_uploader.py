from pathlib import Path

from backend.services.feishu_uploader import FeishuUploader, parse_bitable_url, parse_row_range


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self.payload


class FakeSession:
    def __init__(self):
        self.updated_fields = []
        self.uploaded_names = []

    def post(self, url, **kwargs):
        if "tenant_access_token" in url:
            return FakeResponse({"code": 0, "tenant_access_token": "tenant-token"})
        if "upload_all" in url:
            file_name = kwargs["data"]["file_name"]
            self.uploaded_names.append(file_name)
            return FakeResponse({"code": 0, "data": {"file_token": f"token-{file_name}"}})
        raise AssertionError(url)

    def get(self, url, **kwargs):
        if url.endswith("/records"):
            return FakeResponse({
                "code": 0,
                "data": {
                    "items": [
                        {"record_id": "rec1"},
                        {"record_id": "rec2"},
                        {"record_id": "rec3"},
                        {"record_id": "rec4"},
                        {"record_id": "rec5"},
                    ],
                    "has_more": False,
                },
            })
        if url.endswith("/fields"):
            return FakeResponse({
                "code": 0,
                "data": {"items": [{"field_name": "图片编辑"}, {"field_name": "视频编辑"}], "has_more": False},
            })
        raise AssertionError(url)

    def put(self, url, **kwargs):
        self.updated_fields.append((url, kwargs["json"]["fields"]))
        return FakeResponse({"code": 0, "data": {}})


def test_parse_row_range_returns_1_based_rows():
    assert parse_row_range("2-5") == [2, 3, 4, 5]


def test_parse_bitable_url_extracts_app_token_and_table_id():
    app_token, table_id = parse_bitable_url("https://example.feishu.cn/base/bascnxxx?table=tblABC&view=vew")

    assert app_token == "bascnxxx"
    assert table_id == "tblABC"


def test_preview_folder_mapping_uses_folder_and_image_order(tmp_path: Path):
    root = tmp_path / "upload"
    (root / "02商品").mkdir(parents=True)
    (root / "01商品").mkdir()
    (root / "01商品" / "2.png").write_bytes(b"2")
    (root / "01商品" / "1.png").write_bytes(b"1")
    (root / "02商品" / "1.png").write_bytes(b"1")

    preview = FeishuUploader().preview_folder_mapping(root, "2-3")

    assert [item["folder_name"] for item in preview["mappings"]] == ["01商品", "02商品"]
    assert preview["mappings"][0]["row_number"] == 2
    assert preview["mappings"][0]["images"] == ["1.png", "2.png"]


def test_upload_by_folders_maps_each_folder_to_one_row(tmp_path: Path):
    root = tmp_path / "upload"
    (root / "01商品").mkdir(parents=True)
    (root / "02商品").mkdir()
    (root / "03多余").mkdir()
    (root / "01商品" / "1.png").write_bytes(b"1")
    (root / "01商品" / "2.png").write_bytes(b"2")
    (root / "02商品" / "1.png").write_bytes(b"1")
    session = FakeSession()

    result = FeishuUploader(session=session).upload_by_folders({
        "app_id": "cli_xxx",
        "app_secret": "secret",
        "bitable_url": "https://example.feishu.cn/base/base123?table=tbl123",
        "field_name": "图片编辑",
        "row_range": "2-3",
        "upload_root": str(root),
    })

    assert result["upload_count"] == 2
    assert result["skipped_folder_count"] == 1
    assert session.uploaded_names == ["1.png", "2.png", "1.png"]
    assert session.updated_fields[0][0].endswith("/records/rec2")
    assert session.updated_fields[0][1] == {
        "图片编辑": [{"file_token": "token-1.png"}, {"file_token": "token-2.png"}]
    }
    assert session.updated_fields[1][0].endswith("/records/rec3")
