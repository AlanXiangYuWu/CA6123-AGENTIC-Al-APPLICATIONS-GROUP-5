"""Multiple fake states for QA agent robustness testing.

We test 4 scenarios:
- FAKE_STATE_KIDS_APP : original — has bugs, QA should fail it (low score)
- FAKE_STATE_FITNESS  : different domain — QA should still work coherently
- FAKE_STATE_PERFECT  : intentionally good — QA should give HIGH score
- FAKE_STATE_BROKEN   : everything wrong — QA should give VERY LOW score

This addresses the over-fitting concern: if QA only passed our original fixture,
it might be tuned to that specific data. Running it across 4 distinct states
verifies the agent's behavior generalizes.
"""

# ============================================================
# Fixture 1: original kids coding app — has KNOWN bugs
# ============================================================
FAKE_STATE_KIDS_APP = {
    "project_brief": {
        "product_name": "AI Coding Companion App",
        "one_sentence_summary": (
            "An AI coding companion app for kids aged 6-12 that teaches "
            "Python through gamified missions."
        ),
        "target_users": ["Kids aged 6-12"],
        "user_scenario": "Kids learn Python through fun coding missions.",
        "key_features": [
            "Gamified Python lessons",
            "AI tutor chat",
            "Progress tracking",
            "Parent dashboard",
        ],
    },
    "prd": {
        "product_name": "AI Coding Companion App",
        "features": [
            {"id": "F1", "name": "Gamified missions",
             "description": "Kids complete coding puzzles.",
             "acceptance_criteria": ["User can start a mission",
                                     "Progress saved to backend"]},
            {"id": "F2", "name": "AI chat tutor",
             "description": "AI explains in age-appropriate language.",
             "acceptance_criteria": ["Responds within 5s"]},
            {"id": "F3", "name": "Progress tracking",
             "description": "Users see completion % and badges.",
             "acceptance_criteria": ["Shows completion %"]},
            # 'Parent dashboard' missing on purpose
        ],
        "non_functional": ["COPPA compliant", "Web-based"],
    },
    "tech_design": {
        "architecture": "FastAPI + React + PostgreSQL",
        "components": [
            {"name": "MissionService", "responsibility": "Manages missions"},
            {"name": "ChatGateway", "responsibility": "Routes chat to LLM"},
            # No component for F3 'Progress tracking' on purpose
        ],
        "data_models": ["User", "Mission", "Progress"],
        "external_services": ["Gemini API", "PostgreSQL"],
    },
    "code_artifact": {
        "files": [
            {"path": "backend/main.py",
             "content": "from fastapi import FastAPI\napp = FastAPI()\n"},
            {"path": "backend/missions.py",
             "content": "def start_mission(uid, mid):\n    return {'started': True}\n\n"
                        "def bad_syntax(\n"},  # syntax error on purpose
        ],
    },
    "research": {"market_size": "Kids edtech is large.",
                 "competitors": ["Code.org", "Tynker"]},
    "messages": [],
    "trace": ["customer", "research", "product", "architect", "coder"],
}


# ============================================================
# Fixture 2: fitness tracker — completely different domain
# ============================================================
FAKE_STATE_FITNESS = {
    "project_brief": {
        "product_name": "FitTrack Pro",
        "one_sentence_summary": (
            "A mobile fitness tracker for adults that monitors workouts "
            "and provides AI-powered coaching."
        ),
        "target_users": ["Fitness enthusiasts aged 25-45"],
        "user_scenario": "Users log workouts and get personalized advice.",
        "key_features": [
            "Workout logging",
            "AI coaching",
            "Progress charts",
            "Social leaderboard",
        ],
    },
    "prd": {
        "product_name": "FitTrack Pro",
        "features": [
            {"id": "F1", "name": "Workout logging",
             "description": "Users log exercises with sets/reps.",
             "acceptance_criteria": ["Can save workout", "Edit past workouts"]},
            {"id": "F2", "name": "AI coaching",
             "description": "AI suggests next workout based on history.",
             "acceptance_criteria": ["Suggestion within 3s"]},
            {"id": "F3", "name": "Progress charts",
             "description": "Visualize strength gains over time.",
             "acceptance_criteria": ["Chart loads in 2s"]},
            {"id": "F4", "name": "Social leaderboard",
             "description": "Friends see each other's weekly totals.",
             "acceptance_criteria": ["Leaderboard updates daily"]},
        ],
        "non_functional": ["GDPR compliant", "iOS + Android"],
    },
    "tech_design": {
        "architecture": "React Native + Node.js + MongoDB",
        "components": [
            {"name": "WorkoutLogger", "responsibility": "CRUD for workout entries"},
            {"name": "CoachingEngine", "responsibility": "AI suggestion logic"},
            {"name": "ChartRenderer", "responsibility": "Visualizes progress data"},
            {"name": "LeaderboardService", "responsibility": "Aggregates friend totals"},
        ],
        "data_models": ["User", "Workout", "Friendship"],
        "external_services": ["OpenAI API", "MongoDB Atlas"],
    },
    "code_artifact": {
        "files": [
            {"path": "src/workout.js",
             "content": "function logWorkout(uid, exercises) {\n"
                        "  return db.workouts.insert({uid, exercises});\n"
                        "}\n"},
        ],
    },
    "research": {"market_size": "Fitness app market is $14B."},
    "messages": [],
    "trace": ["customer", "research", "product", "architect", "coder"],
}


