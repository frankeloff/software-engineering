from dishka import make_async_container

import config

from . import providers

container = make_async_container(
    providers.AppProvider(),
    providers.RedisProvider(),
    context={config.Settings: config.settings},
)
