# Backend Refactor Plan

## Objectives
- Remove module-level singletons for pipelines and connection managers.
- Introduce service layer abstractions for pipeline lifecycle and session orchestration.
- Consolidate connection-manager logic into a single configurable implementation.
- Simplify FastAPI routers by injecting dependencies instead of coupling to globals.
- Keep compatibility with existing REST/WebSocket contracts.

## Targeted Changes
1. **Service Layer**
   - `app/services/pipeline_registry.py`: owns initialized `Pipeline`/`RealtimePipeline` instances plus configs, exposes `init`, `get`, `reload`, `shutdown`.
   - `app/services/session_service.py`: wraps `SessionAPI` responsibilities; parameterized by `ConnectionManager`; exposes `create_session`, `websocket`, `stream`, etc.
   - Both services registered during FastAPI lifespan and accessible via dependency injection helpers (`get_canvas_service`, `get_realtime_service`).

2. **Connection Manager Unification**
   - `app/connections/manager.py`: single manager with optional binary-frame parsing helper module (`app/connections/protocol.py`).
   - Behavioural flags: `drain_strategy` (`latest` vs `all`), `supports_binary_frame` (toggles `receive_message`).
   - Remove duplicated `app/connection_manager.py` and `app/api/realtime_connection_manager.py` in favour of new implementation.

3. **Router Simplification**
   - `app/api/canvas.py` and `app/api/realtime.py` import `get_canvas_service` / `get_realtime_service` and delegate endpoints to shared service methods.
   - Routers become thin wrappers containing only FastAPI decorators plus docstrings.

4. **Configuration Builders**
   - `app/config/builders.py`: helper functions `build_canvas_config(settings)` and `build_realtime_config(settings)` used across modules to avoid duplicated dict literals.

5. **Testing**
   - Update `tests/test_realtime_connection_manager.py` to target new unified manager.
   - Add coverage for binary frame parsing, queue draining strategies, and dependency lifecycle (smoke tests for pipeline registry optional depending on time).

## Execution Steps
1. Create configuration builders and service skeletons with unit tests.
2. Replace legacy connection managers with unified implementation; update imports/tests.
3. Refactor routers and `app/main.py` to use the new services and configs.
4. Remove obsolete modules/fields and update documentation (README, DESIGN) if time allows.

## Risks & Mitigations
- **Pipeline lifecycle leaks**: ensure registry `shutdown` is wired to FastAPI `lifespan` or `@app.on_event`. Add try/finally around reload logic.
- **Protocol regression**: maintain legacy binary framing by porting existing `receive_message` logic verbatim into helper, add regression tests.
- **Large diff**: tackle in stages with thorough tests to keep behaviour parity.
