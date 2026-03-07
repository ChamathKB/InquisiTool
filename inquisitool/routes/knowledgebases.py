import os

from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile

from inquisitool.constants import UPLOAD_DIR
from inquisitool.db.mongodb import (
    create_documents_collection,
    delete_documents_collection,
    upload_document,
)

router = APIRouter()


@router.post("/create_collection", response_model=dict)
async def create_collection(request: Request, collection_name: str) -> dict:
    """
    Creates a new Qdrant collection.

    Args:
        collection_name (str): The name of the collection to create.

    Returns:
        dict: A dictionary containing a success message.
    """

    result = await create_documents_collection(request.app.state.qdrant, collection_name)
    return {"message": f"{collection_name} collection created successfully with collection id {result['inserted_id']}!"}


@router.post("/upload_docs", response_model=dict)
async def upload_docs(
    request: Request,
    file: UploadFile = File(...),
    collection_id: str = Form(...),
    chunk_size: int = Form(1000),
    chunk_overlap: int = Form(50),
) -> dict:
    """
    Uploads preprocessed data with embeddings to a Qdrant collection.

    Args:
        file (UploadFile): The uploaded file containing data.
        collection_name (str): The name of the Qdrant collection to upload the data to.
        chunk_size (int): The size of chunks to break the data into.
        chunk_overlap (int): The overlap between chunks.

    Returns:
        dict: A dictionary containing the upload status message.
    """

    filename = file.filename
    content = await file.read()
    qdrant = request.app.state.qdrant

    # Save the uploaded file temporarily
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    file_path = os.path.join(UPLOAD_DIR, filename)

    try:
        with open(file_path, "wb") as buffer:
            buffer.write(content)

        await upload_document(file_path, qdrant, collection_id)

        os.remove(file_path)
        return {"message": "Embeddings uploaded successfully!"}

    except Exception as e:
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=500, detail=f"Document upload failed: {str(e)}")


@router.delete("/delete_collection", response_model=dict)
async def collection_delete(request: Request, collection_id: str) -> dict:
    """
    Deletes a Qdrant collection and its associated documents.

    Args:
        app (FastAPI): The FastAPI application instance containing the Qdrant client
        collection_name (str): The name of the collection to delete

    Returns:
        dict: A dictionary containing a success message indicating the collection was deleted

    Raises:
        HTTPException: If deletion fails with status code 500 and error details
    """

    try:
        result = await delete_documents_collection(request.app.state.qdrant, collection_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Document deletion failed: {str(e)}")
