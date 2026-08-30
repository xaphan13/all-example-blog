from typing import Annotated

from fastapi import Header

from app.views.utils import is_cli_client_by_user_agent


def is_cli_client(user_agent: Annotated[str | None, Header()]) -> bool:
    if not user_agent:
        return False
    return is_cli_client_by_user_agent(user_agent)
