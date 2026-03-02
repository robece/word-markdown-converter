# ---------------------------------------------------------
# Configuración general
# ---------------------------------------------------------
# Conversión de DOCX a Markdown y registro de encabezados H1.

import subprocess
import re
from pathlib import Path


# ---------------------------------------------------------
# Funciones auxiliares
# ---------------------------------------------------------
def convert(input_file, output_file):
    """
    Convert a DOCX file into a Markdown file using Pandoc.
    """
    cmd = [
        "pandoc",
        input_file,
        "-f", "docx",
        "-t", "gfm",
        "-o", output_file
    ]
    subprocess.run(cmd, check=True)


def extract_headers(md_path):
    """
    Extract all H1 headers (# ...) from the generated Markdown file.
    """
    content = md_path.read_text(encoding="utf-8")
    pattern = r"^#(?!#)\s+(.*)$"
    return re.findall(pattern, content, flags=re.MULTILINE)


def log_headers(headers, log_path):
    """
    Write a numbered list of extracted headers to a log file.
    """
    with open(log_path, "w", encoding="utf-8") as f:
        f.write("Detected H1 headers:\n\n")
        for idx, h in enumerate(headers, start=1):
            f.write(f"{idx}. {h}\n")


# ---------------------------------------------------------
# Proceso principal
# ---------------------------------------------------------
# Conversión del archivo y registro de encabezados.

input_path = Path("/workspace/input/article.docx")
output_path = Path("/workspace/output/article.md")
log_path = Path("/workspace/output/headers.log")

convert(str(input_path), str(output_path))

headers = extract_headers(output_path)
log_headers(headers, log_path)


# ---------------------------------------------------------
# Entry point
# ---------------------------------------------------------
# Mensaje final de confirmación.

print("Conversion completed:", output_path)
print("Headers logged at:", log_path)
