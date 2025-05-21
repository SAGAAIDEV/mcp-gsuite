from pydantic_settings import BaseSettings


from pathlib import Path
from pydantic_settings import BaseSettings
from pydantic import Field


class GSuiteConfig(BaseSettings):
    credentials_dir: str = Field(
        "/Users/andrew/saga/mcp-servers/operations/mcp-gsuite/.credentials",
        env="GSUITE_CREDENTIALS_DIR",
    )
    accounts_file: str = Field(".accounts.json", env="GSUITE_ACCOUNTS_FILE")
    client_secrets_file: str = Field(".client_secret.json", env="GSUITE_ACCOUNTS_FILE")

    class Config:
        env_prefix = "GSUITE_"

    def get_client_secrets_file(self) -> Path:
        """Return the Path to the client_secret.json file in the credentials_dir and verify it exists."""
        path = Path(self.credentials_dir) / ".client_secret.json"
        if not path.is_file():
            raise FileNotFoundError(f"client_secret.json not found at {path}")
        return path

    def get_accounts_file(self) -> Path:
        """Return the Path to the accounts file and verify it exists."""
        path = Path(self.credentials_dir) / self.accounts_file
        if not path.is_file():
            raise FileNotFoundError(f"Accounts file not found at {path}")
        return path

    def verify_credentials_dir(self) -> None:
        """Verify that the credentials directory exists."""
        path = Path(self.credentials_dir)
        if not path.is_dir():
            raise FileNotFoundError(f"Credentials directory not found at {path}")


gsuite_config = GSuiteConfig()
