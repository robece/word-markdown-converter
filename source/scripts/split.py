import re
import requests
import argparse
from pathlib import Path
from datetime import datetime

INPUT_MD = Path("/workspace/output/article.md")
OUTPUT_DIR = Path("/workspace/output/articles")
README_PATH = Path("/workspace/output/README.md")
LOG_PATH = Path("/workspace/output/split.log")

OLLAMA_URL = "http://ollama:11434/api/generate"


# ---------------------------------------------------------
# Funciones auxiliares
# ---------------------------------------------------------
def log(msg):
    """Append a timestamped message to the log file."""
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(f"[{datetime.now()}] {msg}\n")


def parse_section_list(value: str):
    """Parse a comma-separated list or a range (e.g., '4-25')."""
    result = set()
    parts = value.split(",")

    for part in parts:
        if "-" in part:
            start, end = part.split("-")
            result.update(range(int(start), int(end) + 1))
        else:
            result.add(int(part))

    return sorted(result)


def _truncate_slug_preserving_words(slug: str, max_len: int = 25) -> str:
    """Truncate a slug while preserving meaningful words."""
    parts = [p for p in slug.split("-") if len(p) > 3]
    if not parts:
        return slug[:max_len].rstrip("-")

    cleaned = "-".join(parts)
    if len(cleaned) <= max_len:
        return cleaned

    kept = []
    current_len = 0
    for part in parts:
        extra = len(part) if not kept else len(part) + 1
        if current_len + extra <= max_len:
            kept.append(part)
            current_len += extra
        else:
            break

    if not kept:
        return cleaned[:max_len].rstrip("-")

    return "-".join(kept)


def ask_ollama_for_filename(title):
    """Request a short, clean filename from Ollama based on a section title."""
    log(f"Generating filename for title: '{title}'")

    prompt = f"""
Generate a short, clean, lowercase, hyphenated filename (max 25 chars) based on this title:

"{title}"

Rules:
- No numbers.
- No special characters except hyphens.
- Only lowercase letters and hyphens.
- Remove words of 1, 2, or 3 letters.
- Must be meaningful and related to the title.
- Do NOT include the extension.
- Max 25 characters.
"""

    try:
        response = requests.post(
            OLLAMA_URL,
            json={"model": "qwen2.5:7b", "prompt": prompt, "stream": False},
            timeout=60
        )
        raw = response.json().get("response", "").strip() if response.status_code == 200 else ""
        log(f"Ollama raw response: '{raw}'")
    except Exception as e:
        log(f"ERROR contacting Ollama: {e}")
        raw = ""

    cleaned = re.sub(r"[^a-z\-]", "", raw.lower()).strip("-")
    cleaned = _truncate_slug_preserving_words(cleaned, max_len=25)

    if not cleaned:
        fallback = re.sub(r"[^a-z\-]", "", title.lower().replace(" ", "-")).strip("-")
        cleaned = _truncate_slug_preserving_words(fallback, max_len=25)
        log(f"Ollama returned empty → fallback slug: '{cleaned}'")

    if not cleaned:
        cleaned = "section"
        log("Fallback slug empty → using 'section'")

    log(f"Final cleaned filename: '{cleaned}'")
    return cleaned


def print_progress(current, total):
    """Print a simple progress bar for section processing."""
    if total <= 0:
        return
    width = 30
    ratio = current / total
    done = int(ratio * width)
    bar = "#" * done + "-" * (width - done)
    print(f"\rProcessing sections: [{bar}] {current}/{total}", end="", flush=True)


# ---------------------------------------------------------
# Proceso principal
# ---------------------------------------------------------
def split_articles(in_readme, article_sections):
    log("=== SPLIT PROCESS STARTED ===")

    if not INPUT_MD.exists():
        log("ERROR: Input Markdown file not found.")
        return [], {}, ""

    content = INPUT_MD.read_text(encoding="utf-8")

    pattern = r"^#(?!#)\s*(.*?)\s*(?:\{.*?\})?$"
    matches = list(re.finditer(pattern, content, flags=re.MULTILINE))

    if len(matches) < 2:
        log("ERROR: Document must contain at least 2 H1 headers.")
        return [], {}, ""

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    readme_sections = {}
    articles = []

    total_sections = len(article_sections)
    processed_count = 0

    for idx, match in enumerate(matches, start=1):
        section_title = match.group(1).strip()
        start = match.end()
        end = matches[idx].start() if idx < len(matches) else len(content)
        body = content[start:end].strip()

        # Ahora la sección 1 también entra en el README
        if idx in in_readme:
            readme_sections[idx] = (section_title, body)

        # Artículos (sección 1 nunca entra aquí)
        if idx in article_sections:
            processed_count += 1
            print_progress(processed_count, total_sections)

            log(f"\n--- Processing article section {idx} ---")
            log(f"Raw title: '{section_title}'")

            base = ask_ollama_for_filename(section_title)
            filename = f"{base}.md"
            filepath = OUTPUT_DIR / filename

            subsections = re.findall(r"^##\s+(.*)", body, flags=re.MULTILINE)

            toc = ""
            if subsections:
                toc += "## Table of Contents\n\n"
                for sub in subsections:
                    anchor = re.sub(r"[^a-z0-9\- ]", "", sub.lower()).replace(" ", "-")
                    toc += f"- [{sub}](#{anchor})\n"
                toc += "\n"

            header_index_link = "[← Back to Home](../README.md)\n\n"
            footer_index_link = "\n\n---\n[← Back to Home](../README.md)\n"

            with open(filepath, "w", encoding="utf-8") as f:
                f.write(header_index_link)
                f.write(toc)
                f.write(f"# {section_title}\n\n")
                f.write(body)
                f.write(footer_index_link)

            articles.append((section_title, filename))

    print()  # salto de línea al terminar la barra

    log("=== SPLIT PROCESS COMPLETED ===")
    return articles, readme_sections, matches[0].group(1).strip()


def generate_readme(articles, readme_sections, title):
    """Generate README.md based on selected sections."""
    log("Generating README.md")

    with open(README_PATH, "w", encoding="utf-8") as f:

        # Sección 1 → título + contenido completo
        sec1_title, sec1_body = readme_sections.get(1, (title, ""))
        f.write(f"# {sec1_title}\n\n")
        f.write(f"{sec1_body}\n\n")

        # Otras secciones → como subsecciones normales
        for idx in sorted(readme_sections.keys()):
            if idx == 1:
                continue
            sec_title, sec_body = readme_sections[idx]
            f.write(f"## {sec_title}\n\n")
            f.write(f"{sec_body}\n\n")

        # Tabla de artículos
        f.write("## Articles\n\n")
        f.write("| Article |\n")
        f.write("|---------|\n")
        for t, filename in articles:
            f.write(f"| [{t}](articles/{filename}) |\n")

    log("README.md generated successfully")


# ---------------------------------------------------------
# Entry point
# ---------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="Split Markdown into articles.")
    parser.add_argument("--in-readme", required=True, help="Sections to include in README (e.g., 1,3 or 1-3)")
    parser.add_argument("--articles", required=True, help="Sections to convert into articles (e.g., 4,5,6 or 4-25)")
    args = parser.parse_args()

    in_readme = parse_section_list(args.in_readme)
    article_sections = parse_section_list(args.articles)

    log("\n\n================ NEW RUN ================")
    articles, readme_sections, title = split_articles(in_readme, article_sections)
    generate_readme(articles, readme_sections, title)
    log("split.py finished successfully")


if __name__ == "__main__":
    main()
