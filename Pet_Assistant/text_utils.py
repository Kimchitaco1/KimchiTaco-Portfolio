import unicodedata


def normalize_text(text):
    normalized = unicodedata.normalize("NFD", str(text).strip().lower())
    without_accents = "".join(
        char for char in normalized if unicodedata.category(char) != "Mn"
    )
    return " ".join(without_accents.split())
