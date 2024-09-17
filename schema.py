import strawberry
from contextlib import asynccontextmanager
from databases import Database
from dotenv import load_dotenv
from fastapi import FastAPI
from functools import partial
from strawberry.types import Info
from strawberry.fastapi import BaseContext, GraphQLRouter
from settings import Settings


load_dotenv()


class Context(BaseContext):
    db: Database

    def __init__(
        self,
        db: Database,
    ) -> None:
        self.db = db



@strawberry.type
class Author:
    name: str


@strawberry.type
class Book:
    title: str
    author: Author


@strawberry.type
class Query:

    @strawberry.field
    async def books(
        self,
        info: Info[Context, None],
        author_ids: list[int] | None = None,
        search: str | None = None,
        limit: int | None = None,
    ) -> list[Book]:
        if not author_ids:
            author_ids = []
        author_ids_str = ','.join([str(author_id) for author_id in author_ids])
        sql_query = "select title, a.name from books inner join authors a on a.id = books.author_id"
        if author_ids or search:
            sql_query += ' where '
        if author_ids:
            sql_query += 'author_id in (' + author_ids_str + ')'
        if search:
            sql_query += "title like '%" + search + "%'"
        if limit is not None:
            sql_query += ' limit ' + str(limit)
        response = await info.context.db.fetch_all(sql_query)
        return [Book(title=book['title'], author=Author(name=book['name'])) for book in response]


CONN_TEMPLATE = "postgresql+asyncpg://{user}:{password}@{host}:{port}/{name}"
settings = Settings()  # type: ignore
db = Database(
    CONN_TEMPLATE.format(
        user=settings.DB_USER,
        password=settings.DB_PASSWORD,
        port=settings.DB_PORT,
        host=settings.DB_SERVER,
        name=settings.DB_NAME,
    ),
)

@asynccontextmanager
async def lifespan(
    app: FastAPI,
    db: Database,
):
    async with db:
        yield
    await db.disconnect()

schema = strawberry.Schema(query=Query)
graphql_app = GraphQLRouter(  # type: ignore
    schema,
    context_getter=partial(Context, db),
)

app = FastAPI(lifespan=partial(lifespan, db=db))
app.include_router(graphql_app, prefix="/graphql")
