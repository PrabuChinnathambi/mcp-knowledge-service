import io
import os
from minio import Minio
from packages.core.config import get_settings
from packages.observability.logger import logger

settings = get_settings()


class StorageClient:
    def __init__(self):
        self.bucket = settings.MINIO_BUCKET
        self._client = None
        self._initialized = False
        self.local_storage_dir = os.path.join(os.getcwd(), "data", "storage")
        os.makedirs(self.local_storage_dir, exist_ok=True)

    def _get_client(self):
        if not self._initialized:
            self._initialized = True
            try:
                client = Minio(
                    endpoint=settings.MINIO_ENDPOINT,
                    access_key=settings.MINIO_ACCESS_KEY,
                    secret_key=settings.MINIO_SECRET_KEY,
                    secure=settings.MINIO_SECURE,
                )
                if client.bucket_exists(self.bucket):
                    self._client = client
                else:
                    client.make_bucket(self.bucket)
                    logger.info("Created MinIO bucket", bucket=self.bucket)
                    self._client = client
            except Exception as e:
                logger.warn("MinIO unavailable, operating with local storage fallback", error=str(e))
                self._client = None
        return self._client

    def upload_file(self, object_name: str, data: bytes, content_type: str) -> str:
        client = self._get_client()
        if client:
            try:
                client.put_object(
                    bucket_name=self.bucket,
                    object_name=object_name,
                    data=io.BytesIO(data),
                    length=len(data),
                    content_type=content_type,
                )
                logger.info("Uploaded object to MinIO", object_name=object_name, bytes=len(data))
                return f"s3://{self.bucket}/{object_name}"
            except Exception as e:
                logger.warn("MinIO upload failed, saving to local disk", error=str(e))

        # Local disk fallback
        local_path = os.path.join(self.local_storage_dir, object_name.replace("/", "_"))
        with open(local_path, "wb") as f:
            f.write(data)
        logger.info("Saved raw file to local storage", path=local_path, bytes=len(data))
        return f"file://{local_path}"

    def download_file(self, object_name: str) -> bytes:
        client = self._get_client()
        if client:
            try:
                response = client.get_object(self.bucket, object_name)
                try:
                    return response.read()
                finally:
                    response.close()
                    response.release_conn()
            except Exception:
                pass

        local_path = os.path.join(self.local_storage_dir, object_name.replace("/", "_"))
        with open(local_path, "rb") as f:
            return f.read()


storage_client = StorageClient()
