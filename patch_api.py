import re

with open('ermi/api.py', 'r') as f:
    content = f.read()

helper = """
def validate_allowed_path(path: Path, root: Path) -> None:
    from ermi.setup import load_setup

    allowed_dirs = [root.resolve()]
    setup_config = load_setup(root)
    if setup_config.get("chatgpt_source"):
        allowed_dirs.append(
            Path(setup_config["chatgpt_source"]).expanduser().resolve().parent
        )
    if setup_config.get("chatlasso_source"):
        allowed_dirs.append(
            Path(setup_config["chatlasso_source"]).expanduser().resolve()
        )

    if not any(path.is_relative_to(d) for d in allowed_dirs):
        raise HTTPException(
            status_code=403,
            detail="Source path is not within an allowed directory.",
        )


def create_app(default_root: Path | None = None) -> FastAPI:"""

content = content.replace("def create_app(default_root: Path | None = None) -> FastAPI:", helper)

with open('ermi/api.py', 'w') as f:
    f.write(content)
