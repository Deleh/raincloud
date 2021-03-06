from hmac import compare_digest as compare_hash
from flask import (
    Flask,
    abort,
    redirect,
    render_template,
    request,
    send_from_directory,
    session,
    url_for,
)
from raincloud.directory_handler import DirectoryHandler, RaincloudIOException
from raincloud.session_handler import SessionHandler
from werkzeug.utils import secure_filename
import crypt
import os
import werkzeug


def create_app(
    base_path,
    secret_key_path,
    redis_url="redis://127.0.0.1:6379/0",
    cloud_name="raincloud",
):

    # Create app
    app = Flask(__name__)
    with open(secret_key_path, "r") as secret_key_file:
        app.config["SECRET_KEY"] = secret_key_file.readline()

    # Create handlers
    dh = DirectoryHandler(base_path)
    sh = SessionHandler(redis_url)

    @app.route("/<directory>", methods=["GET", "POST"])
    @app.route("/<directory>/<path:filename>", methods=["GET"])
    def directory(directory, filename=None):

        try:

            # Clean sessions
            sh.clean_sessions()

            # Logout
            if request.method == "POST" and "logout" in request.form:
                sh.delete_session(session[directory])
                return redirect(url_for("directory", directory=directory))

            config = dh.get_config(directory)

            if config["hashed_password"]:
                authenticated = (
                    True
                    if directory in session
                    and sh.validate_session(directory, session[directory])
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
                            id_ = sh.create_session_id()
                            session[directory] = id_
                            sh.add_session(directory, id_)
                        return redirect(url_for("directory", directory=directory))
                    else:
                        return render_template(
                            "authenticate.html",
                            cloud_name=cloud_name,
                            config=config,
                        )

            if request.method == "GET":
                # List
                if not filename:
                    files = dh.get_files(directory)
                    return render_template(
                        "directory.html",
                        cloud_name=cloud_name,
                        config=config,
                        files=files,
                    )

                # Download
                else:
                    if config["download"] and filename != "rc.conf":
                        return send_from_directory(
                            dh.get_absolute_path(directory),
                            filename,
                            as_attachment=True,
                        )
                    else:
                        abort(404)

            # Upload
            elif request.method == "POST":
                if config["upload"]:
                    f = request.files["file"]
                    filename = secure_filename(f.filename)
                    if filename != "rc.conf":
                        dh.save_to_directory(f, directory, filename)

                    # Reload
                    return redirect(url_for("directory", directory=directory))
                else:
                    abort(403)

        except RaincloudIOException as e:
            print(f"RaincloudIOException: {e}")
            abort(404)
        except Exception as e:
            print(f"Unhandled exception: {e}")
            abort(404)

    return app
