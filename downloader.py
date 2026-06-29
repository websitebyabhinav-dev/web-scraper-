import os
import requests
from urllib.parse import urlparse

def download_file(url, folder):
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()

        filename = os.path.basename(urlparse(url).path)
        if not filename:
            filename = "file"

        path = os.path.join(folder, filename)

        with open(path, "wb") as f:
            f.write(response.content)

        return path

    except:
        return None