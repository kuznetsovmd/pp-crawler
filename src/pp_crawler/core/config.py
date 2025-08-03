from dataclasses import dataclass, field
from multiprocessing import cpu_count
from pathlib import Path
from typing import Any, Optional


@dataclass
class PathConfig:
    resources_path: Path
    html_path: Path
    explicit_file: Path
    descriptor_file: Path

    @staticmethod
    def build(
        resources_path: str,
        html_path: str,
        explicit_file: str,
        descriptor_file: str,
        **kwargs,
    ) -> "PathConfig":
        r = Path(resources_path).expanduser()
        transformed = {
            **kwargs,
            "resources_path": r,
            "html_path": r / html_path,
            "explicit_file": r / explicit_file,
            "descriptor_file": r / descriptor_file,
        }
        return PathConfig(**transformed)


@dataclass
class DriverConfig:
    profile_path: Optional[Path]
    log_path: Path = field(default_factory=lambda: Path("./.geckodriver.log"))
    temp_dir: Path = field(default_factory=lambda: Path("./.tmp"))
    dotfile: Path = field(default_factory=lambda: Path("./.driver"))
    log_level: int = 0
    private: bool = True
    no_cache: bool = True
    headless: bool = True
    use_proxy: bool = False
    page_load_timeout: int = 30
    max_error_attempts: int = 10
    max_captcha_attempts: int = 10
    max_timeout_attempts: int = 10
    proxies_from_conf: bool = False
    proxies: list[str] = field(default_factory=list)
    user_agents: list[str] = field(default_factory=list)

    @staticmethod
    def build(**kwargs) -> "DriverConfig":
        return DriverConfig(**kwargs)


@dataclass
class Config:
    path: PathConfig
    driver: DriverConfig
    pipeline: str
    proc_count: int

    @staticmethod
    def build(
        path: dict[str, str],
        driver: dict[str, Any],
        proc_count: int = -1,
        **kwargs,
    ) -> "Config":
        transformed = {
            **kwargs,
            "proc_count": proc_count if proc_count > 1 else cpu_count(),
            "path": PathConfig.build(**path),
            "driver": DriverConfig.build(**driver),
        }
        return Config(**transformed)
