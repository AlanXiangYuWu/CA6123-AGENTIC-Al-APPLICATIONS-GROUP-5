# Essential Software Design Patterns

**Category**: quality
**Source**: Gang of Four, Refactoring.Guru, Wikipedia
**Use Case**: Coder Agent uses this when generating code structure and reviewing designs.

---

## 1. Overview

**Design patterns** are reusable solutions to common software design problems. They are not finished code that can be pasted into a project; they are templates—named structural and behavioral arrangements of classes and objects that recur across many problems and many languages. The value of a pattern is twofold. First, when a developer recognizes that a problem matches a known pattern, they inherit the accumulated experience of everyone who has solved similar problems before, including the patterns' known limitations. Second, patterns provide a **shared vocabulary**: saying "we should use a Strategy here" communicates a complete design idea in three words to anyone familiar with the pattern, where describing the same idea from scratch would take paragraphs.

Patterns are tools, not goals. The mistake of treating them as goals—forcing every class into a pattern, building elaborate hierarchies for problems that simple code would handle—is one of the more enduring forms of over-engineering in software. The best pattern for many problems is no pattern at all: a small function, a plain data class, or a flat sequence of statements. Patterns earn their cost when the problem they solve is genuinely present.

This document covers the seminal Gang of Four catalog and its three categories of patterns, the eight patterns from that catalog most worth knowing in modern practice, the more recent patterns that have entered widespread use since the GoF book was published, the design anti-patterns that recur often enough to deserve naming, and a worked example of where these patterns naturally apply in an educational coding app.

---

## 2. The Gang of Four

The book **"Design Patterns: Elements of Reusable Object-Oriented Software"** was published in 1994 by **Erich Gamma**, **Richard Helm**, **Ralph Johnson**, and **John Vlissides**—four authors who became known collectively as the **Gang of Four (GoF)**. The book catalogued 23 patterns drawn from the authors' analysis of recurring solutions in object-oriented systems, organized them into three categories, and gave each a name, structure, and discussion of trade-offs. It became one of the most influential software-engineering books ever written.

The GoF book has aged in interesting ways. Some patterns described as essential in 1994 are now built into modern languages or frameworks and are rarely written by hand. Others have become so standard that they no longer feel like patterns—they feel like natural ways of structuring code. A few have aged poorly enough that the consensus has shifted from "use this when appropriate" to "be careful using this." But the underlying contribution—the idea that recurring design problems have named solutions, and that having a vocabulary of solutions improves design discussions—has held up completely.

This document focuses on the eight GoF patterns most worth knowing in 2026. The full catalog of 23 is worth consulting as a reference; in daily practice, a smaller set covers most of the situations where pattern thinking helps.

---

## 3. The Three Categories

GoF organized patterns into three categories based on what they address.

- **Creational patterns** govern how objects are created. They solve problems like "how do I construct a complex object without exposing all its assembly logic?" or "how do I create one of several possible types depending on runtime context?"
- **Structural patterns** govern how objects compose into larger structures. They solve problems like "how do I make two interfaces that don't match work together?" or "how do I add behavior to an object without modifying its class?"
- **Behavioral patterns** govern how objects communicate with each other. They solve problems like "how do I let an object notify many others when something happens?" or "how do I make an algorithm pluggable so different ones can be swapped in?"

The three categories are not airtight—some patterns blur the lines—but they are useful for thinking about which kind of problem a pattern addresses. A team facing a "how do I create the right thing?" problem looks at creational patterns; a team facing a "how do I plug A into B?" problem looks at structural patterns; a team facing a "how do A and B coordinate?" problem looks at behavioral patterns.

---

## 4. Creational Patterns

**Singleton.** Ensure that a class has only one instance and provide a global access point to it. The classic example is a configuration object or a logger. The pattern is famous and frequently overused; many problems Singleton appears to solve are better solved by dependency injection (passing the dependency in rather than fetching it from a global). Singletons make testing harder (the global state persists across tests), make dependencies invisible (calling code does not signal what it depends on), and make refactoring risky (the global access point is everywhere).

```python
class ConfigSingleton:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.settings = load_settings()
        return cls._instance
```

Use sparingly. When tempted, ask whether passing the dependency in would work just as well; usually it would.

**Factory Method.** Provide an interface for creating objects, but let subclasses or configuration decide which class to instantiate. The pattern decouples client code from specific concrete classes.

