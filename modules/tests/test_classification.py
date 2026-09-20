from pathlib import Path

from core.classification import classify_file


def main():
    markdown_paths = (
        "C:/Desktop/CampusGPT/data/md/faculty_details/ds/teaching/A_Srichandana.md",
    )

    for markdown_path in markdown_paths:
        result = classify_file(markdown_path)
        print(result.model_dump_json(indent=2))
        print('-'*60)


if __name__ == "__main__":
    main()