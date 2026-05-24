from pathlib import Path


WORD_EXTENSIONS = {".doc", ".docx"}
POWERPOINT_EXTENSIONS = {".ppt", ".pptx"}


class OfficeConverter:
    def is_available(self) -> bool:
        try:
            import win32com.client  # noqa: F401
        except ImportError:
            return False
        return True

    def convert_to_pdf(self, file_path: Path, output_dir: Path) -> Path:
        if not self.is_available():
            raise RuntimeError("Microsoft Office 或 pywin32 不可用，无法转换 Word/PPT。")

        import pythoncom

        suffix = file_path.suffix.lower()
        output_dir.mkdir(parents=True, exist_ok=True)
        output_pdf = output_dir / f"{file_path.stem}.pdf"
        pythoncom.CoInitialize()
        try:
            if suffix in WORD_EXTENSIONS:
                self._convert_word(file_path, output_pdf)
                return output_pdf
            if suffix in POWERPOINT_EXTENSIONS:
                self._convert_powerpoint(file_path, output_pdf)
                return output_pdf
        finally:
            pythoncom.CoUninitialize()
        raise ValueError(f"不支持的 Office 文档格式：{suffix}")

    def _convert_word(self, file_path: Path, output_pdf: Path) -> None:
        import win32com.client

        word = win32com.client.DispatchEx("Word.Application")
        word.Visible = False
        document = None
        try:
            document = word.Documents.Open(str(file_path))
            document.SaveAs(str(output_pdf), FileFormat=17)
        finally:
            if document is not None:
                document.Close(False)
            word.Quit()

    def _convert_powerpoint(self, file_path: Path, output_pdf: Path) -> None:
        import win32com.client

        powerpoint = win32com.client.DispatchEx("PowerPoint.Application")
        presentation = None
        try:
            presentation = powerpoint.Presentations.Open(str(file_path), WithWindow=False)
            presentation.SaveAs(str(output_pdf), 32)
        finally:
            if presentation is not None:
                presentation.Close()
            powerpoint.Quit()
