from . import app

from . import Session
from sqlalchemy import select
from sqlalchemy import insert
from sqlalchemy import delete
from .posts import create_row_POST
from models import Video
from models import VideoTask
from typing import Optional

from fastapi import HTTPException
from fastapi.responses import JSONResponse

tables = {Video.__tablename__: Video, VideoTask.__tablename__: VideoTask}
allowed_columns = {
    Video.__tablename__: [
        Video.__table__.c.id, 
        Video.__table__.c.title, 
        Video.__table__.c.description, 
        Video.__table__.c.author_user_id
    ],
    VideoTask.__tablename__: [
        VideoTask.__table__.c.id,
        VideoTask.__table__.c.title,
        VideoTask.__table__.c.description,
        VideoTask.__table__.c.author_user_id
    ]
}
@app.get("/db/{table}")
def get_row(table: str, id: Optional[str] = None):
    with Session() as session:
        sql_table = tables.get(table)
        columns = allowed_columns.get(table)
        if not sql_table:
            raise HTTPException(status_code=404, detail="Table not found")
        if id:
            results = session.execute(select(*columns).where(sql_table.id == id))
        else:
            results = session.execute(select(*columns))
        result_list = results.mappings().all()
    return {"list": result_list}

@app.post("/db/{table}")
def add_row(table: str, post_data: create_row_POST):
    with Session() as session:
        sql_table = tables.get(table)
        if not sql_table:
            raise HTTPException(status_code=404, detail="Table not found")
        results = session.execute(insert(sql_table).values(**post_data.kwargs).returning(*sql_table.__table__.c))
        result_list = results.mappings().all()
        session.commit()
    return {"list": result_list}

@app.delete("/db/{table}")
def add_row(table: str, id: str):
    with Session() as session:
        sql_table = tables.get(table)
        if not sql_table:
            raise HTTPException(status_code=404, detail="Table not found")
        results = session.execute(delete(sql_table).where(sql_table.id == id).returning(*sql_table.__table__.c))
        result_list = results.mappings().all()
        session.commit()
    return {"list": result_list}
