import base64
import json

from aiohttp import BasicAuth, web
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from auth import check_password, hash_password
from db import Advertisement, Session, User, close_db, init_db
from errors import HttpError
from schema import CreateAdvertisement, CreateUser, UpdateAdvertisement, validate


async def orm_context(app: web.Application):
    print("START")
    await init_db()
    yield
    await close_db()
    print("END")


@web.middleware
async def session_middleware(request: web.Request, handler):
    async with Session() as session:
        request["session"] = session
        return await handler(request)


@web.middleware
async def error_middleware(request: web.Request, handler):
    try:
        return await handler(request)
    except HttpError as err:
        return web.json_response({"error": err.message}, status=err.status_code)


app = web.Application()
app.cleanup_ctx.append(orm_context)
app.middlewares.append(error_middleware)
app.middlewares.append(session_middleware)


def get_error(
    err_cls: type[web.HTTPException],
    err_msg: dict | list | str,
):
    return err_cls(
        text=json.dumps({"error": err_msg}),
        content_type="application/json",
    )


async def get_user(session: AsyncSession, user_id: int) -> User:
    user = await session.get(User, user_id)
    if user is None:
        raise get_error(web.HTTPNotFound, "user not found")
    return user


async def get_advertisement(
    session: AsyncSession, advertisement_id: int
) -> Advertisement:
    result = await session.execute(
        select(Advertisement)
        .options(selectinload(Advertisement.owner))
        .where(Advertisement.id == advertisement_id)
    )
    advertisement = result.scalar_one_or_none()
    if advertisement is None:
        raise get_error(web.HTTPNotFound, "advertisement not found")
    return advertisement


async def add_user(session: AsyncSession, user: User) -> None:
    session.add(user)
    try:
        await session.commit()
    except IntegrityError:
        raise get_error(web.HTTPBadRequest, "user already exists")


def parse_basic_auth(request: web.Request) -> BasicAuth | None:
    header = request.headers.get("Authorization")
    if header is None or not header.startswith("Basic "):
        return None
    try:
        decoded = base64.b64decode(header[6:]).decode()
        username, _, password = decoded.partition(":")
        if not username or not password:
            return None
        return BasicAuth(username, password)
    except Exception:
        return None


async def get_current_user(request: web.Request) -> User:
    auth = parse_basic_auth(request)
    if auth is None:
        raise get_error(web.HTTPUnauthorized, "unauthorized")

    session: AsyncSession = request["session"]
    user = await session.scalar(select(User).where(User.email == auth.login))
    if user is None or not check_password(auth.password, user.password):
        raise get_error(web.HTTPUnauthorized, "unauthorized")
    return user


def check_owner(advertisement: Advertisement, user: User) -> None:
    if advertisement.owner_id != user.id:
        raise get_error(web.HTTPForbidden, "forbidden")


class UserView(web.View):
    @property
    def session(self) -> AsyncSession:
        return self.request["session"]

    @property
    def user_id(self) -> int:
        return int(self.request.match_info["user_id"])

    async def get(self):
        user = await get_user(self.session, self.user_id)
        return web.json_response(user.dict)

    async def post(self):
        json_data = validate(await self.request.json(), CreateUser)
        user = User(
            email=json_data["email"],
            password=hash_password(json_data["password"]),
        )
        await add_user(self.session, user)
        return web.json_response(user.id_dict, status=201)


class AdvertisementView(web.View):
    @property
    def session(self) -> AsyncSession:
        return self.request["session"]

    @property
    def advertisement_id(self) -> int:
        return int(self.request.match_info["advertisement_id"])

    async def get(self):
        advertisement = await get_advertisement(self.session, self.advertisement_id)
        return web.json_response(advertisement.dict)

    async def post(self):
        user = await get_current_user(self.request)
        json_data = validate(await self.request.json(), CreateAdvertisement)
        advertisement = Advertisement(
            title=json_data["title"],
            description=json_data["description"],
            owner_id=user.id,
        )
        self.session.add(advertisement)
        await self.session.commit()
        return web.json_response(advertisement.id_dict, status=201)

    async def patch(self):
        user = await get_current_user(self.request)
        advertisement = await get_advertisement(self.session, self.advertisement_id)
        check_owner(advertisement, user)

        json_data = validate(await self.request.json(), UpdateAdvertisement)
        if "title" in json_data:
            advertisement.title = json_data["title"]
        if "description" in json_data:
            advertisement.description = json_data["description"]

        self.session.add(advertisement)
        await self.session.commit()
        return web.json_response(advertisement.dict)

    async def delete(self):
        user = await get_current_user(self.request)
        advertisement = await get_advertisement(self.session, self.advertisement_id)
        check_owner(advertisement, user)

        await self.session.delete(advertisement)
        await self.session.commit()
        return web.json_response({"message": "deleted"})


app.add_routes(
    [
        web.post("/users", UserView),
        web.get(r"/users/{user_id:\d+}", UserView),
        web.post("/advertisements", AdvertisementView),
        web.get(r"/advertisements/{advertisement_id:\d+}", AdvertisementView),
        web.patch(r"/advertisements/{advertisement_id:\d+}", AdvertisementView),
        web.delete(r"/advertisements/{advertisement_id:\d+}", AdvertisementView),
    ]
)


if __name__ == "__main__":
    web.run_app(app, host="0.0.0.0", port=8080)
