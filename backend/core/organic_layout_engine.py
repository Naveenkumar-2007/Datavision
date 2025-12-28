"""
Organic Layout Engine
=====================
Force-directed positioning with importance-based sizing.

Features:
- Force simulation for natural grouping
- Importance-based sizing (bigger = more important)
- Collision avoidance
- Converts to CSS Grid specification
"""

import numpy as np
from typing import Dict, Any, List, Tuple
from dataclasses import dataclass


@dataclass
class LayoutNode:
    """A node in the organic layout."""
    id: str
    importance: float  # 0-1, determines size
    x: float = 0.0
    y: float = 0.0
    width: float = 1.0
    height: float = 1.0
    vx: float = 0.0  # velocity for simulation
    vy: float = 0.0


class OrganicLayoutEngine:
    """
    Creates organic, force-directed layouts.
    
    Example:
        engine = OrganicLayoutEngine()
        layout = engine.generate(nodes, relationships)
    """
    
    def __init__(self, 
                 attraction: float = 0.1,
                 repulsion: float = 500.0,
                 damping: float = 0.8,
                 iterations: int = 100):
        self.attraction = attraction
        self.repulsion = repulsion
        self.damping = damping
        self.iterations = iterations
    
    def generate(self, 
                 items: List[Dict[str, Any]], 
                 relationships: List[Tuple[int, int]] = None,
                 grid_width: int = 12) -> Dict[str, Any]:
        """
        Generate organic layout for items.
        
        Args:
            items: List of items with 'id', 'importance', 'type'
            relationships: Optional list of (source_idx, target_idx) pairs
            grid_width: CSS grid column count
        
        Returns:
            Layout specification with positions and grid areas
        """
        if not items:
            return {"nodes": [], "grid": []}
        
        # Create nodes from items
        nodes = self._create_nodes(items)
        
        # Initialize positions in a circle
        self._initialize_positions(nodes)
        
        # Run force simulation
        self._run_simulation(nodes, relationships or [])
        
        # Calculate sizes based on importance
        self._calculate_sizes(nodes)
        
        # Convert to grid layout
        grid_spec = self._to_grid_layout(nodes, grid_width)
        
        return {
            "nodes": [self._node_to_dict(n) for n in nodes],
            "grid": grid_spec,
            "css_grid": self._generate_css_grid(nodes, grid_width)
        }
    
    def _create_nodes(self, items: List[Dict]) -> List[LayoutNode]:
        """Create layout nodes from items."""
        nodes = []
        for item in items:
            node = LayoutNode(
                id=str(item.get('id', len(nodes))),
                importance=float(item.get('importance', item.get('priority', 5)) / 10.0)
            )
            nodes.append(node)
        return nodes
    
    def _initialize_positions(self, nodes: List[LayoutNode]):
        """Initialize nodes in a circle."""
        n = len(nodes)
        for i, node in enumerate(nodes):
            angle = 2 * np.pi * i / n
            radius = 2.0
            node.x = radius * np.cos(angle)
            node.y = radius * np.sin(angle)
    
    def _run_simulation(self, nodes: List[LayoutNode], relationships: List[Tuple[int, int]]):
        """Run force-directed simulation."""
        for _ in range(self.iterations):
            # Reset forces
            forces = [(0.0, 0.0) for _ in nodes]
            
            # Repulsion between all nodes
            for i, node_i in enumerate(nodes):
                for j, node_j in enumerate(nodes):
                    if i >= j:
                        continue
                    
                    dx = node_i.x - node_j.x
                    dy = node_i.y - node_j.y
                    dist = np.sqrt(dx*dx + dy*dy) + 0.1
                    
                    # Coulomb-like repulsion
                    force = self.repulsion / (dist * dist)
                    fx = force * dx / dist
                    fy = force * dy / dist
                    
                    forces[i] = (forces[i][0] + fx, forces[i][1] + fy)
                    forces[j] = (forces[j][0] - fx, forces[j][1] - fy)
            
            # Attraction for related nodes
            for src, tgt in relationships:
                if src < len(nodes) and tgt < len(nodes):
                    dx = nodes[tgt].x - nodes[src].x
                    dy = nodes[tgt].y - nodes[src].y
                    dist = np.sqrt(dx*dx + dy*dy) + 0.1
                    
                    force = self.attraction * dist
                    fx = force * dx / dist
                    fy = force * dy / dist
                    
                    forces[src] = (forces[src][0] + fx, forces[src][1] + fy)
                    forces[tgt] = (forces[tgt][0] - fx, forces[tgt][1] - fy)
            
            # Apply forces with damping
            for i, node in enumerate(nodes):
                node.vx = (node.vx + forces[i][0]) * self.damping
                node.vy = (node.vy + forces[i][1]) * self.damping
                node.x += node.vx * 0.1
                node.y += node.vy * 0.1
    
    def _calculate_sizes(self, nodes: List[LayoutNode]):
        """Calculate sizes based on importance."""
        for node in nodes:
            # Size range: 1-3 grid units based on importance
            base_size = 1.0 + node.importance * 2.0
            node.width = base_size
            node.height = base_size * 0.75  # Maintain aspect ratio
    
    def _to_grid_layout(self, nodes: List[LayoutNode], grid_width: int) -> List[Dict]:
        """Convert node positions to grid layout."""
        if not nodes:
            return []
        
        # Normalize positions to 0-grid_width range
        min_x = min(n.x for n in nodes)
        max_x = max(n.x for n in nodes)
        min_y = min(n.y for n in nodes)
        max_y = max(n.y for n in nodes)
        
        range_x = max_x - min_x + 0.1
        range_y = max_y - min_y + 0.1
        
        grid_items = []
        for node in nodes:
            # Normalize to grid coordinates
            col = int((node.x - min_x) / range_x * (grid_width - int(node.width)))
            row = int((node.y - min_y) / range_y * 10)  # 10 rows max
            
            grid_items.append({
                "id": node.id,
                "col_start": max(1, col + 1),
                "col_end": min(grid_width + 1, col + int(node.width) + 1),
                "row_start": max(1, row + 1),
                "row_end": row + int(node.height) + 2,
                "importance": node.importance
            })
        
        # Resolve overlaps
        grid_items = self._resolve_overlaps(grid_items, grid_width)
        
        return grid_items
    
    def _resolve_overlaps(self, items: List[Dict], grid_width: int) -> List[Dict]:
        """Resolve overlapping grid items."""
        occupied = set()
        result = []
        
        # Sort by importance (highest first)
        sorted_items = sorted(items, key=lambda x: -x['importance'])
        
        for item in sorted_items:
            # Find non-overlapping position
            placed = False
            
            for row in range(1, 20):  # Max 20 rows
                for col in range(1, grid_width + 1):
                    width = item['col_end'] - item['col_start']
                    height = item['row_end'] - item['row_start']
                    
                    if col + width > grid_width + 1:
                        continue
                    
                    # Check if space is free
                    cells_needed = set()
                    for r in range(row, row + height):
                        for c in range(col, col + width):
                            cells_needed.add((r, c))
                    
                    if not cells_needed & occupied:
                        # Place item here
                        occupied.update(cells_needed)
                        result.append({
                            **item,
                            "col_start": col,
                            "col_end": col + width,
                            "row_start": row,
                            "row_end": row + height
                        })
                        placed = True
                        break
                
                if placed:
                    break
            
            if not placed:
                # Fallback: place at end
                max_row = max((i['row_end'] for i in result), default=1)
                result.append({
                    **item,
                    "row_start": max_row,
                    "row_end": max_row + 2
                })
        
        return result
    
    def _generate_css_grid(self, nodes: List[LayoutNode], grid_width: int) -> str:
        """Generate CSS grid template."""
        grid_items = self._to_grid_layout(nodes, grid_width)
        max_row = max((i['row_end'] for i in grid_items), default=2)
        
        css = f"""
.organic-layout {{
    display: grid;
    grid-template-columns: repeat({grid_width}, 1fr);
    grid-template-rows: repeat({max_row}, minmax(200px, auto));
    gap: 16px;
    padding: 16px;
}}
"""
        
        for i, item in enumerate(grid_items):
            css += f"""
.organic-item-{item['id']} {{
    grid-column: {item['col_start']} / {item['col_end']};
    grid-row: {item['row_start']} / {item['row_end']};
}}
"""
        
        return css
    
    def _node_to_dict(self, node: LayoutNode) -> Dict[str, Any]:
        """Convert node to dictionary."""
        return {
            "id": node.id,
            "x": float(node.x),
            "y": float(node.y),
            "width": float(node.width),
            "height": float(node.height),
            "importance": float(node.importance)
        }
