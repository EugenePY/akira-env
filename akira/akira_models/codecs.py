import faust
import typing


class DataSpec(faust.Record):
    libname: str
    symbols: typing.List[str]


class ModelTask(faust.Record):
    id: str
    image: str
    task: {"TRAIN", "ORDER"}  # training will decode using model_schema
    parameters: typing.Mapping[str, str]
    dataspec: DataSpec

    async def __call__(self) -> Any:
        return await self.handler(task=self.task,
                                  **self.parameters)

    @property
    def handler(self) -> Callable[..., Awaitable]:
        return task_registry[self.model_id]


class ModelRegistery(faust.Record):
    model_id: str
    model_task: typing.Mapping[str, ModelTask]
    model_schema_id: str
