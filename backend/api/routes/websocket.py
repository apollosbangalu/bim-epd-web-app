"""
WebSocket API Routes
Real-time streaming endpoints for workflow progress updates
"""
import logging
import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from agents.orchestrator import AgentOrchestrator
from core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()


@router.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    """
    WebSocket endpoint for real-time chat with streaming responses
    
    Sends progress updates as workflow executes
    """
    await websocket.accept()
    logger.info("WebSocket connection established")
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_json()
            
            message = data.get("message")
            query_type = data.get("query_type", "cross_match")
            llm_provider = data.get("llm_provider", settings.default_llm_provider)
            
            logger.info(f"WebSocket received: {message[:50]}...")
            
            # Send acknowledgment
            await websocket.send_json({
                "type": "ack",
                "message": "Processing your request..."
            })
            
            # Create orchestrator
            orchestrator = AgentOrchestrator(llm_provider=llm_provider)
            
            # Extract material name
            material_name = _extract_material_name(message)
            
            # Execute workflow
            result = await orchestrator.execute_workflow(
                material_name=material_name,
                top_n=10
            )
            
            # Send workflow steps as they complete
            for step in result.get("workflow_steps", []):
                await websocket.send_json({
                    "type": "step",
                    "data": step
                })
            
            # Send final result
            await websocket.send_json({
                "type": "complete",
                "data": result
            })
    
    except WebSocketDisconnect:
        logger.info("WebSocket disconnected")
    
    except Exception as e:
        logger.error(f"WebSocket error: {e}", exc_info=True)
        await websocket.send_json({
            "type": "error",
            "message": str(e)
        })


def _extract_material_name(message: str) -> str:
    """Extract material name from message (same as chat route)"""
    message = message.lower()
    remove_phrases = [
        "find epd for", "find epd products for",
        "match", "search for", "get", "show me"
    ]
    
    for phrase in remove_phrases:
        message = message.replace(phrase, "")
    
    return message.strip()