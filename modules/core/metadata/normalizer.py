import re
from datetime import datetime


def normalize_text(value: str | None) -> str | None:
    if not value:
        return None

    value = re.sub(r"\s+", " ", value)
    return value.strip() or None


def normalize_list(values: list[str]) -> list[str]:
    normalized = []

    for value in values:
        value = normalize_text(value)

        if value and value not in normalized:
            normalized.append(value)

    return normalized


def normalize_academic_year(value: str | None) -> str | None:
    if not value:
        return None

    value = value.strip()

    match = re.search(
        r"(20\d{2})\s*[-/]\s*(\d{2}|20\d{2})",
        value,
    )

    if not match:
        return value

    start_year = match.group(1)
    end_year = match.group(2)

    if len(end_year) == 4:
        end_year = end_year[-2:]

    return f"{start_year}-{end_year}"


def normalize_date(value: str | None) -> str | None:
    if not value:
        return None

    value = value.strip()

    date_formats = (
        "%d.%m.%Y",
        "%d-%m-%Y",
        "%d/%m/%Y",
        "%d.%m.%y",
        "%d-%m-%y",
        "%d/%m/%y",
        "%d %b %Y",
        "%d %B %Y",
    )

    for date_format in date_formats:
        try:
            parsed_date = datetime.strptime(value, date_format)
            return parsed_date.strftime("%Y-%m-%d")
        except ValueError:
            continue

    return value


def normalize_program(value: str | None) -> str | None:
    if not value:
        return None

    value = re.sub(r"\s+", "", value.upper())

    aliases = {
        "BTECH": "B.Tech",
        "B.TECH": "B.Tech",
        "MTECH": "M.Tech",
        "M.TECH": "M.Tech",
        "MBA": "MBA",
        "MCA": "MCA",
        "BCA": "BCA",
        "BBA": "BBA",
        "MSC": "M.Sc",
        "M.SC": "M.Sc",
        "BSC": "B.Sc",
        "B.SC": "B.Sc",
    }

    return aliases.get(value, value)


def normalize_email(value: str | None) -> str | None:
    if not value:
        return None

    value = value.strip().lower()

    if re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", value):
        return value

    return None