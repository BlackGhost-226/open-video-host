from pydantic import BaseModel
from typing import Optional

class create_row_POST(BaseModel):
    kwargs: Optional[dict]
