import uuid

from database.base import Base
from database.connection import SessionLocal, engine
from database.models import Document


def main():
    document_id = uuid.uuid4()

    with SessionLocal() as session:
        document = Document(
            id=document_id,
            name="Test Academic Calendar",
            original_filename="academic_calendar.pdf",
            mime_type="application/pdf",
            file_size=1024,
            storage_path="originals/test/academic_calendar.pdf",
            domain="academic",
            document_type="academic_calendar",
            processing_status="pending",
        )

        session.add(document)
        session.commit()

        saved_document = session.get(Document, document_id)

        print("Database connection successful.")
        print(f"Document ID: {saved_document.id}")
        print(f"Document name: {saved_document.name}")
        print(f"Document status: {saved_document.processing_status}")

        # Clean up the test record
        session.delete(saved_document)
        session.commit()
        print("Test record cleaned up successfully.")

if __name__ == "__main__":
    main()