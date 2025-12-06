# Graph builder module
import networkx as nx
from config.settings import Settings
from graph.schema import detect_schema


class GraphBuilder:
    @staticmethod
    def build(company_id: str, tables: list):
        """
        Build knowledge graph from tabular data
        
        Args:
            company_id: Company identifier
            tables: List of pandas DataFrames
        """
        G = nx.Graph()

        for df in tables:
            schema = detect_schema(df.columns)

            for idx, row in df.iterrows():
                # Create invoice node
                inv_id = f"invoice:{row[schema['invoice']]}" if "invoice" in schema else f"invoice:row_{idx}"
                
                # Get amount and clean currency symbols
                amount = row.get(schema.get("amount"), 0.0)
                try:
                    # Strip currency symbols (₹, $, €, £) and commas
                    if isinstance(amount, str):
                        import re
                        amount = re.sub(r'[₹$€£,\s]', '', amount)
                    amount = float(amount)
                except:
                    amount = 0.0
                
                G.add_node(inv_id, type="invoice", label=inv_id, amount=amount)

                # Connect to customer, product, date nodes
                for key in ["customer", "product", "date"]:
                    if key in schema:
                        val = str(row[schema[key]])
                        node_id = f"{key}:{val}"
                        
                        # Add node if doesn't exist
                        if not G.has_node(node_id):
                            G.add_node(node_id, type=key, label=val)
                        
                        # Add edge
                        G.add_edge(inv_id, node_id, relation=f"has_{key}")

        # Save graph using pickle format (compatible with all NetworkX versions)
        import pickle
        output_path = Settings.GRAPH_DIR / f"{company_id}.gpickle"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'wb') as f:
            pickle.dump(G, f)
        
        return G
