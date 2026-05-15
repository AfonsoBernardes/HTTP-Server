from router.http_router import HTTPRouter

router = HTTPRouter()


@router.get("")
def get_users():
    print("GET USERS ROUTER")
