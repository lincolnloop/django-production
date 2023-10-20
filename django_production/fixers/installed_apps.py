import ast
from functools import partial
from typing import Iterable

from django_upgrade.ast import ast_start_offset
from django_upgrade.data import Fixer, State, TokenFunc
from django_upgrade.tokens import CODE, find_last_token
from tokenize_rt import Offset, Token

fixer = Fixer(
    __name__,
    min_version=(0, 0),
)


@fixer.register(ast.Assign)
def visit_Assign(
    state: State,
    node: ast.Assign,
    parents: list[ast.AST],
) -> Iterable[tuple[Offset, TokenFunc]]:
    """
    Ensure these are in INSTALLED_APPS
        [
            "django_webserver",  # Allow running webserver from manage.py
            "whitenoise.runserver_nostatic",  # Use whitenoise with runserver
        ]
    """
    if node.targets[0].id == "INSTALLED_APPS" and isinstance(node.value, ast.List):
        yield ast_start_offset(node), partial(add_apps, node=node)
    return []


def add_apps(
    tokens: list[Token],
    i: int,
    *,
    node: ast.Assign,
) -> None:
    j = find_last_token(tokens, i, node=node)
    needs_app = []
    current_apps = [v.s for v in node.value.elts]
    for wants_app in ["django_webserver", "whitenoise.runserver_nostatic"]:
        if wants_app not in current_apps:
            needs_app.append(wants_app)
    if len(needs_app) == 0:
        return
    code = ["INSTALLED_APPS = ["]
    code.extend([f'    "{a}",' for a in current_apps])
    code.extend([f'    "{a}",' for a in needs_app])
    code.append("]")
    tokens[i : j + 1] = [Token(name=CODE, src="\n".join(code))]
