from pathlib import Path

from processing.converters.pdf import PDFConverter


def main() -> None:
    pdf_path = Path(
        r"C:\Desktop\CampusGPT\data\pdfs\academic_calenders\Revised Academic Calendar for II B.Tech. I & II Semesters 2026-27.pdf"
    )

    converter = PDFConverter(api_key="")

    print(f"Supports PDF: {converter.supports(pdf_path)}")

    markdown = converter.convert(pdf_path)

    print(f"Generated Markdown: {len(markdown)} characters")
    print(markdown)


if __name__ == "__main__":
    main()