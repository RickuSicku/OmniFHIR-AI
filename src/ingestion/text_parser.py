"""
Text file parser for plain .txt clinical documents.
"""


def parse_text_file(file_path: str) -> str:
    """Read and return the raw text content of a .txt file.

    Args:
        file_path: Absolute path to the .txt file.

    Returns:
        The raw text content of the file.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file is empty.
    """
    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
        content = f.read()

    if not content.strip():
        raise ValueError(f"File is empty: {file_path}")

    return content.strip()
