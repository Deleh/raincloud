#!/usr/bin/env python

import crypt
import toml
import uuid
import werkzeug
from datetime import datetime, timedelta
from hmac import compare_digest as compare_hash
from flask import (
    abort,
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
sessions = []


class RaincloudIOException(Exception):
    pass


def clean_sessions():
    global sessions
    sessions = [s for s in sessions if s[0] > datetime.now() - timedelta(days=1)]


def validate_session(directory, id_):
    global sessions
    valid_dates = [s[0] for s in sessions if s[1] == directory and s[2] == id_]
    if len(valid_dates) > 0 and valid_dates[0] > datetime.now() - timedelta(days=1):
        return True
    return False


def delete_session(id_):
    global sessions
    sessions = [s for s in sessions if s[2] != id_]


def get_session_id():
    global sessions
    ids = [s[2] for s in sessions]
    id_ = uuid.uuid4()
    while id_ in ids:
        id_ = uuid.uuid4()
    return id_


def get_config(directory):
    """Load a 'rc.toml' file from given directory.

    Parameters:
        directory - basepath of 'mincloud.conf'

    Returns: Dictionary of config parameters
    """
    path = base_path / directory / "rc.toml"

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
def directory(directory, filename=None):
    global sessions
    try:

        # Clean sessions
        clean_sessions()

        # Logout
        if request.method == "POST" and "logout" in request.form:
            delete_session(session[directory])
            return redirect(url_for("directory", directory=directory))

        config = get_config(directory)
        if config["hashed_password"]:
            authenticated = (
                True
                if directory in session
                and validate_session(directory, session[directory])
                else False
            )

            if not authenticated:
                if request.method == "POST":
                    if compare_hash(
                        config["hashed_password"],
                        crypt.crypt(
                            request.form["password"], config["hashed_password"]
                        ),
                    ):
                        id_ = get_session_id()
                        session[directory] = id_
                        sessions.append((datetime.now(), directory, id_))
                    return redirect(url_for("directory", directory=directory))
                else:
                    return render_template(
                        "authenticate.html", cloud_name=cloud_name, config=config
                    )

        if request.method == "GET":
            # List
            if not filename:
                files = get_files(directory)
                return render_template(
                    "directory.html", cloud_name=cloud_name, config=config, files=files
                )

            # Download
            else:
                if config["download"] and filename != "rc.toml":
                    return send_from_directory(base_path / directory, filename)
                else:
                    abort(403)

        # Upload
        elif request.method == "POST":
            if config["upload"]:
                f = request.files["file"]
                filename = secure_filename(f.filename)
                if filename != "rc.toml":
                    f.save(base_path / directory / filename)

                # Reload
                return redirect(url_for("directory", directory=directory))
            else:
                abort(403)

    except RaincloudIOException as e:
        print(e)
        abort(404)


app.secret_key = "raincloud"
app.run(host="0.0.0.0", debug=True)
