import queue
import time
from unittest.mock import MagicMock

from graphon.graph_engine.event_management import EventManager
from graphon.graph_engine.layers.base import GraphEngineLayer
from graphon.graph_engine.orchestration.dispatcher import Dispatcher
from graphon.graph_events.base import GraphEngineEvent


class PollRecordingLayer(GraphEngineLayer):
    def __init__(self) -> None:
        super().__init__()
        self.polls: list[tuple[float, float]] = []

    def on_graph_start(self) -> None:
        pass

    def on_event(self, event: GraphEngineEvent) -> None:
        _ = event

    def on_dispatcher_poll(self, now: float, elapsed: float) -> None:
        self.polls.append((now, elapsed))

    def on_graph_end(self, error: Exception | None) -> None:
        _ = error


class FakeExecutionCoordinator:
    aborted = False
    execution_complete = False
    paused = False

    def __init__(self) -> None:
        self.completed = False

    def check_scaling(self) -> None:
        pass

    def process_commands(self) -> None:
        pass

    def mark_complete(self) -> None:
        self.completed = True

    def mark_failed(self, error: Exception) -> None:
        raise error

    def has_executing_nodes(self) -> bool:
        return False


def test_dispatcher_poll_notifies_layers_without_buffering_events() -> None:
    layer = PollRecordingLayer()
    event_manager = EventManager()
    event_manager.set_layers([layer])

    event_manager.notify_dispatcher_poll(now=10.0, elapsed=2.5)
    event_manager.mark_complete()

    assert layer.polls == [(10.0, 2.5)]
    assert list(event_manager.emit_events()) == []


def test_dispatcher_idle_loop_notifies_layer_poll() -> None:
    layer = PollRecordingLayer()
    event_manager = EventManager()
    event_manager.set_layers([layer])
    dispatcher = Dispatcher(
        event_queue=queue.Queue(),
        event_handler=MagicMock(),
        execution_coordinator=FakeExecutionCoordinator(),  # type: ignore[arg-type]
        event_emitter=event_manager,
    )

    dispatcher.start()
    time.sleep(0.25)
    dispatcher.stop()

    assert len(layer.polls) >= 1
    assert all(elapsed >= 0 for _, elapsed in layer.polls)
