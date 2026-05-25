import pytest
from asserts import assert_equal, assert_in, assert_raises

from request.schema import HTTPRequestMethod
from router.exceptions import DuplicateRoute
from router.http_router import HTTPRouter


TEST_PATH = "/"

class TestIncludeRoute:
    @pytest.mark.parametrize(
        "request_method",
        [
            request_method for request_method in HTTPRequestMethod
        ],
    )
    @pytest.mark.asyncio
    async def test_should_include_route_with_non_existent_path(self, request_method: HTTPRequestMethod):
        router = HTTPRouter()

        router.include_route(path=TEST_PATH, method=request_method, handler=lambda x: x)

        assert_in(TEST_PATH, router.routes)
        assert_in(request_method, router.routes[TEST_PATH])


    @pytest.mark.parametrize(
        "request_method",
        [
            request_method for request_method in HTTPRequestMethod
        ],
    )
    @pytest.mark.asyncio
    async def test_should_include_new_route_method_for_existent_path(self, request_method: HTTPRequestMethod):
        router = HTTPRouter()

        for test_method in HTTPRequestMethod:
            if test_method != request_method:
                router.include_route(path=TEST_PATH, method=test_method, handler=lambda x: x)
                assert_in(test_method, router.routes[TEST_PATH])
                break

        router.include_route(path=TEST_PATH, method=request_method, handler=lambda x: x)

        assert_in(TEST_PATH, router.routes)
        assert_in(request_method, router.routes[TEST_PATH])


    @pytest.mark.parametrize(
        "request_method",
        [
            request_method for request_method in HTTPRequestMethod
        ],
    )
    @pytest.mark.asyncio
    async def test_should_fail_to_include_route_with_duplicate_method_for_same_path(self, request_method: HTTPRequestMethod):
        router = HTTPRouter()

        router.include_route(path=TEST_PATH, method=request_method, handler=lambda x: x)
        assert_in(request_method, router.routes[TEST_PATH])

        assert_in(TEST_PATH, router.routes)
        assert_in(request_method, router.routes[TEST_PATH])

        with assert_raises(DuplicateRoute, f"{request_method.value} already exists for path {TEST_PATH}"):
            router.include_route(path=TEST_PATH, method=request_method, handler=lambda x: x)
