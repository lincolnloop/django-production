import ast


def add_imports(contents: str, filename: str) -> str:
    tree = ast.parse(contents.encode(), filename=filename)

    # Check if the 'os' module has been imported
    os_imported = any(
        isinstance(node, ast.Import) and any(alias.name == 'os' for alias in node.names) for node in ast.walk(tree))

    # If 'os' module is not imported, add the import statement
    if not os_imported:
        import_os = ast.Import(names=[ast.alias(name='os', asname=None)])
        tree.body.insert(0, import_os)

    # Generate the modified code
    return compile(tree, filename, 'exec')
