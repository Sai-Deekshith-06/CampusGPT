from pathlib import Path

from processing.converters import MarkdownConverter
from processing.converters.registry import ConverterRegistry
from processing.exceptions import UnsupportedFileError


def main() -> None:
    registry = ConverterRegistry(
        converters=[
            MarkdownConverter(),
        ]
    )

    markdown_file = Path(r"C:\Desktop\CampusGPT\data\md\faculty_details\ds\teaching\A_Srichandana.md")

    converter = registry.get_converter(markdown_file)

    print(f"Selected converter: {converter.__class__.__name__}")

    markdown = converter.convert(markdown_file)

    print(f"Markdown length: {len(markdown)} characters")
    print(f"First 100 characters:\n{markdown[:100]}")

    try:
        registry.get_converter("sample.pdf")
    except UnsupportedFileError as exc:
        print(f"Unsupported file handled correctly: {exc}")


if __name__ == "__main__":
    main()