```python
class NotificationFactory:
    @staticmethod
    def create(kind: str) -> Notification:
        if kind == "email":
            return EmailNotification()
        if kind == "sms":
            return SmsNotification()
        if kind == "push":
            return PushNotification()
        raise ValueError(f"Unknown notification kind: {kind}")
```

Factory Method is useful when the choice of concrete type depends on runtime context and the calling code should not need to know about every possible type.

**Builder.** Construct complex objects step by step, separating the construction process from the representation. Builders shine when an object has many optional parameters or when the construction process is itself complex enough to deserve its own type.

```python
query = (
    QueryBuilder()
    .table("learners")
    .where("age_band", "=", "6-8")
    .order_by("created_at", desc=True)
    .limit(10)
    .build()
)
```

Builders are common in libraries (HTTP-request builders, query builders, configuration builders) where the alternative—a constructor with 15 optional parameters—is unfriendly. The fluent chain-style API is a typical builder signature.

---

## 5. Structural Patterns

**Adapter.** Make two incompatible interfaces work together by wrapping one to look like the other. Adapters are the standard tool for integrating with third-party libraries that expose interfaces different from what your application expects.

```python
class LegacyPaymentGateway:
    def charge_card(self, amount_cents: int, card_token: str) -> dict: ...

class PaymentProcessorAdapter:
    """Adapt the legacy gateway to the application's PaymentProcessor interface."""

    def __init__(self, legacy: LegacyPaymentGateway):
        self._legacy = legacy

    def process(self, amount: Decimal, payment_method: PaymentMethod) -> Receipt:
        cents = int(amount * 100)
        result = self._legacy.charge_card(cents, payment_method.token)
        return Receipt.from_legacy(result)
```

The application code talks to a clean `PaymentProcessor` interface; the adapter handles the translation to the legacy gateway. Replacing the gateway later requires only a new adapter, not changes throughout the application.

**Decorator.** Add behavior to an object dynamically, by wrapping it in another object that adds the behavior. Python's `@decorator` syntax is directly inspired by the pattern, and the pattern is also the basis for middleware in many web frameworks.

```python
def with_caching(func):
    cache = {}
    def wrapper(*args):
        if args not in cache:
            cache[args] = func(*args)
        return cache[args]
    return wrapper

@with_caching
def expensive_lookup(key: str) -> Result:
    ...
```

Decorators compose: cache, log, and time a function by stacking three decorators. The pattern is widely used in Python for cross-cutting concerns and in web frameworks for middleware (authentication, logging, request validation).

**Facade.** Provide a simplified, unified interface to a complex subsystem. The facade hides the subsystem's complexity from clients that need only common operations.

```python
class LessonFacade:
    """Simple interface for the lesson-related subsystems."""

    def __init__(self, content_service, progress_service, recommender, ai_tutor):
        self._content = content_service
        self._progress = progress_service
        self._recommender = recommender
        self._ai_tutor = ai_tutor

    def start_lesson(self, learner_id: str) -> LessonStart:
        next_lesson = self._recommender.recommend(learner_id)
        content = self._content.load(next_lesson.id)
        self._progress.mark_started(learner_id, next_lesson.id)
        return LessonStart(content=content, hint_provider=self._ai_tutor)
```

The application's controllers call `lesson_facade.start_lesson()` instead of orchestrating four services directly. The facade makes the common path simple while leaving the underlying services available for less common cases.

---

## 6. Behavioral Patterns

**Strategy.** Encapsulate a family of algorithms so they can be selected at runtime and used interchangeably. Strategy is one of the most consistently useful patterns; it cleanly separates "what to do" from "how to do it."

```python
class HintStrategy(Protocol):
    def generate(self, code: str, lesson: Lesson) -> Hint: ...

class GentleHintStrategy:
    def generate(self, code: str, lesson: Lesson) -> Hint:
        # Returns vague nudges suitable for younger learners
        ...

class DetailedHintStrategy:
    def generate(self, code: str, lesson: Lesson) -> Hint:
        # Returns specific guidance with code examples
        ...

class HintEngine:
    def __init__(self, strategy: HintStrategy):
        self._strategy = strategy

    def hint_for(self, code: str, lesson: Lesson) -> Hint:
        return self._strategy.generate(code, lesson)
```

