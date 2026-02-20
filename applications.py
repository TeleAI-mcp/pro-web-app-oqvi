"""
FastAPI applications.
"""
from typing import Any, Dict, Optional

from starlette.applications import Starlette
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.gzip import GZipMiddleware
from starlette.middleware.httpsredirect import HTTPSRedirectMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware
from starlette.middleware.sessions import SessionMiddleware
from starlette.routing import Mount
from starlette.staticfiles import StaticFiles

from fastapi import routing
from fastapi.concurrency import run_in_threadpool
from fastapi.encoders import jsonable_encoder
from fastapi.exception_handlers import (
    http_exception_handler,
    request_validation_exception_handler,
)
from fastapi.exceptions import RequestValidationError
from fastapi.openapi.docs import get_redoc_html, get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
from fastapi.types import ASGIApp, IncEx


class FastAPI(Starlette):
    """
    The main FastAPI class.

    This class is the entry point for a FastAPI application.
    It inherits from Starlette and adds some functionality.
    """

    def __init__(
        self,
        *,
        debug: bool = False,
        routes: Optional[list[routing.BaseRoute]] = None,
        title: str = "FastAPI",
        description: str = "",
        version: str = "0.1.0",
        openapi_url: Optional[str] = "/openapi.json",
        openapi_tags: Optional[list[Dict[str, Any]]] = None,
        servers: Optional[list[Dict[str, Union[str, Any]]]] = None,
        docs_url: Optional[str] = "/docs",
        redoc_url: Optional[str] = "/redoc",
        swagger_ui_oauth2_redirect_url: Optional[str] = "/docs/oauth2-redirect",
        swagger_ui_init_oauth: Optional[Dict[str, Any]] = None,
        middleware: Optional[list[ASGIApp]] = None,
        exception_handlers: Optional[
            Dict[Union[int, Type[Exception]], typing.Callable]
        ] = None,
        on_startup: Optional[Sequence[Callable[[], Any]]] = None,
        on_shutdown: Optional[Sequence[Callable[[], Any]]] = None,
        default_response_class: Type[Response] = Default(JSONResponse),
        **extra: Any,
    ) -> None:
        """
        Initialize the FastAPI application.
        """
        self._debug: bool = debug
        self.state: State = State()
        self.router: routing.APIRouter = routing.APIRouter(
            routes=routes,
            dependency_overrides_provider=self,
            on_startup=on_startup,
            on_shutdown=on_shutdown,
        )
        self.title: str = title
        self.description: str = description
        self.version: str = version
        self.servers: Optional[list[Dict[str, Union[str, Any]]]] = servers
        self.openapi_url: Optional[str] = openapi_url
        self.openapi_tags: Optional[list[Dict[str, Any]]] = openapi_tags
        self.docs_url: Optional[str] = docs_url
        self.redoc_url: Optional[str] = redoc_url
        self.swagger_ui_oauth2_redirect_url: Optional[
            str
        ] = swagger_ui_oauth2_redirect_url
        self.swagger_ui_init_oauth: Optional[Dict[str, Any]] = swagger_ui_init_oauth
        self.middleware: list[ASGIApp] = middleware or []
        self.exception_handlers: Dict[
            Union[int, Type[Exception]], typing.Callable
        ] = exception_handlers or {}
        self.default_response_class: Type[Response] = default_response_class
        self.extra: Dict[str, Any] = extra
        self.openapi_version: str = "3.1.0"
        self.openapi_schema: Optional[Dict[str, Any]] = None
        self.user_middleware: list[UserMiddleware] = []
        self.middleware_stack: ASGIApp = self.build_middleware_stack()
        self.setup()

    def setup(self) -> None:
        """
        Set up the application.
        """
        if self.openapi_url:
            self.add_route(
                self.openapi_url,
                lambda: JSONResponse(self.openapi()),
                include_in_schema=False,
            )
        if self.docs_url:
            self.add_route(
                self.docs_url,
                lambda: get_swagger_ui_html(
                    openapi_url=self.openapi_url,
                    title=self.title + " - Swagger UI",
                    oauth2_redirect_url=self.swagger_ui_oauth2_redirect_url,
                    init_oauth=self.swagger_ui_init_oauth,
                ),
                include_in_schema=False,
            )
        if self.redoc_url:
            self.add_route(
                self.redoc_url,
                lambda: get_redoc_html(
                    openapi_url=self.openapi_url, title=self.title + " - ReDoc"
                ),
                include_in_schema=False,
            )
        if self.swagger_ui_oauth2_redirect_url:
            self.add_route(
                self.swagger_ui_oauth2_redirect_url,
                lambda: get_swagger_ui_oauth2_redirect_html(),
                include_in_schema=False,
            )
        self.add_exception_handler(RequestValidationError, request_validation_exception_handler)
        self.add_exception_handler(HTTPException, http_exception_handler)
        self.add_exception_handler(Exception, server_error_handler)

    def openapi(self) -> Dict[str, Any]:
        """
        Generate the OpenAPI schema.
        """
        if not self.openapi_schema:
            self.openapi_schema = get_openapi(
                title=self.title,
                version=self.version,
                description=self.description,
                routes=self.routes,
                tags=self.openapi_tags,
                servers=self.servers,
            )
        return self.openapi_schema
