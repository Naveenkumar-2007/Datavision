from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, List
from pydantic import BaseModel
import uuid
import logging
from api.deps import get_current_user_id

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/pipelines", tags=["Pipelines"])

class PipelineNode(BaseModel):
    id: str
    type: str
    data: Dict[str, Any]

class PipelineEdge(BaseModel):
    id: str
    source: str
    target: str

class PipelineExecutionRequest(BaseModel):
    nodes: List[PipelineNode]
    edges: List[PipelineEdge]

@router.post("/execute")
async def execute_pipeline(
    req: PipelineExecutionRequest,
    user_id: str = Depends(get_current_user_id)
):
    """
    Executes a visual pipeline represented as a DAG.
    This is a mocked execution engine for demonstration purposes,
    but it validates the flow logic.
    """
    try:
        if not req.nodes:
            raise HTTPException(status_code=400, detail="Pipeline contains no nodes")
            
        # Build execution graph
        graph = {node.id: {"type": node.type, "data": node.data, "next": []} for node in req.nodes}
        for edge in req.edges:
            if edge.source in graph and edge.target in graph:
                graph[edge.source]["next"].append(edge.target)
                
        # Find start node (DataSource)
        start_nodes = [n_id for n_id, n_data in graph.items() if n_data["type"] == 'dataSource']
        
        if not start_nodes:
            raise HTTPException(status_code=400, detail="Pipeline must start with a Data Source node")
            
        # Linear execution for demonstration
        execution_log = []
        current = start_nodes[0]
        
        while current:
            node = graph[current]
            action_desc = f"Executing {node['type']}"
            if node['type'] == 'dataSource':
                file_name = node['data'].get('file', 'unknown_file')
                action_desc = f"Loading dataset: {file_name}"
            elif node['type'] == 'cleanData':
                action_desc = "Cleaning dataset (imputing missing values)"
            elif node['type'] == 'transform':
                action_desc = "Transforming features (scaling, encoding)"
            elif node['type'] == 'trainModel':
                action_desc = "Training AutoML Model"
                
            execution_log.append(f"[SUCCESS] {action_desc}")
            
            if node['next']:
                current = node['next'][0] # Take first branch for simplicity
            else:
                current = None
                
        return {
            "success": True,
            "message": "Pipeline executed successfully",
            "log": execution_log,
            "pipeline_id": f"pl_{uuid.uuid4().hex[:8]}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Pipeline execution failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

from database.db import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from database.orm import VisualPipeline

@router.post('/save')
async def save_pipeline(
    req: PipelineExecutionRequest,
    name: str = 'Untitled Pipeline',
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    try:
        new_pipeline = VisualPipeline(
            user_id=user_id,
            name=name,
            nodes=[n.dict() for n in req.nodes],
            edges=[e.dict() for e in req.edges],
            is_active=True
        )
        db.add(new_pipeline)
        await db.commit()
        return {'success': True, 'message': 'Pipeline saved', 'pipeline_id': str(new_pipeline.id)}
    except Exception as e:
        await db.rollback()
        return {'success': False, 'error': str(e)}

@router.get('/saved')
async def get_saved_pipelines(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    try:
        stmt = select(VisualPipeline).where(VisualPipeline.user_id == user_id)
        result = await db.execute(stmt)
        pipelines = result.scalars().all()
        return {
            'success': True,
            'pipelines': [{'id': str(p.id), 'name': p.name, 'created_at': p.created_at.isoformat()} for p in pipelines]
        }
    except Exception as e:
        return {'success': False, 'error': str(e)}
