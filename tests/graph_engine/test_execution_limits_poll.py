import queue
import time
from unittest.mock import MagicMock

from graphon.graph_engine.command_channels.in_memory_channel import InMemoryChannel
from graphon.graph_engine.command_processing import (
    AbortCommandHandler,
    CommandProcessor,
)
from graphon.graph_engine.domain.graph_execution import GraphExecution
from graphon.graph_engine.entities.commands import AbortCommand
from graphon.graph_engine.event_management import EventManager
from graphon.graph_engine.layers.execution_limits import ExecutionLimitsLayer
from graphon.graph_engine.orchestration.dispatcher import Dispatcher


class CommandProcessingCoordinator:
    paused = False
    execution_complete = False

    def __init__(
        self,
        graph_execution: GraphExecution,
        command_processor: CommandProcessor,
    ) -> None:
        self._graph_execution = graph_execution
        self._command_processor = command_processor
        self.completed = False

    @property
    def aborted(self) -> bool:
        return self._graph_execution.aborted

    def check_scaling(self) -> None:
        pass

    def process_commands(self) -> None:
        self._command_processor.process_commands()

    def mark_complete(self) -> None:
        self.completed = True

    def mark_failed(self, error: Exception) -> None:
        raise error

    def has_executing_nodes(self) -> bool:
        return False


def test_execution_limits_layer_sends_time_limit_abort_on_dispatcher_poll() -> None:
    layer = ExecutionLimitsLayer(max_steps=999, max_time=1)
    layer.command_channel = MagicMock()
    layer.on_graph_start()
    layer.start_time = time.time() - 2

    layer.on_dispatcher_poll(now=0.0, elapsed=2.0)

    abort_command = layer.command_channel.send_command.call_args.args[0]
    assert isinstance(abort_command, AbortCommand)
    assert abort_command.reason is not None
    assert abort_command.reason.startswith("Maximum execution time exceeded:")


def test_dispatcher_poll_abort_command_aborts_execution() -> None:
    channel = InMemoryChannel()
    graph_execution = GraphExecution(workflow_id="workflow-1", started=True)
    command_processor = CommandProcessor(
        command_channel=channel,
        graph_execution=graph_execution,
    )
    command_processor.register_handler(AbortCommand, AbortCommandHandler())

    layer = ExecutionLimitsLayer(max_steps=999, max_time=1)
    layer.command_channel = channel
    layer.on_graph_start()
    layer.start_time = time.time() - 2

    event_manager = EventManager()
    event_manager.set_layers([layer])
    dispatcher = Dispatcher(
        event_queue=queue.Queue(),
        event_handler=MagicMock(),
        execution_coordinator=CommandProcessingCoordinator(
            graph_execution,
            command_processor,
        ),  # type: ignore[arg-type]
        event_emitter=event_manager,
    )

    dispatcher.start()
    time.sleep(0.25)
    dispatcher.stop()

    assert graph_execution.aborted is True
    assert graph_execution.error is not None
    assert str(graph_execution.error).startswith(
        "Aborted: Maximum execution time exceeded:",
    )
