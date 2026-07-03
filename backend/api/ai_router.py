"""
AI Router for MetaPilot AI

Provides endpoints for AI inference and orchestration.
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import StreamingResponse
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field

from ..orchestrator import AIOrchestrator, AIRequest, AIResponse, TaskType, TaskStatus
from ..security.auth import AuthManager, get_current_user
from ..security.permission_manager import PermissionManager, check_permission

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ai", tags=["AI"])


# Models
class GenerateRequest(BaseModel):
    """Request for text generation."""
    prompt: str = Field(..., description="The user prompt")
    system_prompt: Optional[str] = Field(None, description="Optional system prompt")
    task_type: TaskType = Field(TaskType.TEXT_GENERATION, description="Type of AI task")
    provider: Optional[str] = Field(None, description="Specific provider to use")
    model: Optional[str] = Field(None, description="Specific model to use")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Model parameters")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class ChatRequest(BaseModel):
    """Request for chat completion."""
    messages: List[Dict[str, str]] = Field(..., description="List of chat messages")
    system_prompt: Optional[str] = Field(None, description="Optional system prompt")
    provider: Optional[str] = Field(None, description="Specific provider to use")
    model: Optional[str] = Field(None, description="Specific model to use")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Model parameters")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class MultiProviderRequest(BaseModel):
    """Request for multi-provider generation."""
    prompt: str = Field(..., description="The user prompt")
    system_prompt: Optional[str] = Field(None, description="Optional system prompt")
    providers: List[str] = Field(..., description="List of providers to use")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Model parameters")


class BatchRequest(BaseModel):
    """Request for batch processing."""
    requests: List[GenerateRequest] = Field(..., description="List of generation requests")


class ConversationRequest(BaseModel):
    """Request for conversation operations."""
    name: Optional[str] = Field(None, description="Conversation name")
    message: Optional[str] = Field(None, description="Message to add")
    role: Optional[str] = Field(None, description="Role of the message")


# Endpoints
@router.post("/generate", summary="Generate text", response_model=Dict[str, Any])
async def generate(
    request: GenerateRequest,
    current_user: Optional[Dict[str, Any]] = Depends(get_current_user),
    orchestrator: AIOrchestrator = Depends(lambda: AIOrchestrator()),
) -> AIResponse:
    """
    Generate text from a prompt.
    
    This endpoint supports:
    - Text generation
    - Chat completion
    - Knowledge queries
    - Document processing
    - And more based on task_type
    """
    # Check permission
    if current_user:
        check_permission("ai:use", current_user)
    
    # Create AI request
    ai_request = AIRequest(
        task_type=request.task_type,
        prompt=request.prompt,
        system_prompt=request.system_prompt,
        provider=request.provider,
        model=request.model,
        parameters=request.parameters,
        metadata={
            "user_id": current_user.get("id") if current_user else None,
            **request.metadata,
        },
    )
    
    # Process request
    response = await orchestrator.process_request(ai_request)
    
    return response


@router.post("/chat", summary="Chat completion", response_model=Dict[str, Any])
async def chat(
    request: ChatRequest,
    current_user: Optional[Dict[str, Any]] = Depends(get_current_user),
    orchestrator: AIOrchestrator = Depends(lambda: AIOrchestrator()),
) -> AIResponse:
    """
    Generate a chat response.
    
    Send a list of messages and get an AI response.
    """
    # Check permission
    if current_user:
        check_permission("ai:use", current_user)
    
    # Create AI request with chat task type
    ai_request = AIRequest(
        task_type=TaskType.CHAT,
        prompt=request.messages[-1]["content"] if request.messages else "",
        system_prompt=request.system_prompt,
        provider=request.provider,
        model=request.model,
        parameters=request.parameters,
        metadata={
            "user_id": current_user.get("id") if current_user else None,
            "messages": request.messages,
            **request.metadata,
        },
    )
    
    # Process request
    response = await orchestrator.process_request(ai_request)
    
    return response


@router.post("/multi-provider", summary="Multi-provider generation", response_model=Dict[str, Any])
async def multi_provider(
    request: MultiProviderRequest,
    current_user: Optional[Dict[str, Any]] = Depends(get_current_user),
    orchestrator: AIOrchestrator = Depends(lambda: AIOrchestrator()),
) -> Dict[str, Any]:
    """
    Generate text using multiple providers and merge results.
    
    This is useful for:
    - Getting multiple perspectives
    - Comparing provider outputs
    - Ensuring robustness
    """
    # Check permission
    if current_user:
        check_permission("ai:use", current_user)
    
    # Create AI request
    ai_request = AIRequest(
        task_type=TaskType.MULTI_PROVIDER,
        prompt=request.prompt,
        system_prompt=request.system_prompt,
        parameters=request.parameters,
        metadata={
            "user_id": current_user.get("id") if current_user else None,
        },
    )
    
    # Process multi-provider request
    result = await orchestrator.process_multi_provider(ai_request, request.providers)
    
    return result


@router.post("/batch", summary="Batch processing", response_model=List[Dict[str, Any]])
async def batch(
    request: BatchRequest,
    current_user: Optional[Dict[str, Any]] = Depends(get_current_user),
    orchestrator: AIOrchestrator = Depends(lambda: AIOrchestrator()),
) -> List[AIResponse]:
    """
    Process multiple requests in batch.
    
    Useful for:
    - Processing multiple prompts at once
    - Parallel processing (when implemented)
    - Batch inference
    """
    # Check permission
    if current_user:
        check_permission("ai:use", current_user)
    
    # Convert requests
    ai_requests = []
    for req in request.requests:
        ai_requests.append(AIRequest(
            task_type=req.task_type,
            prompt=req.prompt,
            system_prompt=req.system_prompt,
            provider=req.provider,
            model=req.model,
            parameters=req.parameters,
            metadata={
                "user_id": current_user.get("id") if current_user else None,
                **req.metadata,
            },
        ))
    
    # Process batch
    responses = await orchestrator.process_batch(ai_requests)
    
    return responses


@router.post("/stream", summary="Streaming generation")
async def stream(
    request: GenerateRequest,
    current_user: Optional[Dict[str, Any]] = Depends(get_current_user),
    orchestrator: AIOrchestrator = Depends(lambda: AIOrchestrator()),
):
    """
    Stream generation token by token.
    
    Use this for:
    - Real-time generation
    - Large responses
    - Interactive applications
    """
    # Check permission
    if current_user:
        check_permission("ai:use", current_user)
    
    # Create AI request
    ai_request = AIRequest(
        task_type=request.task_type,
        prompt=request.prompt,
        system_prompt=request.system_prompt,
        provider=request.provider,
        model=request.model,
        parameters=request.parameters,
        metadata={
            "user_id": current_user.get("id") if current_user else None,
            **request.metadata,
        },
    )
    
    async def generate_stream():
        try:
            async for chunk in orchestrator.stream_generation(ai_request, lambda x: x):
                yield f"data: {json.dumps({'text': chunk})}\n\n"
        except Exception as e:
            logger.error(f"Streaming error: {e}")
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
    
    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
    )


# Conversation endpoints
@router.post("/conversations", summary="Create conversation", response_model=Dict[str, Any])
async def create_conversation(
    request: ConversationRequest,
    current_user: Optional[Dict[str, Any]] = Depends(get_current_user),
    orchestrator: AIOrchestrator = Depends(lambda: AIOrchestrator()),
) -> Dict[str, Any]:
    """Create a new conversation."""
    if current_user:
        check_permission("conversation:create", current_user)
    
    conversation = orchestrator.create_conversation(
        name=request.name or "New Conversation"
    )
    
    return {
        "id": conversation.id,
        "name": conversation.name,
        "created_at": conversation.created_at.isoformat(),
    }


@router.get("/conversations", summary="List conversations", response_model=List[Dict[str, Any]])
async def list_conversations(
    current_user: Optional[Dict[str, Any]] = Depends(get_current_user),
    orchestrator: AIOrchestrator = Depends(lambda: AIOrchestrator()),
) -> List[Dict[str, Any]]:
    """List all conversations."""
    if current_user:
        check_permission("conversation:list", current_user)
    
    return orchestrator.list_conversations()


@router.get("/conversations/{conversation_id}", summary="Get conversation", response_model=Dict[str, Any])
async def get_conversation(
    conversation_id: str,
    current_user: Optional[Dict[str, Any]] = Depends(get_current_user),
    orchestrator: AIOrchestrator = Depends(lambda: AIOrchestrator()),
) -> Dict[str, Any]:
    """Get a conversation by ID."""
    if current_user:
        check_permission("conversation:read", current_user)
    
    conversation = orchestrator.get_conversation(conversation_id)
    
    if not conversation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
    
    return {
        "id": conversation.id,
        "name": conversation.name,
        "messages": [
            {
                "role": msg.role,
                "content": msg.content,
                "timestamp": msg.timestamp.isoformat(),
                "metadata": msg.metadata,
            }
            for msg in conversation.messages
        ],
        "created_at": conversation.created_at.isoformat(),
        "updated_at": conversation.updated_at.isoformat(),
        "metadata": conversation.metadata,
    }


@router.delete("/conversations/{conversation_id}", summary="Delete conversation")
async def delete_conversation(
    conversation_id: str,
    current_user: Optional[Dict[str, Any]] = Depends(get_current_user),
    orchestrator: AIOrchestrator = Depends(lambda: AIOrchestrator()),
) -> Dict[str, Any]:
    """Delete a conversation."""
    if current_user:
        check_permission("conversation:delete", current_user)
    
    success = orchestrator.delete_conversation(conversation_id)
    
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
    
    return {"success": True, "message": "Conversation deleted"}


# Task status endpoints
@router.get("/tasks/{task_id}/status", summary="Get task status")
async def get_task_status(
    task_id: str,
    current_user: Optional[Dict[str, Any]] = Depends(get_current_user),
    orchestrator: AIOrchestrator = Depends(lambda: AIOrchestrator()),
) -> Dict[str, Any]:
    """Get the status of a task."""
    status = orchestrator.get_task_status(task_id)
    
    if status is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    
    return {"task_id": task_id, "status": status.value}


@router.post("/tasks/{task_id}/cancel", summary="Cancel task")
async def cancel_task(
    task_id: str,
    current_user: Optional[Dict[str, Any]] = Depends(get_current_user),
    orchestrator: AIOrchestrator = Depends(lambda: AIOrchestrator()),
) -> Dict[str, Any]:
    """Cancel a running task."""
    if current_user:
        check_permission("ai:use", current_user)
    
    success = orchestrator.cancel_task(task_id)
    
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    
    return {"success": True, "message": "Task cancelled"}
