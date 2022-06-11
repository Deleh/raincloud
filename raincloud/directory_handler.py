from datetime import datetime
from pathlib import Path
import configparser
import os


def get_human_readable_filesize(num_bytes):
    """Return a human readable string of 'num_bytes'."""
    print(num_bytes)
    for unit in ["", "Ki", "Mi", "Gi", "Ti", "Pi", "Ei", "Zi"]:
        if abs(num_bytes) < 1024.0:
            return f"{num_bytes:3.1f} {unit}B"
        num_bytes /= 1024.0
    return f"{num_bytes:.1f} YiB"


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
        """Load a 'rc.conf' file from given directory.

        Parameters:
            directory - basepath of 'rc.conf'

        Returns: Dictionary of config parameters
        """
        path = self.base_path / directory / "rc.conf"

        if path.exists():
            config = {}
            config["directory"] = directory

            config_parser = configparser.ConfigParser()
            config_parser.read(path)

            if not "raincloud" in config_parser:
                raise RaincloudIOException(
                    f"Malformed configuration file in directory '{directory}'"
                )

            parsed_config = dict(config_parser["raincloud"])

            config["hashed_password"] = (
                parsed_config["hashed_password"]
                if "hashed_password" in parsed_config
                else None
            )
            config["download"] = False
            if (
                "download" in parsed_config
                and parsed_config["download"].lower() == "true"
            ):
                config["download"] = True
            config["upload"] = False
            if "upload" in parsed_config and parsed_config["upload"].lower() == "true":
                config["upload"] = True
            return config

        else:
            raise RaincloudIOException(f"No raincloud directory '{directory}'")

    def get_files(self, directory):
        """Get files from directory."""
        path = self.base_path / directory
        file_paths = [f for f in path.glob("*") if f.is_file()]
        files = []
        for p in file_paths:
            if p.name != "rc.conf":
                print(p)
                files.append(
                    {
                        "name": p.name,
                        "size": get_human_readable_filesize(os.path.getsize(p)),
                    }
                )
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
