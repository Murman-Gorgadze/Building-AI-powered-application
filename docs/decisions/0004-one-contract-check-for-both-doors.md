# 0004 · Both tool doors check our own contract, not only the MCP SDK's

**Date:** 25 November 2026 · **Proposed by:** Murman Gorgadze · **Agreed by:** Tornike Varshalomidze, by approving the pull request that adds this file

**Context.** `check_reserve` is served two ways: function calling (`src/act.py`) and MCP (`src/mcp_server.py`). The MCP SDK (2.3) builds its own argument model from the function's type hints and validates against that. Run by hand on 25 November, it did two things our contract forbids: it ran `check_reserve` with an extra `action: RESERVE` argument, silently dropping it instead of refusing it, and for `sold_pct: 150` it answered with pydantic's raw text (`1 validation error for check_reserveArguments ... input_value=150 ... https://errors.pydantic.dev/...`), not a message the model can act on.

**Decision.** `FanReserveServer` overrides `MCPServer.call_tool()` to validate every call against the tool's class in `src/contracts.py` (`extra="forbid"` included) before the SDK runs it, and refuses with `tools.invalid_arguments()`, the same message the function-calling door sends.

**Alternatives.** Setting the SDK's generated argument model to forbid extra fields: it would fix the silent drop, but the error text would still be pydantic's. A low-level MCP server with hand-written `list_tools`/`call_tool` handlers: more code, and we would lose the SDK's structured output. Doing nothing: the contract would hold on one door only.

**Consequences.** One gate, one refusal text, two doors. `tests/test_mcp.py` checks that an extra argument is refused through MCP and that both doors send the same refusal; with the plain `MCPServer` those tests fail. If a later SDK version stops calling `call_tool()` from its request handler, these tests are what will notice.