The `HintEngine` does not care which strategy it uses; the calling context selects one based on the learner's age band. Adding a new strategy is a matter of writing a new class, not modifying existing code.

**Observer.** Define a one-to-many dependency between objects so that when one changes state, all dependents are notified automatically. The pattern is the basis for event emitters, reactive frameworks (RxJS), and many UI frameworks.

```python
class LessonProgressEvents:
    def __init__(self):
        self._listeners: list[Callable] = []

    def subscribe(self, listener: Callable):
        self._listeners.append(listener)

    def emit_completed(self, learner_id: str, lesson_id: str):
        for listener in self._listeners:
            listener(learner_id, lesson_id)

events = LessonProgressEvents()
events.subscribe(update_streak)
events.subscribe(send_progress_email)
events.subscribe(record_analytics)
events.emit_completed(learner_id="abc", lesson_id="lesson-42")
```

Observer is conceptually the same idea as event-driven architecture from the architecture documents, applied at the object level. It allows the producer of an event to remain ignorant of the consumers, which keeps coupling low.

---

## 7. Modern Patterns Beyond GoF

Several patterns that postdate the GoF book have entered widespread use, particularly for application-level architecture rather than object-level structure.

**Repository.** Abstract data access behind a domain-friendly interface. The application talks to a `LearnerRepository` that exposes operations like `find_by_id`, `find_by_parent`, and `save`; the repository's implementation handles the database access. The pattern decouples business logic from storage technology and makes testing easier (a `FakeLearnerRepository` for tests does not need a database).

```python
class LearnerRepository(Protocol):
    def find_by_id(self, learner_id: str) -> Learner | None: ...
    def find_by_parent(self, parent_id: str) -> list[Learner]: ...
    def save(self, learner: Learner) -> None: ...
```

Repositories are common in domain-driven design and in any codebase where the team wants to keep storage decisions separable from business logic.

**Dependency Injection (DI).** Rather than having an object create or fetch its dependencies, dependencies are provided from outside. The pattern is foundational to testable, modular code: an object that takes its dependencies as constructor arguments can be tested by passing in fakes, and its requirements are explicit. Most modern frameworks (Spring in Java, FastAPI in Python, NestJS in Node.js) have built-in DI.

```python
class LessonService:
    def __init__(
        self,
        repository: LessonRepository,
        ai_tutor: AiTutor,
        events: LessonProgressEvents,
    ):
        self._repo = repository
        self._tutor = ai_tutor
        self._events = events
```

The service does not create its own dependencies; they are passed in. The same service can use real implementations in production and fakes in tests.

**CQRS (Command Query Responsibility Segregation).** Separate the model used for writes (commands) from the model used for reads (queries). The two models can use different storage, scale independently, and evolve their data shapes independently. CQRS is heavyweight for most applications but valuable for high-scale systems with very different read and write patterns.

**Saga.** Manage long-running transactions across multiple services in a distributed system. Where a single-database transaction guarantees atomicity, a saga coordinates a sequence of local transactions, each with a defined compensating action that runs if a later step fails. Sagas are essential for microservices architectures where cross-service ACID transactions are not available.

---

## 8. Example: Patterns in Educational Coding App for Kids

Consider where these patterns naturally apply in **CodeCub**, the educational coding app for children aged 6–12. Patterns are not adopted because they are patterns; they are adopted where the underlying problem they solve is present.

**Strategy — for age-band-specific behavior.**
Hint generation, lesson recommendation, and content presentation all vary by age band. Rather than scattering `if age_band == "6-8"` checks throughout the code, the team defines strategy interfaces (`HintStrategy`, `RecommendationStrategy`, `PresentationStrategy`) with one implementation per age band. The age-band-specific logic lives in one place per concern, and adding a new age band is a contained change.

**Observer — for progress events.**
When a learner completes a lesson, several things should happen: streak update, parent notification (if conditions are met), analytics event, achievement check, possibly an in-app celebration animation. Wiring all of these into the lesson-completion endpoint directly produces tightly coupled code. An Observer-style event emitter (or, when scale demands it, a real event bus as discussed in the EDA document) lets each concern subscribe independently.

**Repository — for data access boundaries.**
The application's business logic (lesson recommendation, progress tracking, hint generation) should not know whether the underlying database is PostgreSQL, Supabase, or something else. A `LearnerRepository`, `LessonRepository`, `ProgressRepository`, and `AchievementRepository` provide domain-friendly interfaces, and a single layer of repository implementations handles the actual database access. The repositories also make unit testing the business logic feasible without spinning up a database.

