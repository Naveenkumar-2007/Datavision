
import networkx as nx
import json
import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

try:
    from agents.graph_visualizations import generate_mindmap, generate_knowledge_graph
except ImportError as e:
    print(f"❌ ImportError: {e}")
    sys.exit(1)

def create_mock_graph():
    G = nx.Graph()
    # Create hierarchy: Region -> Country -> City
    G.add_edge("North America", "USA")
    G.add_edge("North America", "Canada")
    G.add_edge("USA", "New York")
    G.add_edge("USA", "California")
    G.add_edge("USA", "Texas")
    G.add_edge("Canada", "Ontario")
    G.add_edge("Canada", "Quebec")
    
    # Add types
    G.nodes["North America"]["type"] = "Region"
    G.nodes["USA"]["type"] = "Country"
    G.nodes["Canada"]["type"] = "Country"
    G.nodes["New York"]["type"] = "City"
    
    # Add extra connections for community detection
    G.add_edge("New York", "California") # Cross connection
    G.add_edge("Texas", "California")
    
    return G

def test_mindmap():
    print("\n🧪 Testing Mindmap Generation...")
    G = create_mock_graph()
    chart, explanation = generate_mindmap(G, query="Show hierarchy", focus_entity="North America")
    
    if chart and "data" in chart and "layout" in chart:
        print("✅ Mindmap JSON generated successfully")
        print(f"   Nodes: {len(chart['data'][1]['x'])}")
        print(f"   Edges: {len(chart['data'][0]['x']) // 3}")
        print(f"   Layout Title: {chart['layout']['title']['text']}")
    else:
        print("❌ Mindmap generation failed")
        print(chart)

def test_knowledge_graph():
    print("\n🧪 Testing Knowledge Graph Generation...")
    G = create_mock_graph()
    chart, explanation = generate_knowledge_graph(G, query="Analyze network")
    
    if chart and "data" in chart and "layout" in chart:
        print("✅ Knowledge Graph JSON generated successfully")
        # Check for community colors (should be more than 1 color if communities detected)
        colors = chart['data'][1]['marker']['color']
        unique_colors = set(colors)
        print(f"   Nodes: {len(colors)}")
        print(f"   Detected Communities (Unique Colors): {len(unique_colors)}")
    else:
        print("❌ Knowledge Graph generation failed")

if __name__ == "__main__":
    test_mindmap()
    test_knowledge_graph()
