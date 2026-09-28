from collections.abc import AsyncIterator, Sequence

from src.common.csv_export import csv_streaming_response, safe_csv_cell


async def test_csv_response_streams_bom_quotes_and_safe_formula_cells():
    async def rows() -> AsyncIterator[Sequence[object]]:
        yield ["Jan, Kowalski", "=2+2", "żółć"]

    response = csv_streaming_response(
        filename="lista obecności.csv",
        headers=["Osoba", "Wartość", "Notatka"],
        rows=rows(),
    )
    chunks = [chunk async for chunk in response.body_iterator]
    body = "".join(chunk.decode() if isinstance(chunk, bytes) else chunk for chunk in chunks)

    assert response.media_type == "text/csv; charset=utf-8"
    assert "lista%20obecno%C5%9Bci.csv" in response.headers["content-disposition"]
    assert body.startswith("\ufeffOsoba,Wartość,Notatka\r\n")
    assert '"Jan, Kowalski",\'=2+2,żółć\r\n' in body


def test_safe_csv_cell_neutralizes_spreadsheet_formulas():
    assert [safe_csv_cell(value) for value in ("=1", "+1", "-1", "@cmd")] == [
        "'=1",
        "'+1",
        "'-1",
        "'@cmd",
    ]
