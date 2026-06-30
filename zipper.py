import zipfile
import io
import json

class ZipBuilder:
    def __init__(self):
        """
        Initializes an isolated, in-memory ZIP archive stream pipeline.
        Avoids reading/writing files to disk for fast API streaming delivery.
        """
        self.buffer = io.BytesIO()
        self.zipf = zipfile.ZipFile(self.buffer, "w", zipfile.ZIP_DEFLATED)

    def add_text(self, filename: str, content: str):
        """
        Writes structured layout text assets (HTML, CSS, JS, TXT) 
        directly into the archive.
        """
        self.zipf.writestr(filename, content)

    def add_json(self, filename: str, data: dict):
        """
        Serializes a Python dictionary to a pretty-printed JSON string 
        and saves it into the archive structure.
        """
        json_content = json.dumps(data, indent=4, ensure_ascii=False)
        self.zipf.writestr(filename, json_content)

    def add_bytes(self, filename: str, content: bytes):
        """
        Writes raw binary asset data streams (PNG, JPG, WEBP, ICO, etc.) 
        directly into the archive layer. This prevents encoding or 
        string conversion corruption from breaking downloaded images.
        """
        self.zipf.writestr(filename, content)

    def close(self) -> io.BytesIO:
        """
        Finalizes the ZIP archive write headers, seals the wrapper container, 
        and resets the inner pointer to byte zero for immediate FastAPI 
        StreamingResponse execution.
        """
        self.zipf.close()
        self.buffer.seek(0)
        return self.buffer
