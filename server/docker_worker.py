"""
Celery-like task queue implemented using Faust

"""

import random
import asyncio

from typing import (Any, Awaitable,
                    Callable, Mapping,
                    MutableMapping, Sequence, Optional)
import faust
from faust import cli
import docker
import time
from loguru import logger
from mode.utils.objects import qualname
from faust.livecheck import Case, Signal
import arctic

class Request(faust.Record):
    """Describes how tasks are serialized and sent to Kafka."""

    #: Correlation ID, can be used to pass results back to caller.
    id: str

    #: Name of the task as registered in the task_registry.
    name: str
    #: Positional arguments to the task.
    arguments: Sequence
    #: Keyword arguments to the task.
    keyword_arguments: Mapping
    output: Optional[str]

    async def __call__(self) -> Any:
        if self.handler:
            return await self.handler(*self.arguments,
                                      **self.keyword_arguments)

    @property
    def handler(self) -> Callable[..., Awaitable]:
        return task_registry.get(self.name, None)


app = faust.App('pipelime-docker',
                origin='task-job.livecheck',
                broker='kafka://localhost:9092')

livecheck = app.LiveCheck()

docker_hook = docker.from_env()

task_queue_topic = app.topic('tasks', value_type=Request)
task_result_topic = app.topic('tasks-output', value_type=Request)

task_registry: MutableMapping[str, Callable[..., Awaitable]]

task_registry = {}


@app.agent(task_queue_topic)
async def process_task(tasks: faust.Stream[Request]) -> None:
    """A "worker" stream processor that executes tasks."""
    async for task in tasks:
        print(f'Processing task: {task!r}')
        out = await task()
        task.output = out

        # sending topic
        await task_result_topic.send(value=task)
        print(f'Result of {task.id} is: {out!r}')
        yield task


class Task:
    def __init__(self, fun: Callable[..., Awaitable], *,
                 name: str = None) -> None:
        self.fun: Callable[..., Awaitable] = fun
        self.name = name or qualname(fun)

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        return self.fun(*args, **kwargs)

    async def delay(self, *args: Any, **kwargs: Any) -> Any:
        return await self.apply_async(args, kwargs)

    async def apply_async(self,
                          args: Sequence,
                          kwargs: Mapping,
                          id: str = None,
                          **options: Any) -> None:
        id = id or faust.uuid()
        return await process_task.send(
            value=Request(
                id=id, name=self.name,
                arguments=args, keyword_arguments=kwargs))


def task(fun: Callable) -> Task:
    # Task decorator
    task = Task(fun)
    task_registry[task.name.split(".")[-1]] = task
    return task


@task
async def docker_task(image, command):
    container = docker_hook.containers.run(
        image=image, command=command, stdout=True)
    return container


@livecheck.case(frequency=0.5, probability=0.5)
class test_task(Case):

    task_sent_to_kafka: Signal[Request]
    task_executed: Signal[str]

    async def run(self) -> None:
        # 1) wait for order to be sent to database.

        # contract:
        #   order id matches test execution id
        #   order.side matches test argument side.

        # 2) wait for order to be sent to Kafka
        await self.order_sent_to_kafka.wait(timeout=30.0)
        # 3) wait for redis index to be updated.
        # 4) wait for execution agent to execute the order.
        await self.order_executed.wait(timeout=30.0)


@app.command(
    cli.option('--name', default=''),
    cli.option('--image', default=''),
    cli.option('--command', default=''),
)
async def post_task(self: cli.AppCommand, name: str, image: str, command: str) -> None:
    print(f"Availiable Tasks: {'.'.join(list(task_registry.keys()))}")
    task = Request(id=faust.uuid(), name=name, arguments=[],
                   keyword_arguments={"image": image, "command": command})
    await task_queue_topic.send(value=task)

if __name__ == '__main__':
    app.main()
