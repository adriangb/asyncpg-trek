from typing import Any

import pytest


@pytest.fixture(
    params=[
        pytest.param(("asyncio", {"use_uvloop": False}), id="asyncio"),
    ]
)
def anyio_backend(request: Any) -> Any:
    return request.param
