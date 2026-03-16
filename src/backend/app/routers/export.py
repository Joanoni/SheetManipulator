import io

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.schema_definition import SchemaDefinition
from app.services.export import export_table_to_xlsx

router = APIRouter()

XLSX_MEDIA_TYPE = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


@router.get("/tables/{table_name}/export")
async def export_table(
    table_name: str,
    db: AsyncSession = Depends(get_db),
):
    """Stream a .xlsx file of all non-deleted rows for the given table.

    Returns:
        StreamingResponse with Content-Type xlsx and Content-Disposition attachment.

    Raises:
        HTTPException 404: If table_name does not exist in schema_definitions.
    """
    # Verify table exists in schema_definitions
    result = await db.execute(
        select(SchemaDefinition.table_system_name)
        .where(SchemaDefinition.table_system_name == table_name)
        .limit(1)
    )
    if result.scalar_one_or_none() is None:
        raise HTTPException(status_code=404, detail="Table not found")

    xlsx_bytes = await export_table_to_xlsx(table_name, db)

    return StreamingResponse(
        io.BytesIO(xlsx_bytes),
        media_type=XLSX_MEDIA_TYPE,
        headers={
            "Content-Disposition": f'attachment; filename="{table_name}_export.xlsx"'
        },
    )
