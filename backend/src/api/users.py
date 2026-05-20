import json
from pathlib import Path

from api.schema import Response, ContentType
from router.http_router import HTTPRouter

DATABASE_PATH = Path("./src/database")

router = HTTPRouter()


@router.get("")
def get_users() -> Response:
    users_data = DATABASE_PATH / "users.json"
    with users_data.open("r", encoding="utf-8") as file:
        users = json.load(file)
        return Response(content_type=ContentType.JSON, data=users)
