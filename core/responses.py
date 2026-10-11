from rest_framework.response import Response


def success(message: str, data=None, status: int = 200, headers: dict | None = None) -> Response:
    return Response({"success": True, "message": message, "data": data}, status=status, headers=headers)


def error_body(message: str, errors: list | None = None) -> dict:
    return {"success": False, "message": message, "errors": errors or []}
