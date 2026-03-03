class FakeResult:
    def __init__(self, rows: list[dict] | None = None, scalar_value: int | None = None):
        self._rows = rows or []
        self._scalar_value = scalar_value

    def mappings(self) -> "FakeResult":
        return self

    def all(self) -> list[dict]:
        return self._rows

    def first(self) -> dict | None:
        return self._rows[0] if self._rows else None

    def scalar_one(self) -> int:
        if self._scalar_value is None:
            raise AssertionError("scalar_one() called without a configured scalar value")
        return self._scalar_value


class FakeConnection:
    def __init__(self, handlers: list):
        self.handlers = handlers

    def execute(self, statement, params=None) -> FakeResult:
        sql = str(statement)
        for handler in self.handlers:
            result = handler(sql, params or {})
            if result is not None:
                return result
        raise AssertionError(f"Unexpected SQL executed in test: {sql}")


class FakeSession:
    def __init__(self, handlers: list):
        self._connection = FakeConnection(handlers)

    def connection(self) -> FakeConnection:
        return self._connection
