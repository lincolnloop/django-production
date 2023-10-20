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
    try:
    MIDDLEWARE.insert(
        MIDDLEWARE.index("django.middleware.security.SecurityMiddleware") + 1,
        "whitenoise.middleware.WhiteNoiseMiddleware",
    )
    except ValueError:
        MIDDLEWARE.insert(0, "whitenoise.middleware.WhiteNoiseMiddleware")

    # skip host checking for healthcheck URLs
    MIDDLEWARE.insert(0, "django_alive.middleware.healthcheck_bypass_host_check")
    """
    if node.targets[0].id == "MIDDLEWARE" and isinstance(node.value, ast.List):
        yield ast_start_offset(node), partial(add_middleware, node=node)
    return []


def add_middleware(
    tokens: list[Token],
    i: int,
    *,
    node: ast.Assign,
) -> None:
    j = find_last_token(tokens, i, node=node)
    middleware = [v.s for v in node.value.elts]
    original_middleware = middleware.copy()
    whitenoise_middleware_path = "whitenoise.middleware.WhiteNoiseMiddleware"
    if whitenoise_middleware_path not in middleware:
        try:
            security_middleware_index = middleware.index(
                "django.middleware.security.SecurityMiddleware"
            )
        except ValueError:
            security_middleware_index = -1
        middleware.insert(security_middleware_index + 1, whitenoise_middleware_path)

    alive_middleware_path = "django_alive.middleware.healthcheck_bypass_host_check"
    if alive_middleware_path not in middleware:
        middleware.insert(0, alive_middleware_path)
    if middleware == original_middleware:
        return
    code = ["MIDDLEWARE = ["]
    code.extend([f'    "{m}",' for m in middleware])
    code.append("]")
    tokens[i : j + 1] = [Token(name=CODE, src="\n".join(code))]
