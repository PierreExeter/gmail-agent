# Architectural Patterns

This document describes the reusable design patterns used throughout the Gmail Agent codebase.

## Lazy Initialization

Dependencies are initialized on first access via properties, avoiding startup costs and enabling deferred configuration.

**Pattern:**
```python
def __init__(self):
    self._dependency = None

@property
def dependency(self):
    if self._dependency is None:
        self._dependency = create_dependency()
    return self._dependency
```

**Usage locations:**
- `agent/classifier.py:66-77` - LLM and chain initialization
- `agent/drafter.py:58-77` - LLM and chain initialization
- `agent/scheduler.py:90-117` - LLM, calendar, and chain initialization
- `agent/approval.py:45-50` - Database initialization
- `services/llm_service.py:56-61` - Inference client initialization
- `services/gmail_service.py:73-78` - Gmail service initialization
- `db/database.py:22-36` - Engine and session factory initialization

## Context Manager Sessions

Database sessions use context managers for transaction safety with automatic commit/rollback.

**Pattern:**
```python
@contextmanager
def get_db():
    session = create_session()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
```

**Usage locations:**
- `db/database.py:39-50` - Global session context manager
- `db/database.py:60-67` - Class-level session context manager

## Dataclass DTOs

Immutable data transfer objects use `@dataclass` for type-safe data passing between layers.

**Usage locations:**
- `agent/classifier.py:16-22` - `ClassificationResult`
- `agent/scheduler.py:20-40` - `MeetingExtraction`, `SchedulingProposal`
- `agent/approval.py:15-22` - `ApprovalCheck`
- `services/gmail_service.py:47-64` - `EmailMessage`
- `services/llm_service.py:15-35` - `ClassificationResult`, `MeetingExtraction`

## Fallback Chain

LLM operations have heuristic fallbacks when API calls fail, ensuring graceful degradation.

**Pattern:**
```python
def process(self, input):
    try:
        result = self.chain.invoke(input)
        return self._parse_result(result)
    except Exception:
        logger.exception("Chain failed")
        return self._fallback_method(input)
```

**Usage locations:**
- `agent/classifier.py:100-111` - Classification with keyword fallback (`_fallback_classification`)
- `agent/drafter.py:107-120` - Draft generation with template fallback (`_fallback_draft`)
- `agent/scheduler.py:131-142` - Meeting extraction with keyword fallback (`_fallback_extraction`)
- `services/llm_service.py:91-105` - Classification with default category fallback

## LangChain Pipelines

Composable pipelines using prompt templates, LLMs, and output parsers.

**Pattern:**
```python
prompt = ChatPromptTemplate.from_template(TEMPLATE)
parser = JsonOutputParser()
chain = prompt | llm | parser
result = chain.invoke({"key": "value"})
```

**Usage locations:**
- `agent/classifier.py:79-86` - Classification chain (prompt | llm | parser)
- `agent/drafter.py:71-77` - Drafting chain (prompt | llm)
- `agent/scheduler.py:110-117` - Extraction chain (prompt | llm | parser)

## Config Module

Centralized typed configuration with environment variable loading and constants.

**Location:** `config.py`

**Contents:**
- Path constants (`BASE_DIR`, `DATA_DIR`, `TOKEN_PATH`)
- API credentials from environment (`HUGGINGFACE_API_KEY`, `GOOGLE_CLIENT_ID`)
- Application settings (`CONFIDENCE_THRESHOLD`, `SENSITIVE_KEYWORDS`)
- Enum-like classes (`EmailCategory`, `ApprovalFlag`)

**Usage pattern:**
```python
import config
threshold = config.CONFIDENCE_THRESHOLD
model = config.LLM_MODEL_ID
```

## Model Swappability

Agents support runtime model changes by resetting cached instances.

**Pattern:**
```python
def set_model(self, model_id: str) -> None:
    self.model_id = model_id
    self._llm = None      # Reset cached LLM
    self._chain = None    # Reset cached chain
```

**Usage locations:**
- `agent/classifier.py:174-178`
- `agent/drafter.py:232-236`
- `agent/scheduler.py:377-381`
- `services/llm_service.py:318-321`

## Exception Logging

Consistent error handling using `logger.exception()` for full stack traces.

**Pattern:**
```python
try:
    result = risky_operation()
except SomeError:
    logger.exception("Operation failed")  # Logs message + stack trace
    return fallback_value
```

**Convention:**
- Use `logger.exception()` not `logger.error()` when catching exceptions
- Don't include the exception in the message (it's added automatically)
- Catch specific exceptions where possible

**Examples throughout:**
- `agent/classifier.py:109-111`
- `services/gmail_service.py:102-104, 129-131, 151-153`
- `db/database.py:46-48`

## Service Wrapper Pattern

External APIs are wrapped in service classes that handle authentication and error handling.

**Usage locations:**
- `services/gmail_service.py:66-354` - `GmailService` wraps Gmail API
- `services/calendar_service.py` - `CalendarService` wraps Calendar API
- `services/llm_service.py:37-321` - `LLMService` wraps HuggingFace Inference API

**Characteristics:**
- Lazy initialization of API clients
- Methods return domain objects (not raw API responses)
- Consistent exception logging
- Type hints for all public methods
