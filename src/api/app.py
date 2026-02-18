import sys
from pathlib import Path

# Add the api directory to sys.path so imports work when running directly
sys.path.insert(0, str(Path(__file__).parent))

from connexion import AsyncApp
from connexion.exceptions import ProblemException
from pydantic import ValidationError

from mcp_tools.main import mcp
from middleware import (
    app_exception_handler,
    generic_exception_handler,
    http_exception_handler,
    validation_error_handler,
)
from shared.exceptions import AppError

mcp_http_app = mcp.http_app(
    path="/",
    transport="http",
    stateless_http=True,
    json_response=True,
)

app = AsyncApp(
    __name__,
    specification_dir=Path(__file__).parent,
    lifespan=mcp_http_app.lifespan,
)
app.add_api("specification.yaml")

app._middleware_app.router.mount("/mcp", mcp_http_app)
app._middleware_app.router.mount("/mcp/", mcp_http_app)

app.add_error_handler(ValidationError, validation_error_handler)
app.add_error_handler(ProblemException, http_exception_handler)
app.add_error_handler(AppError, app_exception_handler)
app.add_error_handler(Exception, generic_exception_handler)

if __name__ == "__main__":
    app.run(port=8080)
