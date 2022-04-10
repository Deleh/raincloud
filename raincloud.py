#!/usr/bin/env python

import toml
import werkzeug
from flask import (
    Flask,
    render_template,
    redirect,
    request,
    send_from_directory,
    session,
    url_for,
)
from pathlib import Path
from werkzeug.utils import secure_filename

base_path = Path("public")
cloud_name = "raincloud"


class MincloudIOException(Exception):
    pass


def get_config(directory):
    """Load a 'mincloud.conf' file from given directory.

    Parameters:
        directory - basepath of 'mincloud.conf'

    Returns: Dictionary of config parameters
    """
    path = base_path / directory / "rc.toml"

    if path.exists():
        config = {}
        config["directory"] = directory

        parsed_config = toml.load(path)
        config["password"] = (
            parsed_config["password"] if "password" in parsed_config else None
        )
        config["download"] = (
            parsed_config["download"] if "download" in parsed_config else False
        )
        config["upload"] = (
            parsed_config["upload"] if "upload" in parsed_config else False
        )
        return config

    else:
        raise MincloudIOException("No raincloud directory")


def get_files(directory):
    path = base_path / directory
    file_paths = [f for f in path.glob("*") if f.is_file()]
    files = []
    for p in file_paths:
        if p.name != "rc.toml":
            files.append({"name": p.name})
    return files


app = Flask(__name__)


@app.route("/<directory>", methods=["GET", "POST"])
@app.route("/<directory>/<path:filename>", methods=["GET"])
def files(directory, filename=None):

    try:
        config = get_config(directory)
        if config["password"]:
            authenticated = False
            if directory in session and session[directory] == config["password"]:
                authenticated = True

            if not authenticated:
                if request.method == "POST":
                    if request.form["password"] == config["password"]:
                        session[directory] = config["password"]
                    return redirect(url_for("files", directory=directory))
                else:
                    return render_template(
                        "authenticate.html", cloud_name=cloud_name, config=config
                    )

        if request.method == "GET":
            # List
            if not filename:
                files = get_files(directory)
                return render_template(
                    "files.html", cloud_name=cloud_name, config=config, files=files
                )

            # Download
            else:
                if config["download"] and filename != "rc.toml":
                    return send_from_directory(base_path / directory, filename)
                else:
                    return "Not allowed"

        # Upload
        elif request.method == "POST":
            if config["upload"]:
                f = request.files["file"]
                filename = secure_filename(f.filename)
                if filename != "rc.toml":
                    f.save(base_path / directory / filename)

                # Return new file list
                files = get_files(directory)
                return render_template(
                    "files.html", cloud_name=cloud_name, config=config, files=files
                )
            else:
                return "No upload allowed"

    except MincloudIOException as e:
        print(e)
        return "No 404 file"


app.secret_key = "raincloud"
app.run(host="0.0.0.0", debug=True)
