"""
Configuration settings for Ollaa Web Scraper.
Manages database connection, scraper delays, and global settings.
"""
import os
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class DatabaseConfig:
    """PostgreSQL database configuration."""
    host: str = os.getenv("OLLAADB_HOST", "localhost")
    port: int = int(os.getenv("OLLAADB_PORT", "5432"))
    database: str = os.getenv("OLLAADB_NAME", "ollaa")
    user: str = os.getenv("OLLAADB_USER", "postgres")
    password: str = os.getenv("OLLAADB_PASSWORD", "postgres")
    
    @property
    def connection_string(self) -> str:
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"


@dataclass
class ScraperConfig:
    """Scraper behavior configuration."""
    request_delay_min: float = 2.0
    request_delay_max: float = 5.0
    request_timeout: int = 30
    max_retries: int = 3
    retry_delay: float = 5.0
    user_agent: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
    batch_size: int = 100
    fetch_limit: int = 1000
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