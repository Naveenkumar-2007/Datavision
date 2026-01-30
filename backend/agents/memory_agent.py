"""
Memory Agent - Incremental knowledge graph updates
Maintains and enhances the workspace knowledge graph
"""

from agents.base.agent_runner import AgentRunner, Insight
from graph.query import load_graph
import logging
from typing import List

logger = logging.getLogger(__name__)


class MemoryAgent(AgentRunner):
    """Maintains and updates knowledge graph memory"""
    
    def __init__(self):
        super().__init__('MemoryAgent')
    
    async def detect_insights(self, workspace_id: str) -> List[Insight]:
        """
        Update knowledge graph and detect memory-related insights
        This agent focuses on maintaining data quality
        """
        insights = []
        
        try:
            # Load current graph
            graph = load_graph(workspace_id)
            
            if not graph or graph.number_of_nodes() == 0:
                self.logger.info(f"No graph data for workspace {workspace_id}")
                return []
            
            # Check graph health
            num_nodes = graph.number_of_nodes()
            num_edges = graph.number_of_edges()
            
            # Detect orphaned nodes
            orphaned_nodes = [node for node in graph.nodes() if graph.degree(node) == 0]
            
            if len(orphaned_nodes) > num_nodes * 0.1:  # More than 10% orphaned
                insight = Insight(
                    title="🧠 Knowledge Graph Alert",
                    body=f"Detected {len(orphaned_nodes)} isolated entities in your knowledge graph. This may indicate data quality issues or missing relationships.",
                    severity='medium',
                    score=60,
                    metadata={
                        'orphaned_count': len(orphaned_nodes),
                        'total_nodes': num_nodes,
                        'total_edges': num_edges
                    }
                )
                insights.append(insight)
            
            # Positive insight if graph is healthy
            if num_nodes > 100 and num_edges > 200:
                insight = Insight(
                    title="✅ Knowledge Graph Healthy",
                    body=f"Your business knowledge graph is well-connected with {num_nodes} entities and {num_edges} relationships. Good data quality detected!",
                    severity='low',
                    score=100,
                    metadata={
                        'nodes': num_nodes,
                        'edges': num_edges,
                        'density': num_edges / (num_nodes * (num_nodes - 1)) if num_nodes > 1 else 0
                    }
                )
                insights.append(insight)
            
            self.logger.info(f"MemoryAgent generated {len(insights)} insights")
            return insights
            
        except Exception as e:
            self.logger.error(f"MemoryAgent failed: {e}", exc_info=True)
            return []
