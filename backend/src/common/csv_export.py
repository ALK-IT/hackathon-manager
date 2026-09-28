import csv
import io
from collections.abc import AsyncIterable, AsyncIterator, Sequence
from urllib.parse import quote

from fastapi.responses import StreamingResponse

CSV_FORMULA_PREFIXES = ("=", "+", "-", "@")


def safe_csv_cell(value: object) -> str:
    text = "" if value is None else str(value)
    if text.startswith(CSV_FORMULA_PREFIXES):
        return f"'{text}"
    return text


def _csv_line(values: Sequence[object]) -> str:
    output = io.StringIO(newline="")
    csv.writer(output).writerow([safe_csv_cell(value) for value in values])
    return output.getvalue()


def csv_streaming_response(
    *,
    filename: str,
    headers: Sequence[str],
    rows: AsyncIterable[Sequence[object]],
) -> StreamingResponse:
    async def content() -> AsyncIterator[str]:
        yield "\ufeff" + _csv_line(headers)
        async for row in rows:
            yield _csv_line(row)

    encoded_filename = quote(filename)
    return StreamingResponse(
        content(),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}"},
    )
