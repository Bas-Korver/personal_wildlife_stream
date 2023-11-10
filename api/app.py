import flask
from flask_restful import Resource, Api

app = flask.Flask(__name__)
api = Api(app)


if __name__ == "__main__":
    app.run(debug=True)