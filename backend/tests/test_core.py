import pytest
from backend.orchestrator import orchestrator, OrchestrationRequest
from backend.providers.registry import provider_registry
from backend.planner.intent_analyzer import intent_analyzer
from backend.planner.task_planner import task_planner

@pytest.mark.asyncio
async def test_registry_initialization():
    await provider_registry.initialize()
    assert provider_registry.is_initialized()
    assert provider_registry.count() > 0

@pytest.mark.asyncio
async def test_intent_analyzer():
    intent = await intent_analyzer.analyze("Build a python script")
    assert intent.type == "code"

@pytest.mark.asyncio
async def test_task_planner():
    plan = await task_planner.create_plan("Build a react app", "code")
    assert plan.is_complex == True
    assert len(plan.subtasks) > 1

@pytest.mark.asyncio
async def test_orchestrator_instantiation():
    assert orchestrator is not None
    assert orchestrator.result_fuser is not None
