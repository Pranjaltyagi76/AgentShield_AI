"""Bound JSON writes before FastAPI buffers or parses them."""

from starlette.responses import JSONResponse


class BodyLimit:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http" or scope["method"] not in {"POST", "PATCH"}:
            return await self.app(scope, receive, send)
        limit = 262144 if scope["path"] == "/api/v1/runs" else 65536
        body = bytearray()
        while True:
            event = await receive()
            if event["type"] == "http.disconnect":
                return
            chunk = event.get("body", b"")
            if len(body) + len(chunk) > limit:
                return await JSONResponse(
                    {
                        "error": {
                            "code": "payload_too_large",
                            "message": f"Maximum body is {limit // 1024} KiB.",
                        }
                    },
                    status_code=413,
                )(scope, receive, send)
            body.extend(chunk)
            if not event.get("more_body"):
                break
        consumed = False

        async def replay():
            nonlocal consumed
            if consumed:
                return await receive()
            consumed = True
            return {"type": "http.request", "body": bytes(body), "more_body": False}

        await self.app(scope, replay, send)
