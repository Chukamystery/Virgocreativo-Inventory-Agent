import time
from pathlib import Path

from openai import OpenAI

from app.config import settings


client = OpenAI(
    api_key=settings.openai_api_key
)


KNOWLEDGE_FOLDER = Path("knowledge")


def main():
    if not KNOWLEDGE_FOLDER.exists():
        raise FileNotFoundError(
            "knowledge folder was not found"
        )

    files = list(
        KNOWLEDGE_FOLDER.glob("*.txt")
    )

    if not files:
        raise ValueError(
            "No .txt knowledge files were found"
        )

    # -----------------------------------------
    # CREATE VECTOR STORE
    # -----------------------------------------

    vector_store = (
        client.vector_stores.create(
            name="Inventory Agent Knowledge"
        )
    )

    print(
        "Vector store created:",
        vector_store.id,
    )

    # -----------------------------------------
    # UPLOAD + ATTACH FILES
    # -----------------------------------------

    for path in files:

        print(
            "Uploading:",
            path.name,
        )

        with path.open("rb") as file_handle:

            uploaded_file = (
                client.files.create(
                    file=file_handle,
                    purpose="assistants",
                )
            )

        client.vector_stores.files.create(
            vector_store_id=(
                vector_store.id
            ),
            file_id=uploaded_file.id,
        )

        print(
            "Attached:",
            path.name,
        )

    # -----------------------------------------
    # WAIT FOR INDEXING
    # -----------------------------------------

    print(
        "Waiting for files to be processed..."
    )

    while True:

        current = (
            client.vector_stores.retrieve(
                vector_store_id=(
                    vector_store.id
                )
            )
        )

        print(
            "Status:",
            current.status,
            "| Completed:",
            current.file_counts.completed,
            "| In progress:",
            current.file_counts.in_progress,
            "| Failed:",
            current.file_counts.failed,
        )

        if current.file_counts.failed > 0:
            raise RuntimeError(
                "One or more knowledge files "
                "failed to process"
            )

        if (
            current.file_counts.in_progress == 0
            and current.file_counts.completed
            == current.file_counts.total
        ):
            break

        time.sleep(2)

    print()
    print(
        "Knowledge store ready."
    )

    print(
        "Add this to your .env file:"
    )

    print(
        "OPENAI_VECTOR_STORE_ID="
        + vector_store.id
    )


if __name__ == "__main__":
    main()