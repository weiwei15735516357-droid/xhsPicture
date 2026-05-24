from pydantic import BaseModel, Field


class FeishuSettings(BaseModel):
    app_id: str = ""
    app_secret: str = ""
    bitable_url: str = ""
    table_id: str = ""
    attachment_field_name: str = ""
    row_range: str = ""


class AppSettings(BaseModel):
    backend_port: int = 8787
    recent_project_dir: str | None = None
    office_available: bool | None = None
    default_export_scale: int = Field(default=2, ge=1, le=4)
    default_canvas_ratio: str = "3:4"
    default_export_format: str = "png"
    feishu: FeishuSettings = Field(default_factory=FeishuSettings)


class CreateProjectRequest(BaseModel):
    project_dir: str


class CreateLogRequest(BaseModel):
    level: str
    message: str
    context: dict = Field(default_factory=dict)


class ImportAssetsRequest(BaseModel):
    project_dir: str
    paths: list[str]


class ExportDocumentRequest(BaseModel):
    project_dir: str
    file_path: str
    scale: int = Field(default=2, ge=1, le=4)
    page_start: int | None = None
    page_end: int | None = None
    subfolder_output: bool = True
    summary_group_size: int | None = Field(default=5, ge=5, le=9)
    background_path: str | None = None
    background_has_text: bool = False
