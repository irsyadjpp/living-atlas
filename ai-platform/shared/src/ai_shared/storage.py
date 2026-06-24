"""Storage client — NOT USED in PRD v2.0.

No audio/video files are stored. All data is text/JSON in PostgreSQL.
This file is kept as a stub for potential future use with article images/assets.
"""

import structlog

logger = structlog.get_logger(__name__)


class StorageClient:
    """Stub — no file storage needed in PRD v2.0.
    
    All data is stored as text/JSON in PostgreSQL.
    Audio/video is never downloaded or stored.
    """

    def __init__(self, *args, **kwargs):
        logger.warning("storage_client_not_used", message="No file storage needed. All data in PostgreSQL.")

    async def ensure_buckets(self) -> None:
        pass

    def upload_file(self, *args, **kwargs) -> str:
        raise NotImplementedError("File storage not available. All data in PostgreSQL.")

    def download_file(self, *args, **kwargs):
        raise NotImplementedError("File storage not available. All data in PostgreSQL.")