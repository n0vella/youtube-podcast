from pathlib import Path

from dynaconf import Dynaconf

SETTINGS_DIR = Path(__file__).parent.parent

settings = Dynaconf(
    envvar_prefix="DYNACONF",
    settings_files=[
        str(SETTINGS_DIR / "settings.toml"),
        str(SETTINGS_DIR / ".secrets.toml"),
    ],
)