**Factory Method — for lesson construction.**
Lessons come in several types (introductory, challenge, project, review) with different content shapes and behaviors. A `LessonFactory.create(lesson_data)` that returns the correct subtype keeps the calling code agnostic about which type it received and concentrates type-selection logic in one place.

**Facade — for the lesson-orchestration subsystem.**
The lesson lifecycle involves several services (content, progress, recommendation, AI tutoring). A `LessonFacade` exposes the common operations (`start_lesson`, `submit_attempt`, `request_hint`) and hides the orchestration details from API controllers. The facade makes the most common paths simple while leaving the underlying services available for less common cases.

**Decorator — for cross-cutting concerns.**
Caching, rate limiting, logging, and authentication are all cross-cutting concerns that should not pollute business logic. Decorators (Python's `@` syntax, FastAPI's dependency-injection style, or middleware in the framework layer) layer these concerns onto endpoints and functions cleanly.

**Dependency Injection — throughout.**
Every service takes its dependencies as constructor arguments rather than creating or fetching them. FastAPI's dependency-injection system makes this idiomatic in the Python backend. The pattern is non-negotiable: it is the foundation of testability and modularity.

**Builder — for AI prompt construction.**
The AI tutoring layer constructs prompts from many parts: a system prompt, the learner's age band, the lesson context, the code submitted, the conversation history. A `PromptBuilder` with a fluent API is cleaner than a constructor with eight parameters and easier to evolve as prompt templates change.

**Patterns deliberately avoided:**

- **Singleton.** Configuration, the database connection pool, and similar are managed by the framework's lifespan or DI system, not as global Singletons. Tests pass in test configurations rather than mutating shared singletons.
- **CQRS.** The application's read and write patterns are similar enough that splitting models would add complexity without payoff. CQRS may be reconsidered later if specific read patterns demand it.
- **Saga.** The application is a modular monolith; cross-service transactions do not exist yet. If service extraction happens (e.g., the code-execution sandbox or AI tutoring), saga-style compensation may become relevant for specific flows.

---

## 9. Anti-Patterns to Avoid

- **Singleton overuse.** Singletons turn dependencies into hidden globals, making testing difficult and refactoring risky. Default to dependency injection; reach for Singleton only when a genuine "exactly one instance" requirement exists.
- **God Object.** A class that does everything—`UserManager` that handles authentication, profile editing, billing, notifications, and analytics—is impossible to test, hard to change, and a magnet for further accumulation. Split by responsibility.
- **Anemic Domain Model.** Data classes with no behavior, paired with service classes that contain all the logic, produce code where the data is dumb and the services know everything. Domain entities should encapsulate the rules that govern them; services should orchestrate, not implement, business logic.
- **Pattern theater.** Forcing patterns where simple code would work. Three classes and a factory for what could be a 10-line function is over-engineering. Patterns are tools; if no pattern applies, no pattern is the right answer.
- **Inheritance abuse.** Deep inheritance hierarchies that exist for code reuse rather than genuine "is-a" relationships produce fragile, hard-to-change code. Composition (delegating to a collaborator) is usually preferable; inheritance should be reserved for real subtyping relationships.
- **Premature abstraction.** Writing interfaces, abstract base classes, and DI hooks before there is a second implementation that justifies them produces complexity without payoff. Wait for the second case to demand the abstraction; build it then with full information about what the abstraction needs to express.
- **Confusing patterns with solutions.** A pattern is a structural template; the actual solution is the code that fills it in. Naming a class `*Strategy` does not mean the design is good; the strategies inside have to do something useful.
- **Spreading transactional logic across services.** When a single business operation requires changes in multiple services without proper saga coordination, partial-failure modes become silent data corruption. Either keep the operation within a single transaction boundary or design the saga explicitly.
- **Treating GoF as a checklist.** Patterns are vocabulary, not requirements. A codebase is not better because it uses 15 patterns; it is better when its design is appropriate to its problem, whether that involves named patterns or not.

---

## 10. References

- Refactoring.Guru — Design Patterns: https://refactoring.guru/design-patterns
- Wikipedia — Design Patterns (book): https://en.wikipedia.org/wiki/Design_Patterns