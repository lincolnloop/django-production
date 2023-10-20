import tokenize

from django_upgrade.ast import ast_parse
from django_upgrade.data import Settings
from django_upgrade.main import fixup_dedent_tokens
from tokenize_rt import reversed_enumerate, src_to_tokens, tokens_to_src

from django_production.data import visit


def apply_fixers(contents_text: str, filename: str) -> str:
    try:
        ast_obj = ast_parse(contents_text)
    except SyntaxError:
        return contents_text

    callbacks = visit(ast_obj, Settings(target_version=(999, 0)), filename)

    if not callbacks:
        return contents_text

    try:
        tokens = src_to_tokens(contents_text)
    except tokenize.TokenError:  # pragma: no cover (bpo-2180)
        return contents_text

    fixup_dedent_tokens(tokens)

    for i, token in reversed_enumerate(tokens):
        if not token.src:
            continue
        # though this is a defaultdict, by using `.get()` this function's
        # self time is almost 50% faster
        for callback in callbacks.get(token.offset, ()):
            callback(tokens, i)

    # no types for tokenize-rt
    return tokens_to_src(tokens)  # type: ignore [no-any-return]
