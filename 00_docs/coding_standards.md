# Unified Recommendation Engine: Coding Standards & Architecture

## 1. Architectural Principles
We follow a **Layered Service Architecture**. The goal is to keep the codebase modular, testable, and scalable.

### A. The "Thin Controller" Rule
API Route handlers (`app/api/*.py`) must be "thin." Their only responsibilities are:
*   Request validation (via Pydantic).
*   Calling the appropriate Service method.
*   Formatting the success response or raising an `HTTPException`.
*   **Prohibited:** API routes must NOT contain business logic, raw Qdrant queries, or manual embedding calls.

### B. Service-Oriented Logic
Business logic resides in the `app/services/` layer.
*   **Granularity:** Services should have a single responsibility.
*   **Statelessness:** Services should rely on the `core/config.py` or passed parameters, not internal state.
*   **Refactoring Goal:** As a service grows beyond 300 lines, it must be split (e.g., `qdrant.py` -> `indexer.py` and `discovery.py`).

---

## 2. Technical Standards

### A. Error Handling & Exceptions
*   **No "Catch-All" blocks:** Avoid `except Exception:`. Always catch specific errors (e.g., `httpx.TimeoutException`).
*   **Custom Exceptions:** Define domain-specific exceptions in a new `app/core/exceptions.py`.
*   **Logging:** Every failure must be logged with context (e.g., `store_id`, `product_id`) before raising an exception.

### B. Type Safety & Validation
*   **Strict Typing:** Use Python type hints for all function signatures and variables.
*   **Schema Evolution:** When adding fields to `ProductMetadata`, ensure they are `Optional` to maintain backward compatibility with existing synced data.
*   **Input Sanitization:** Filters must be passed through `translate_filters` to ensure tenant isolation (`store_id`) is always enforced.

### C. Performance & Concurrency
*   **Async Everywhere:** All I/O bound operations (DB, API, Files) MUST use `async/await`.
*   **Batching:** Use batch operations for Qdrant upserts and Jina AI embeddings whenever possible.
*   **Connection Pooling:** Use persistent, shared clients (e.g., `AsyncQdrantClient`, `httpx.AsyncClient`) initialized at startup via the FastAPI `lifespan`.

---

## 3. Multi-tenancy & Security
*   **Partition Key:** The `store_id` is the mandatory partition key. No query should ever execute without a `store_id` filter.
*   **Credential Protection:** Never log API keys or secrets. Use `logging.filter` or mask sensitive values in logs.

---

## 4. Documentation & Style
*   **Docstrings:** Every public function/method must have a Google-style docstring explaining its purpose, parameters, and return value.
*   **Naming:** 
    *   Functions/Variables: `snake_case`
    *   Classes: `PascalCase`
    *   Constants: `UPPER_SNAKE_CASE`
*   **DRY (Don't Repeat Yourself):** If logic (like MMR or Filter translation) is used in two different API routers, it must be moved to `app/utils/`.
