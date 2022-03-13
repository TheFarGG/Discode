from __future__ import annotations

__all__ = ("Client",)

import asyncio
import functools
from typing import Any, Dict, List, Optional, Union

import aiohttp

from . import utils
from .connection import Connection
from .enums import GatewayEvent
from .flags import Intents
from .gateway import Gateway
from .http import HTTP
from .models import ClientUser, DMChannel, Guild, Message, TextChannel, User


class Client:

    r"""
    Represents the Client that connects to the Discord Gateway and HTTP Api.

    Parameters
    ----------

    token: :class:`str`
        The token to use to communicate with the gateway and REST APIs.
    intents: :class:`Intents`
        The intents to use while connecting to the gateway. Defaults to :meth:`Intents.all()`.
    loop: :class:`asyncio.AbstractEventLoop`
        The event loop the client should use for asynchronous operations.

    Attributes
    ----------

    token: :class:`str`
        The token used to connect to the REST & gateway APIs.
    intents: :class:`Intents`
        The intents the client is using.
    loop: :class:`asyncio.AbstractEventLoop`
        The event loop used by the client for asynchronous operations.
    """

    def __init__(
        self,
        token: str,
        *,
        intents: Intents = None,
        loop: asyncio.AbstractEventLoop = None,
        api_version: int = 10,
    ):
        self.token: str = token.strip()
        self.loop: asyncio.AbstractEventLoop = (
            loop if loop else asyncio.get_event_loop()
        )
        self.intents: Intents = intents if intents else Intents.all()
        self.api_version: int = api_version
        self._http: HTTP = HTTP(self)
        self._connection: Connection = Connection(self)
        self._listeners: Dict[str, Any] = {}

    @property
    def latency(self) -> float:
        r""""""
        return self._ws.latency

    @property
    def user(self) -> ClientUser:
        return self._user

    @property
    def users(self) -> List[User]:
        return list(self._connection.user_cache.values())

    @property
    def guilds(self) -> List[Guild]:
        return list(self._connection.guild_cache.values())

    @property
    def messages(self) -> List[Message]:
        return list(self._connection.message_cache.values())

    @property
    def channels(self) -> List[Union[TextChannel, DMChannel]]:
        return list(self._connection.channel_cache.values())

    @property
    def dm_channels(self) -> List[DMChannel]:
        return [c for c in self._connection.channel_cache.values() if c.type == 1]

    @property
    def invite_url(self) -> str:
        return utils.invite_url(client_id=self.user.id)

    @property
    def session(self) -> aiohttp.ClientSession:
        return self._http._session

    async def run_task(self, *args, **kwargs):
        self._user = await self._http.login()
        ws_options = kwargs.pop("ws_options", {})
        self._ws: Gateway = Gateway(self)
        await self._ws.connect(**ws_options)

    def run(self, *args, **kwargs):
        r"""The :meth:`Client.run()` is similar to :meth:`Client.run_task()` but is a normal function and not a coroutine. The library recommends users to use this to start the bot as this function handles closing the client without raising any errors and runs till the client is alive."""
        loop = self.loop

        async def runner():
            await self.run_task(*args, **kwargs)

        def stop(f):
            asyncio.ensure_future(self.close())
            loop.stop()

        future = asyncio.ensure_future(runner(), loop=loop)
        future.add_done_callback(stop)
        try:
            loop.run_forever()
        except KeyboardInterrupt:
            pass
        finally:
            future.remove_done_callback(stop)

    async def close(self):
        await self._http.logout()
        await self._http.close()

    def on_event(self, event: Union[str, GatewayEvent]):
        r"""Decorator to register event listeners to the client. The function decorated must be a coroutine. This decorator uses :meth:`Client.add_listener()` to register the listener.

        Parameters
        ----------

        event: :class:`str`
            The event the listener should be registered for.
        Raises
        ------

        TypeError
            The function decorated isn't a coroutine.
        """

        def wrapper(func):
            if not asyncio.iscoroutinefunction(func):
                raise TypeError(
                    f"Couldn't register {func} as a listener as it was of type {type(func)} and the library expected a coroutine!"
                )
            self.add_listener(func, event)
            return func

        return wrapper

    def add_listener(self, coro, event):
        if event not in vars(GatewayEvent).values():
            raise Exception(f"Invalid Listener: {event}")
        if event in self._listeners:
            self._listeners.append(coro)
        else:
            self._listeners[event] = [coro]

    async def dispatch(self, event, *args, **kwargs):
        ev = getattr(self, f"on_{event}", None)
        if asyncio.iscoroutinefunction(ev):
            await ev(*args, **kwargs)
        listeners = self._listeners.get(event, [])
        for l in listeners:
            self.loop.create_task(l(*args, **kwargs))

    async def wait_for(self, event, check, *, timeout=30):
        listener = self._ws.wait_for(event, check)
        fut = listener.future
        try:
            return await asyncio.wait_for(fut, timeout=timeout)
        except asyncio.TimeoutError as exc:
            fut.cancel()
            try:
                del listener
            except:
                pass
            raise exc
