import asyncio
import inspect

_LOOP = asyncio.new_event_loop()
asyncio.set_event_loop(_LOOP)


def async_run(awaitable):
    if inspect.iscoroutine(awaitable):
        asyncio.set_event_loop(_LOOP)
        return _LOOP.run_until_complete(awaitable)

    if asyncio.isfuture(awaitable):
        loop = awaitable.get_loop()
        asyncio.set_event_loop(loop)
        return loop.run_until_complete(awaitable)

    if inspect.isawaitable(awaitable):
        asyncio.set_event_loop(_LOOP)
        return _LOOP.run_until_complete(awaitable)

    return awaitable
