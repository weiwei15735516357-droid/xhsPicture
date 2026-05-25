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


class LayoutSlot(BaseModel):
    x: float = Field(ge=0, le=1)
    y: float = Field(ge=0, le=1)
    width: float = Field(gt=0, le=1)
    height: float = Field(gt=0, le=1)


class ExportDocumentRequest(BaseModel):
    project_dir: str
    file_path: str
    scale: int = Field(default=2, ge=1, le=4)
    page_start: int | None = None
    page_end: int | None = None
    subfolder_output: bool = True
    summary_group_size: int | None = Field(default=5, ge=1, le=30)
    background_path: str | None = None
    custom_layout: list[LayoutSlot] | None = None
    followup_layout: list[LayoutSlot] | None = None


class PerspectivePoint(BaseModel):
    x: float = Field(ge=0, le=1)
    y: float = Field(ge=0, le=1)


class TextOverlayOptions(BaseModel):
    x: int = Field(default=118, ge=0, le=1080)
    y: int = Field(default=386, ge=0, le=1440)
    font_size: int = Field(default=92, ge=16, le=220)
    color: str = "#000000"
    stroke_color: str = "#ffffff"
    stroke_width: int = Field(default=0, ge=0, le=16)
    bold: bool = True


class PerspectiveComposeRequest(BaseModel):
    project_dir: str
    scene_path: str
    mode: str = "image"
    overlay_paths: list[str] = Field(default_factory=list)
    excel_path: str | None = None
    points: list[PerspectivePoint] = Field(default_factory=list)
    opacity: float = Field(default=1.0, ge=0.1, le=1.0)
    shadow: bool = True
    text_options: TextOverlayOptions = Field(default_factory=TextOverlayOptions)
