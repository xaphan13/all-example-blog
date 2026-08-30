import re
from typing import Any, Literal

from jinja2 import Template

CLI_USER_AGENT_PATTERN = re.compile(r"\b(?:curl|httpie|wget)/[^\s]+\b", re.IGNORECASE)

POST_ANSI_TEMPLATE = """
{{ post.header }}

\033[1;97m{{ post.title }}\033[0m

\033[90m{{ author.full_name }}\033[0m

\033[90m{{ post.reading_time }}\t{{ post.publish_date }}\033[0m

{{ post.body }}\n
"""

PROJECT_ANSI_TEMPLATE = """
{{ project.header }}

\033[1;97m{{ project.title }}\033[0m

\033[90m{{ author.full_name }}\033[0m

\033[90m{{ project.reading_time }}\t{{ project.publish_date }}\033[0m

{{ project.body }}

{% if project.repository %}\033[1;97mRepository:\033[0m {{ project.repository }}{% endif %}

{% if project.website %}\033[1;97mWebsite:\033[0m {{ project.website }}{% endif %}\n
"""  # noqa: E501

NOT_FOUND_ANSI_TEMPLATE = """
\033[1;97mPage not found\033[0m\n
"""

UNEXPECTED_ERROR_ANSI_TEMPLATE = """
\033[1;97mUnexpected error\033[0m\n
"""

POST_LIST_ANSI_TEMPLATE = """
\033[47;30;1mRevelations\033[0m
{% for post in posts %}
{% set thumbnail_lines = post.thumbnail.split('\n') %}
\033[3m\033[4m\033[34m{{ post.url }}\033[0m

{{ thumbnail_lines[0] }}
{{ thumbnail_lines[1] }}    \033[90m\033[40m{{ post.reading_time }}\033[0m  \033[90m{% if post.topic %}{{ post.topic }}{% endif %}\033[0m
{{ thumbnail_lines[2] }}    \033[1;97m\033]8;;{{ post.url }}\033\\{{ post.title }}\033]8;;\033\\\033[0m
{{ thumbnail_lines[3] }}
{{ thumbnail_lines[4] }}
{{ thumbnail_lines[5] }}
{{ thumbnail_lines[6] }}    \033[90m{{ post.publish_date.rjust(35) }}\033[0m
{{ thumbnail_lines[7] }}
{% endfor %}
"""  # noqa: E501

PROJECT_LIST_ANSI_TEMPLATE = """
\033[47;30;1mProjects\033[0m
{% for project in projects %}
{% set thumbnail_lines = project.thumbnail.split('\n') %}
\033[3m\033[4m\033[34m{{ project.url }}\033[0m

{{ thumbnail_lines[0] }}
{{ thumbnail_lines[1] }}    \033[90m\033[40m{{ project.reading_time }}\033[0m  \033[90m{% if project.repository %}Open Source{% else %}Closed Source{% endif %}\033[0m
{{ thumbnail_lines[2] }}    \033[1;97m\033]8;;{{ project.url }}\033\\{{ project.title }}\033]8;;\033\\\033[0m
{{ thumbnail_lines[3] }}    {{ project.ansi_description[0] }}
{{ thumbnail_lines[4] }}    {{ project.ansi_description[1] }}
{{ thumbnail_lines[5] }}
{{ thumbnail_lines[6] }}    \033[90m{{ project.publish_date.rjust(35) }}\033[0m
{{ thumbnail_lines[7] }}
{% endfor %}
"""  # noqa: E501

ANSITemplateName = Literal[
    "post_template",
    "project_template",
    "not_found_template",
    "unexpected_error_template",
    "post_list_template",
    "project_list_template",
]


def is_cli_client_by_user_agent(user_agent: str) -> bool:
    return bool(CLI_USER_AGENT_PATTERN.search(user_agent))


def render_ansi_template(
    template_name: ANSITemplateName,
    context: dict[str, Any] | None = None,
):
    match template_name:
        case "post_template":
            template = Template(POST_ANSI_TEMPLATE)
        case "project_template":
            template = Template(PROJECT_ANSI_TEMPLATE)
        case "not_found_template":
            template = Template(NOT_FOUND_ANSI_TEMPLATE)
        case "unexpected_error_template":
            template = Template(UNEXPECTED_ERROR_ANSI_TEMPLATE)
        case "post_list_template":
            template = Template(POST_LIST_ANSI_TEMPLATE)
        case "project_list_template":
            template = Template(PROJECT_LIST_ANSI_TEMPLATE)
    context = context or {}
    return template.render(**context)