# ============================================================
# Fixture 3: PERFECT case — well-designed, no bugs. QA should give HIGH score.
# ============================================================
FAKE_STATE_PERFECT = {
    "project_brief": {
        "product_name": "TaskFlow",
        "one_sentence_summary": "A simple to-do list web app for individuals.",
        "target_users": ["Adults wanting personal task management"],
        "user_scenario": "Users add, complete, and organize daily tasks.",
        "key_features": ["Add task", "Mark complete", "Filter by date"],
    },
    "prd": {
        "product_name": "TaskFlow",
        "features": [
            {"id": "F1", "name": "Add task",
             "description": "User creates a new task with title and due date.",
             "acceptance_criteria": ["Task appears in list immediately"]},
            {"id": "F2", "name": "Mark complete",
             "description": "User toggles task between open and complete.",
             "acceptance_criteria": ["Status persists across reload"]},
            {"id": "F3", "name": "Filter by date",
             "description": "User views tasks for today / week / overdue.",
             "acceptance_criteria": ["Filter applies in <1s"]},
        ],
        "non_functional": ["Web-based"],
    },
    "tech_design": {
        "architecture": "FastAPI + SQLite + plain HTML",
        "components": [
            {"name": "TaskService", "responsibility": "CRUD for tasks (covers F1, F2)"},
            {"name": "FilterService", "responsibility": "Date filtering for F3"},
        ],
        "data_models": ["Task"],
        "external_services": [],
    },
    "code_artifact": {
        "files": [
            {"path": "main.py",
             "content": (
                 "from fastapi import FastAPI\n"
                 "app = FastAPI()\n\n"
                 "tasks = []\n\n"
                 "@app.post('/tasks')\n"
                 "def add_task(title: str, due: str):\n"
                 "    t = {'id': len(tasks), 'title': title, 'due': due, 'done': False}\n"
                 "    tasks.append(t)\n"
                 "    return t\n\n"
                 "@app.put('/tasks/{tid}/toggle')\n"
                 "def toggle(tid: int):\n"
                 "    tasks[tid]['done'] = not tasks[tid]['done']\n"
                 "    return tasks[tid]\n"
             )},
        ],
    },
    "research": {"market_size": "To-do apps are well-established."},
    "messages": [],
    "trace": ["customer", "research", "product", "architect", "coder"],
}


# ============================================================
# Fixture 4: BROKEN case — everything is wrong. QA should give very LOW score.
# ============================================================
FAKE_STATE_BROKEN = {
    "project_brief": {
        "product_name": "MyApp",
        "one_sentence_summary": "A social network for cat owners.",
        "target_users": ["Cat owners worldwide"],
        "user_scenario": "Cat owners share photos and tips.",
        "key_features": ["Photo sharing", "Cat profiles", "Messaging",
                         "Marketplace", "Vet directory"],
    },
    "prd": {
        # PRD covers almost nothing from brief
        "product_name": "MyApp",
        "features": [
            {"id": "F1", "name": "Login",
             "description": "User can log in.",
             "acceptance_criteria": []},
        ],
        "non_functional": ["Must scale to 1 billion users",  # extreme commitment
                           "HIPAA compliant",  # wrong regulation for this domain
                           "Quantum-encrypted"],  # nonsense factual claim
    },
    "tech_design": {
        # Empty design
        "architecture": "TBD",
        "components": [],
        "data_models": [],
    },
    "code_artifact": {
        "files": [
            {"path": "broken.py",
             # Multiple syntax errors
             "content": "def func(\n    print 'hello'\n    if x =\n"},
        ],
    },
    "research": {},
    "messages": [],
    "trace": ["customer", "research", "product", "architect", "coder"],
}


# Backwards compat: keep the old name pointing at the original fixture
FAKE_STATE = FAKE_STATE_KIDS_APP


# ============================================================
# Registry for the test runner
# ============================================================
ALL_FIXTURES = {
    "kids_app": FAKE_STATE_KIDS_APP,
    "fitness":  FAKE_STATE_FITNESS,
    "perfect":  FAKE_STATE_PERFECT,
    "broken":   FAKE_STATE_BROKEN,
}