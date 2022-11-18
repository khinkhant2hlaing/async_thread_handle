"""One solution: Use a decorator to poll for the disconnect"""
from random import random
import asyncio
from functools import wraps
from typing import Any, Awaitable, Callable
from fastapi import FastAPI, Query, Request, HTTPException
import uvicorn
import time

app = FastAPI(title="Disconnect example")


async def disconnect_poller(request: Request, result: Any):
    """
    Poll for a disconnect.
    If the request disconnects, stop polling and return.
    """
    try:
        while not await request.is_disconnected():
            await asyncio.sleep(0.01)
            print("working")
            result = await randomNumberGenerator(request)
            if result:
                break

        print("Request disconnected")

        return result
    except asyncio.CancelledError:
        print("Stopping polling loop")
        return 'request is aborted'

async def randomNumberGenerator(request):
    """
    Generate a random number every 2 seconds and emit to a socketio instance (broadcast)
    Ideally to be run in a separate thread?
    """
    #infinite loop of magical random numbers
    print("Making random numbers")
    count = 1
    while not await request.is_disconnected():
        if count>10:
            break
        number = round(random()*10, 3)
        count+=1
        print(number)
        time.sleep(2)
    return f'random {number}'



def cancel_on_disconnect(handler: Callable[[Request], Awaitable[Any]]):
    """
    Decorator that will check if the client disconnects,
    and cancel the task if required.
    """

    @wraps(handler)
    async def cancel_on_disconnect_decorator(request: Request, *args, **kwargs):
        sentinel = object()

        # Create two tasks, one to poll the request and check if the
        # client disconnected, and another which is the request handler
        poller_task = asyncio.ensure_future(disconnect_poller(request, sentinel))
        handler_task = asyncio.ensure_future(handler(request, *args, **kwargs))

        done, pending = await asyncio.wait(
            [poller_task, handler_task], return_when=asyncio.FIRST_COMPLETED
        )

        # Cancel any outstanding tasks
        for t in pending:
            t.cancel()

            try:
                await t
            except asyncio.CancelledError:
                print(f"{t} was cancelled")
            except Exception as exc:
                print(f"{t} raised {exc} when being cancelled")

        # Return the result if the handler finished first
        if handler_task in done:
            return await handler_task

        # Otherwise, raise an exception
        # This is not exactly needed, but it will prevent
        # validation errors if your request handler is supposed
        # to return something.
        print("Raising an HTTP error because I was disconnected!!")

        raise HTTPException(503)

    return cancel_on_disconnect_decorator


@app.get("/example")
@cancel_on_disconnect
async def example(
    request: Request,
):
    try:
        wait = 20
        print(f"Sleeping for {wait:.2f}")
        await asyncio.sleep(wait)

        print("Sleep not cancelled")

        return f"I waited for {wait:.2f}s and now this is the result"
    except asyncio.CancelledError:
        print("Exiting on cancellation")

#https://stackoverflow.com/questions/36342899/asyncio-ensure-future-vs-baseeventloop-create-task-vs-simple-coroutine
uvicorn.run(app, port=5051)