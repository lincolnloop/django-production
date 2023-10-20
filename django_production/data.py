import ast
import pkgutil
from collections import defaultdict

from django_upgrade.data import FIXERS, ASTCallbackMapping, Settings, State, TokenFunc
from tokenize_rt import Offset

from django_production import fixers


def visit(
    tree: ast.Module,
    settings: Settings,
    filename: str,
) -> dict[Offset, list[TokenFunc]]:
    ast_funcs = get_ast_funcs()
    initial_state = State(
        settings=settings,
        filename=filename,
        from_imports=defaultdict(set),
    )

    nodes: list[tuple[State, ast.AST, ast.AST]] = [(initial_state, tree, tree)]
    parents: list[ast.AST] = [tree]
    ret = defaultdict(list)
    while nodes:
        state, node, parent = nodes.pop()
        if len(parents) > 1 and parent == parents[-2]:
            parents.pop()
        elif parent != parents[-1]:
            parents.append(parent)

        for ast_func in ast_funcs.get(type(node), [None]):
            if ast_func is None:
                continue
            for offset, token_func in ast_func(state, node, parents):
                ret[offset].append(token_func)

        for name in reversed(node._fields):
            value = getattr(node, name)
            next_state = state

            if isinstance(value, ast.AST):
                nodes.append((next_state, value, node))
            elif isinstance(value, list):
                for subvalue in reversed(value):
                    if isinstance(subvalue, ast.AST):
                        nodes.append((next_state, subvalue, node))
    return ret


def _import_fixers() -> None:
    # https://github.com/python/mypy/issues/1422
    fixers_path: str = fixers.__path__  # type: ignore
    mod_infos = pkgutil.walk_packages(fixers_path, f"{fixers.__name__}.")
    for _, name, _ in mod_infos:
        __import__(name, fromlist=["_trash"])


_import_fixers()


def get_ast_funcs() -> ASTCallbackMapping:
    ast_funcs: ASTCallbackMapping = defaultdict(list)
    for fixer in FIXERS:
        if fixer.name.startswith("django_production."):
            for type_, type_funcs in fixer.ast_funcs.items():
                ast_funcs[type_].extend(type_funcs)
    return ast_funcs
