from typing import Annotated, AsyncIterator

import redis.asyncio as redis
from dishka import FromComponent, Provider, Scope, from_context, provide

import config

SERVICE_TOKEN = "ServiceToken"


class AppProvider(Provider):
    component = "AppProvider"

    settings = from_context(provides=config.Settings, scope=Scope.APP)


class RedisProvider(Provider):
    component = "RedisProvider"

    @provide(scope=Scope.APP)
    async def _init_redis_pool(
        self,
        settings: Annotated[config.Settings, FromComponent("AppProvider")],
    ) -> AsyncIterator[redis.ConnectionPool]:
        """
        Провайдер, поставляющий пул подключений для БД Редис
        Является зависимостью для получения устройства доступа и не предназначен для вызова извне
        """

        redis_pool = redis.ConnectionPool.from_url(
            f"rediss://:{settings.redis_password}@{settings.redis_host}:{settings.redis_port}",
        )

        yield redis_pool

        await redis_pool.aclose()

    @provide(scope=Scope.REQUEST)
    async def get_redis_client(
        self,
        redis_pool: redis.ConnectionPool,
        settings: Annotated[config.Settings, FromComponent("AppProvider")],
    ) -> AsyncIterator[redis.Redis]:
        """
        Провайдер, поставляющий устройства доступа для обращения в БД Редис
        Используется извне
        """

        redis_client = redis.Redis(
            host=settings.redis_host,
            port=settings.redis_port,
            password=settings.redis_password,
        )

        yield redis_client

        await redis_client.aclose()
