from flask import Flask, Response, jsonify, request
from flask.views import MethodView
from flask_bcrypt import Bcrypt
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from db import Advertisement, Session, User
from errors import HttpError
from schema import CreateAdvertisement, CreateUser, UpdateAdvertisement, validate

app = Flask("app")
bcrypt = Bcrypt(app)


def hash_password(password: str) -> str:
    password = password.encode()
    password = bcrypt.generate_password_hash(password)
    password = password.decode()
    return password


def check_password(password: str, password_hash: str) -> bool:
    return bcrypt.check_password_hash(password_hash, password.encode())


@app.before_request
def before_request():
    session = Session()
    request.session = session


@app.after_request
def after_requests(response: Response):
    request.session.close()
    return response


@app.errorhandler(HttpError)
def error_handler(err: HttpError):
    response = jsonify({"error": err.message})
    response.status_code = err.status_code
    return response


def get_user(user_id: int) -> User:
    user = request.session.get(User, user_id)
    if user is None:
        raise HttpError("user not found", 404)
    return user


def get_advertisement(advertisement_id: int) -> Advertisement:
    advertisement = request.session.get(Advertisement, advertisement_id)
    if advertisement is None:
        raise HttpError("advertisement not found", 404)
    return advertisement


def add_user(user: User):
    request.session.add(user)
    try:
        request.session.commit()
    except IntegrityError:
        raise HttpError("user already exists", 400)


def get_current_user() -> User:
    auth = request.authorization
    if auth is None or not auth.username or not auth.password:
        raise HttpError("unauthorized", 401)

    user = request.session.scalar(select(User).where(User.email == auth.username))
    if user is None or not check_password(auth.password, user.password):
        raise HttpError("unauthorized", 401)
    return user


def check_owner(advertisement: Advertisement, user: User):
    if advertisement.owner_id != user.id:
        raise HttpError("forbidden", 403)


class UserView(MethodView):
    def get(self, user_id: int):
        user = get_user(user_id)
        return jsonify(user.dict)

    def post(self):
        json_data = validate(request.json, CreateUser)
        user = User(
            email=json_data["email"],
            password=hash_password(json_data["password"]),
        )
        add_user(user)
        return jsonify(user.id_dict), 201


class AdvertisementView(MethodView):
    def get(self, advertisement_id: int):
        advertisement = get_advertisement(advertisement_id)
        return jsonify(advertisement.dict)

    def post(self):
        user = get_current_user()
        json_data = validate(request.json, CreateAdvertisement)
        advertisement = Advertisement(
            title=json_data["title"],
            description=json_data["description"],
            owner_id=user.id,
        )
        request.session.add(advertisement)
        request.session.commit()
        return jsonify(advertisement.id_dict), 201

    def patch(self, advertisement_id: int):
        user = get_current_user()
        advertisement = get_advertisement(advertisement_id)
        check_owner(advertisement, user)

        json_data = validate(request.json, UpdateAdvertisement)
        if "title" in json_data:
            advertisement.title = json_data["title"]
        if "description" in json_data:
            advertisement.description = json_data["description"]

        request.session.add(advertisement)
        request.session.commit()
        return jsonify(advertisement.dict)

    def delete(self, advertisement_id: int):
        user = get_current_user()
        advertisement = get_advertisement(advertisement_id)
        check_owner(advertisement, user)

        request.session.delete(advertisement)
        request.session.commit()
        return jsonify({"message": "deleted"})


user_view = UserView.as_view("user")
advertisement_view = AdvertisementView.as_view("advertisement")

app.add_url_rule("/users", view_func=user_view, methods=["POST"])
app.add_url_rule("/users/<int:user_id>", view_func=user_view, methods=["GET"])
app.add_url_rule("/advertisements", view_func=advertisement_view, methods=["POST"])
app.add_url_rule(
    "/advertisements/<int:advertisement_id>",
    view_func=advertisement_view,
    methods=["GET", "PATCH", "DELETE"],
)


if __name__ == "__main__":
    app.run()
