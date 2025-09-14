from flask import Flask, render_template

def create_app():
    app = Flask(__name__, template_folder="templates", static_folder="static")

    @app.route("/")
    def index():
        return render_template("index.html")

    @app.route("/view")
    def view_json():
        return render_template("view_json.html")

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=5000, debug=True)
