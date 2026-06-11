from time import time

from graphon.runtime import CancellationToken
from graphon.runtime.graph_runtime_state import GraphRuntimeState
from graphon.runtime.variable_pool import VariablePool


def test_cancellation_token_defaults_to_fresh_token() -> None:
    state = GraphRuntimeState(variable_pool=VariablePool(), start_at=time())

    assert state.cancellation_token.cancelled is False
    assert state.cancellation_token.cancel("timeout") is True
    assert state.cancellation_token.reason == "timeout"


def test_cancellation_token_can_be_injected() -> None:
    token = CancellationToken()

    state = GraphRuntimeState(
        variable_pool=VariablePool(),
        start_at=time(),
        cancellation_token=token,
    )

    assert state.cancellation_token is token


def test_child_runtime_state_shares_parent_cancellation_token() -> None:
    parent = GraphRuntimeState(variable_pool=VariablePool(), start_at=time())

    child = parent.create_child_runtime_state(start_at=time())

    assert child.cancellation_token is parent.cancellation_token
    assert child.cancellation_token.cancel("timeout") is True
    assert parent.cancellation_token.cancelled is True
    assert parent.cancellation_token.reason == "timeout"
