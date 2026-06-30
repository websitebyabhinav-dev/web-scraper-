import zipfile
import os
import io


# -----------------------------
# MODE 1: Folder → ZIP (DISK)
# -----------------------------
def create_zip_from_folder(folder_path: str):
    zip_path = folder_path + ".zip"

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(folder_path):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, folder_path)
                zipf.write(file_path, arcname)

    return zip_path


# -----------------------------
# MODE 2: Memory → ZIP (API FAST)
# -----------------------------
def create_zip_in_memory(files: dict):
    """
    files format:
    {
        "page.html": "<html>...</html>",
        "data.json": "{...}",
        "developer.profile.json": "{...}"
    }
    """

    buffer = io.BytesIO()

    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zipf:
        for filename, content in files.items():

            # if content is dict → convert to JSON
            if isinstance(content, dict):
                import json
                content = json.dumps(content, indent=4)

            zipf.writestr(filename, content)

    buffer.seek(0)
    return buffer