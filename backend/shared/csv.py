import csv
import io

from collections.abc import AsyncIterable
from typing import Any

from fastapi.responses import StreamingResponse

def csv_response(filename: str, header: list[str], rows: AsyncIterable[list[Any]]) -> StreamingResponse:
    async def generate():
        buffer = io.StringIO()
        writer = csv.writer(buffer)
        writer.writerow(header)
        yield buffer.getvalue()
        buffer.seek(0)
        buffer.truncate(0)
        async for row in rows:
            writer.writerow(row)
            yield buffer.getvalue()
            buffer.seek(0)
            buffer.truncate(0)

    return StreamingResponse(
        generate(),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )
