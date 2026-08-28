"""Enable `python -m overheatlens <command>`."""

from .cli.main import main

if __name__ == "__main__":
    raise SystemExit(main())
