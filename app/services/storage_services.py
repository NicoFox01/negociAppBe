from uuid import uuid4, UUID
from fastapi import UploadFile, HTTPException
from app.core.supabase_client import supabase

BUCKET_NAME = "payments"

async def upload_payment_proof(
    file: UploadFile,
    tenant_id: UUID
) -> str:
    try:
        if file.content_type not in ["application/pdf", "image/jpeg", "image/png"]:
            raise HTTPException(status_code=400, detail="Formato de archivo no válido. Debe ser PDF, JPG o PNG.")
        file_content = await file.read()
        
        # Limit to 5MB
        if len(file_content) > 5 * 1024 * 1024:
             raise HTTPException(status_code=400, detail="El archivo excede el tamaño máximo permitido de 5MB")

        file_extension = file.filename.split(".")[-1]
        file_path = f"payments/{tenant_id}/{uuid4()}.{file_extension}"

        res = supabase.storage.from_(BUCKET_NAME).upload(
            path = file_path,
            file = file_content,
            file_options = {"content-type": file.content_type})
        public_url = supabase.storage.from_(BUCKET_NAME).get_public_url(file_path)
        return public_url
    except Exception as e:
        print(f"Error al subir el archivo: {str(e)}")
        raise HTTPException(status_code=500, detail="Error al subir el archivo")
        
    