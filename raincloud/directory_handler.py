from datetime import datetime
from pathlib import Path
import toml


class RaincloudIOException(Exception):
    pass


class DirectoryHandler:
    def __init__(self, base_path):
        self.base_path = Path(base_path)
        if not self.base_path.exists():
            raise RaincloudIOException(
                f"Base path '{self.base_path.resolve()}' not existent"
            )

    def get_config(self, directory):
        """Load a 'rc.toml' file from given directory.

        Parameters:
            directory - basepath of 'rc.toml'

        Returns: Dictionary of config parameters
        """
        path = self.base_path / directory / "rc.toml"

        if path.exists():
            config = {}
            config["directory"] = directory

            parsed_config = toml.load(path)
            config["hashed_password"] = (
                parsed_config["hashed_password"]
                if "hashed_password" in parsed_config
                else None
            )
            config["download"] = (
                parsed_config["download"] if "download" in parsed_config else False
            )
            config["upload"] = (
                parsed_config["upload"] if "upload" in parsed_config else False
            )
            return config

        else:
            raise RaincloudIOException("No raincloud directory")

    def get_files(self, directory):
        """Get files from directory."""
        path = self.base_path / directory
        file_paths = [f for f in path.glob("*") if f.is_file()]
        files = []
        for p in file_paths:
            if p.name != "rc.toml":
                files.append(p.name)
        return files

    def get_absolute_path(self, directory):
        """Get absolute path of 'directory'."""
        return (self.base_path / directory).resolve()

    def save_to_directory(self, file_, directory, filename):
        """Save 'file_' to 'directory' with 'filename'."""
        filepath = self.base_path / directory / filename
        if not filepath.exists():
            file_.save(filepath)
        else:
            file_.save(
                filepath.with_suffix(
                    f".{datetime.now().strftime('%Y%m%d%H%M')}{filepath.suffix}"
                )
            )
