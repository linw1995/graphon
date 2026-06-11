from graphon.graph_engine.command_processing import AbortCommandHandler
from graphon.graph_engine.domain.graph_execution import GraphExecution
from graphon.graph_engine.entities.commands import AbortCommand
from graphon.runtime import CancellationToken


def test_abort_command_handler_cancels_token_and_aborts_execution() -> None:
    token = CancellationToken()
    execution = GraphExecution(workflow_id="workflow-1", started=True)
    handler = AbortCommandHandler(token)

    handler.handle(AbortCommand(reason="timeout"), execution)

    assert token.cancelled is True
    assert token.reason == "timeout"
    assert execution.aborted is True
    assert str(execution.error) == "Aborted: timeout"


def test_abort_command_handler_keeps_existing_cancellation_reason() -> None:
    token = CancellationToken()
    execution = GraphExecution(workflow_id="workflow-1", started=True)
    handler = AbortCommandHandler(token)

    assert token.cancel("external stop") is True
    handler.handle(AbortCommand(reason="timeout"), execution)

    assert token.reason == "external stop"
    assert execution.aborted is True
    assert str(execution.error) == "Aborted: timeout"
