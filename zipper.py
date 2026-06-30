import io
import json
import zipfile

class ZipBuilder:
    def __init__(self):
        self.buffer = io.BytesIO()
        self.zip = zipfile.ZipFile(self.buffer, "w", zipfile.ZIP_DEFLATED)

    def add_text(self, filename, data: str):
        self.zip.writestr(filename, data)

    def add_json(self, filename, data):
        self.zip.writestr(filename, json.dumps(data, indent=4))

    def close(self):
        self.zip.close()
        self.buffer.seek(0)
        return self.buffer