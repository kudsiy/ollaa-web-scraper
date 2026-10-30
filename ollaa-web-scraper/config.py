"""
Configuration settings for Ollaa Web Scraper.
Manages database connection, scraper delays, and global settings.

Passwords and connection details come from the .env file in the top project folder
(never committed; .env.example lists the names). Settings already in the environment,
such as those of the GitHub automation, are kept.
"""
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

ENV_FILE = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(ENV_FILE)


def _env(name: str, default: str = ""):
    """Read a setting when the config is created, so tests can change it."""
    return field(default_factory=lambda: os.getenv(name, default))


@dataclass
class DatabaseConfig:
    """
    PostgreSQL database configuration: the shared `ollaa` database on this laptop, with its
    everyday login ollaa_user (task W3). There is no default password.
    """
    host: str = _env("DB_HOST", "localhost")
    port: int = field(default_factory=lambda: int(os.getenv("DB_PORT", "5432")))
    database: str = _env("DB_NAME", "ollaa")
    user: str = _env("DB_USER", "ollaa_user")
    password: str = _env("DB_PASSWORD")


@dataclass
class ScraperConfig:
    """Scraper behavior configuration."""
    request_delay_min: float = 2.0
    request_delay_max: float = 5.0
    request_timeout: int = 90
    max_retries: int = 3
    retry_delay: float = 5.0
    user_agent: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
    batch_size: int = 100
    # FIXED: was 1000 — that was a single global cap across ALL sources,
    # causing only ~179 listings after cross-site dedup.
    # 10000 lets each source run to its natural max; dedup handles overlap.
    fetch_limit: int = 10000
    start_date: str = "2024-01-01"


@dataclass
class LogConfig:
    """Logging configuration."""
    level: str = os.getenv("LOG_LEVEL", "INFO")
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file_path: Optional[str] = os.getenv("LOG_FILE", None)


@dataclass
class SchedulerConfig:
    """Scheduler configuration."""
    enabled: bool = True
    default_interval_minutes: int = 60
    banks_interval_minutes: int = 30
    tenders_interval_minutes: int = 60
    listings_interval_minutes: int = 15


@dataclass
class GoogleSheetsConfig:
    """Google Sheets integration configuration."""
    enabled: bool = os.getenv("GOOGLE_SHEETS_ENABLED", "false").lower() == "true"
    spreadsheet_id: str = os.getenv("GOOGLE_SHEETS_SPREADSHEET_ID", "")
    credentials_file: str = os.getenv("GOOGLE_SHEETS_CREDENTIALS_FILE", "credentials.json")
    sheet_name: str = os.getenv("GOOGLE_SHEETS_SHEET_NAME", "Sheet1")


@dataclass
class Config:
    """Main configuration container."""
    db: DatabaseConfig = field(default_factory=DatabaseConfig)
    scraper: ScraperConfig = field(default_factory=ScraperConfig)
    log: LogConfig = field(default_factory=LogConfig)
    scheduler: SchedulerConfig = field(default_factory=SchedulerConfig)
    sheets: GoogleSheetsConfig = field(default_factory=GoogleSheetsConfig)


# Global config instance
config = Config()


def get_config() -> Config:
    """Get the global configuration instance."""
    return config


def update_config(**kwargs) -> None:
    """Update configuration values."""
    if "db_host" in kwargs:
        config.db.host = kwargs["db_host"]
    if "db_port" in kwargs:
        config.db.port = kwargs["db_port"]
    if "db_name" in kwargs:
        config.db.database = kwargs["db_name"]
    if "db_user" in kwargs:
        config.db.user = kwargs["db_user"]
    if "db_password" in kwargs:
        config.db.password = kwargs["db_password"]
