# Graph builder module
import networkx as nx
import re
import networkx as nx
import re
from config.settings import Settings
from graph.schema import detect_schema
from utils.paths import STORAGE_BASE


def detect_currency_from_value(value: str) -> str:
    """Detect currency from a value string like '$100' or '₹1000'."""
    if not isinstance(value, str):
        return 'USD'
    
    value = value.strip()
    
    # Check multi-char symbols first
    if value.startswith('A$') or 'AUD' in value.upper():
        return 'AUD'
    if value.startswith('C$') or 'CAD' in value.upper():
        return 'CAD'
    if value.startswith('S$') or 'SGD' in value.upper():
        return 'SGD'
    if value.startswith('CHF') or 'CHF' in value.upper():
        return 'CHF'
    
    # Single char symbols
    if '€' in value:
        return 'EUR'
    if '£' in value:
        return 'GBP'
    if '₹' in value:
        return 'INR'
    if '$' in value and not any(x in value for x in ['A$', 'C$', 'S$']):
        return 'USD'
    if '¥' in value:
        return 'JPY' if '.' not in value else 'CNY'
    
    return 'USD'


class GraphBuilder:
    @staticmethod
    def build(company_id: str, tables: list, default_currency: str = 'USD'):
        """
        Build knowledge graph from tabular data with multi-currency support.
        
        Args:
            company_id: Company identifier
            tables: List of pandas DataFrames
            default_currency: Default currency if none detected
        """
        G = nx.Graph()
        currencies_detected = {}  # Track currency counts

        for df in tables:
            schema = detect_schema(df.columns)
            print(f"📊 Detected schema: {schema}")
            print(f"📊 DataFrame columns: {list(df.columns)}")
            print(f"📊 DataFrame shape: {df.shape}")

            for idx, row in df.iterrows():
                # Create invoice node
                inv_id = f"invoice:{row[schema['invoice']]}" if "invoice" in schema else f"invoice:row_{idx}"
                
                # Get amount and detect currency from the value
                amount_raw = row.get(schema.get("amount"), 0.0)
                currency = default_currency
                
                try:
                    if isinstance(amount_raw, str):
                        # Detect currency from the string value
                        currency = detect_currency_from_value(amount_raw)
                        # Strip currency symbols and commas
                        amount = re.sub(r'[₹$€£¥,\s]', '', amount_raw)
                        amount = float(amount)
                    else:
                        amount = float(amount_raw)
                except:
                    amount = 0.0
                
                # Track currency frequency
                currencies_detected[currency] = currencies_detected.get(currency, 0) + 1
                
                # Store both amount and currency in the invoice node
                G.add_node(inv_id, type="invoice", label=inv_id, amount=amount, currency=currency)

                # Connect to customer (Fallback if missing)
                if "customer" in schema:
                    val = str(row[schema["customer"]])
                    node_id = f"customer:{val}"
                    if not G.has_node(node_id):
                        G.add_node(node_id, type="customer", label=val)
                    G.add_edge(inv_id, node_id, relation="has_customer")
                else:
                    # Fallback for missing customer
                    node_id = "customer:Unknown"
                    if not G.has_node(node_id):
                        G.add_node(node_id, type="customer", label="Unknown Customer")
                    G.add_edge(inv_id, node_id, relation="has_customer")

                # Connect to product (Fallback if missing)
                if "product" in schema:
                    val = str(row[schema["product"]])
                    node_id = f"product:{val}"
                    if not G.has_node(node_id):
                        G.add_node(node_id, type="product", label=val)
                    G.add_edge(inv_id, node_id, relation="has_product")
                else:
                    # Fallback for missing product
                    node_id = "product:General"
                    if not G.has_node(node_id):
                        G.add_node(node_id, type="product", label="General Item")
                    G.add_edge(inv_id, node_id, relation="has_product")

                # Connect to date (Optional)
                if "date" in schema:
                    val = str(row[schema["date"]])
                    node_id = f"date:{val}"
                    if not G.has_node(node_id):
                        G.add_node(node_id, type="date", label=val)
                    G.add_edge(inv_id, node_id, relation="has_date")
                    
        print(f"📊 Built graph with {G.number_of_nodes()} nodes and {G.number_of_edges()} edges")
        print(f"💰 Currencies detected: {currencies_detected}")

        # Save graph using pickle format to USER-SPECIFIC directory
        import pickle
        
        # Primary: User-specific graph directory (Consolidated storage)
        user_graph_dir = STORAGE_BASE / company_id / "graph"
        user_graph_dir.mkdir(parents=True, exist_ok=True)
        user_graph_path = user_graph_dir / f"{company_id}.gpickle"
        
        with open(user_graph_path, 'wb') as f:
            pickle.dump(G, f)
        print(f"✅ Graph saved to user directory: {user_graph_path}")
        
        # Also save to Settings.GRAPH_DIR for backward compatibility
        output_path = Settings.GRAPH_DIR / f"{company_id}.gpickle"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'wb') as f:
            pickle.dump(G, f)
        print(f"✅ Graph also saved to: {output_path}")
        
        return G

