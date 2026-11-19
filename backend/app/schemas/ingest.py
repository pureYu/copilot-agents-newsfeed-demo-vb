from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models import IngestionStatus


class IngestionRunResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    source_id: int
    started_at: datetime
    completed_at: datetime | None
    status: IngestionStatus
    articles_found: int
    articles_inserted: int
