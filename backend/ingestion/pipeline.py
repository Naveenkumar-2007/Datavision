# Ingestion pipeline module
"""
Enhanced ingestion with:
1. Semantic chunking for better RAG
2. Cache invalidation on data change
3. Hybrid search index building
4. Aggregated summary chunks for accurate analytics
"""
import shutil
import pandas as pd
from pathlib import Path
from typing import List
from fastapi import UploadFile

from config.settings import Settings
from ingestion.loader import Loader
from ingestion.processor import Processor
from core.llm import embed_texts
from vector.store_faiss import FaissStore
from graph.builder import GraphBuilder


class IngestionPipeline:
    def __init__(self):
        # Use semantic chunking by default for better RAG accuracy
        self.processor = Processor(
            Settings.CHUNK_SIZE,
            Settings.CHUNK_OVERLAP,
            strategy="semantic"  # Changed from fixed to semantic
        )
        # Don't create store in __init__ - create it in ingest() after paths are set
        self.store = None

    def process(self, uploaded_files: list, user_id: str, base_path: Path = None):
        """
        Process already-saved files into the knowledge graph.
        This is the main entry point called by files.py after files are saved to disk.
        
        Args:
            uploaded_files: List of dicts with file info (id, name, etc.)
            user_id: User/company identifier
            base_path: Base storage path for user files
        """
        from pathlib import Path
        from utils.paths import get_user_paths
        
        print(f"📥 Processing {len(uploaded_files)} files for user {user_id}")
        
        # Get user-specific paths
        paths = get_user_paths(user_id)
        files_dir = paths["files"]
        
        # Process each file from disk
        texts = []
        tables = []
        table_sources = []  # Track source filename for each table
        metadata = []
        processed_files = []
        
        for file_info in uploaded_files:
            filename = file_info.get("name") or file_info.get("id")
            file_path = files_dir / filename
            
            print(f"📄 Processing: {file_path}")
            
            if not file_path.exists():
                print(f"⚠️ File not found: {file_path}")
                continue
            
            try:
                result = Loader.load(file_path)
                processed_files.append(filename)
                
                if result["type"] == "text":
                    clean_text = self.processor.clean(result["content"])
                    chunks = self.processor.chunk(clean_text)
                    texts.extend(chunks)
                    metadata.extend([
                        {"company": user_id, "source": filename, "chunk": i, "text": chunks[i]}
                        for i in range(len(chunks))
                    ])
                    print(f"📝 Text file: {len(chunks)} chunks")
                    
                elif result["type"] == "table":
                    tables.append(result["df"])
                    table_sources.append(filename)  # Track source file for this table
                    df = result["df"]
                    
                    # Create summary chunks for RAG
                    summary_chunks = self._create_table_summary_chunks(df, filename, user_id)
                    texts.extend(summary_chunks)
                    metadata.extend([
                        {"company": user_id, "source": filename, "chunk": i, "type": "table_summary", "text": summary_chunks[i]}
                        for i in range(len(summary_chunks))
                    ])
                    
                    # Create row-based chunks
                    row_chunks = self._create_row_based_chunks(df, filename)
                    texts.extend(row_chunks)
                    metadata.extend([
                        {"company": user_id, "source": filename, "chunk": len(summary_chunks) + i, "type": "table_rows", "text": row_chunks[i]}
                        for i in range(len(row_chunks))
                    ])
                    print(f"📊 Table: {len(df)} rows, {len(summary_chunks)} summaries, {len(row_chunks)} row chunks")
                    
                elif result["type"] == "json":
                    import json
                    json_text = json.dumps(result["json"], indent=2)
                    chunks = self.processor.chunk(json_text)
                    texts.extend(chunks)
                    metadata.extend([
                        {"company": user_id, "source": filename, "chunk": i, "type": "json", "text": chunks[i]}
                        for i in range(len(chunks))
                    ])
                    print(f"📋 JSON: {len(chunks)} chunks")
                    
            except Exception as e:
                print(f"⚠️ Error processing {filename}: {e}")
                import traceback
                traceback.print_exc()
                continue
        
        # Embed and store text chunks
        if texts:
            self.store = FaissStore.load_or_create(user_id=user_id, fresh=True)
            print(f"🧠 Embedding {len(texts)} chunks from {len(processed_files)} files...")
            embeddings = embed_texts(texts)
            self.store.add(embeddings, metadata)
            self.store.save(user_id=user_id)
            print(f"✅ FAISS index saved with {self.store.index.ntotal} vectors")
            
            self._rebuild_hybrid_index(user_id)
        else:
            print(f"⚠️ No text chunks to embed")
        
        # Build knowledge graph from tables
        if tables:
            print(f"🔗 Building knowledge graph from {len(tables)} tables from files: {table_sources}")
            
            # Detect user's primary currency from their files
            try:
                from utils.currency import load_currency_metadata, detect_and_save_user_currency
                from utils.paths import STORAGE_BASE
                user_currency = load_currency_metadata(user_id, STORAGE_BASE)
                if not user_currency:
                    user_currency = detect_and_save_user_currency(user_id, paths["files"], STORAGE_BASE)
                print(f"💰 Using detected currency for graph: {user_currency}")
            except Exception as e:
                print(f"⚠️ Currency detection error: {e}")
                user_currency = 'USD'
            
            GraphBuilder.build(user_id, tables, default_currency=user_currency, source_files=table_sources)
            print(f"✅ Knowledge graph built with source tracking and currency: {user_currency}")
        else:
            print(f"ℹ️ No tables found for graph building")
        
        result = {"chunks": len(texts), "tables": len(tables), "files_processed": len(processed_files)}
        print(f"✅ Processing complete: {result}")
        return result

    def ingest(self, company_id: str, files: List[UploadFile], fresh: bool = False, skip_save: bool = False):
        """
        Ingest uploaded files: load, process, embed, and build graph.
        
        Args:
            company_id: User/company identifier
            files: List of file objects to process
            fresh: If True, create fresh indexes (for retraining after file deletion)
            skip_save: If True, don't save files (they already exist - for retraining)
        """
        # Invalidate cache for this user since data is changing
        self._invalidate_user_cache(company_id)
        
        # For retraining, use parent directory (files are already in their location)
        if skip_save:
            company_dir = Settings.UPLOADS
        else:
            company_dir = Settings.UPLOADS / company_id
            company_dir.mkdir(parents=True, exist_ok=True)

        texts = []
        tables = []
        metadata = []
        processed_files = []
        
        print(f"📥 Ingesting {len(files)} files for {company_id} (fresh={fresh}, skip_save={skip_save})")
        print(f"📂 Working directory: {company_dir}")
        print(f"📝 Using semantic chunking for better RAG accuracy")

        for file in files:
            # For retraining (skip_save=True), file path is the actual path
            # For new uploads, we need to construct the path
            if skip_save:
                # File already exists - get path from file object if available
                if hasattr(file, '_path'):
                    file_path = file._path
                else:
                    file_path = company_dir / file.filename
            else:
                file_path = company_dir / file.filename
            
            # Only save file if not skipping (new upload vs retrain)
            if not skip_save:
                # Reset file pointer to beginning
                file.file.seek(0)
                
                with open(file_path, "wb") as f:
                    shutil.copyfileobj(file.file, f)
                print(f"💾 Saved file: {file.filename}")
            else:
                # For retraining, file already exists - just reset pointer
                file.file.seek(0)
                print(f"📄 Processing existing file: {file.filename} at {file_path}")

            # Verify file exists before loading
            if not file_path.exists():
                print(f"⚠️ File not found: {file_path}, skipping")
                continue

            # Load file content
            try:
                result = Loader.load(file_path)
                processed_files.append(file.filename)
            except Exception as e:
                print(f"⚠️ Error loading {file.filename}: {e}")
                continue

            if result["type"] == "text":
                # Process text content with semantic chunking
                clean_text = self.processor.clean(result["content"])
                chunks = self.processor.chunk(clean_text)
                texts.extend(chunks)
                metadata.extend([
                    {"company": company_id, "source": file.filename, "chunk": i, "text": chunks[i]}
                    for i in range(len(chunks))
                ])
                print(f"📝 Text file: {len(chunks)} semantic chunks")

            elif result["type"] == "table":
                tables.append(result["df"])
                df = result["df"]
                
                # Create AGGREGATED SUMMARY chunks for accurate RAG answers
                summary_chunks = self._create_table_summary_chunks(df, file.filename, company_id)
                texts.extend(summary_chunks)
                metadata.extend([
                    {"company": company_id, "source": file.filename, "chunk": i, "type": "table_summary", "text": summary_chunks[i]}
                    for i in range(len(summary_chunks))
                ])
                
                # Create ROW-BASED chunks to preserve transaction integrity
                # This ensures each row is complete and searchable
                row_chunks = self._create_row_based_chunks(df, file.filename)
                texts.extend(row_chunks)
                metadata.extend([
                    {"company": company_id, "source": file.filename, "chunk": len(summary_chunks) + i, "type": "table_rows", "text": row_chunks[i]}
                    for i in range(len(row_chunks))
                ])
                print(f"📊 Table file: {len(df)} rows, {len(summary_chunks)} summary chunks, {len(row_chunks)} row chunks")

            elif result["type"] == "json":
                # Convert JSON to text and chunk
                import json
                json_text = json.dumps(result["json"], indent=2)
                chunks = self.processor.chunk(json_text)
                texts.extend(chunks)
                metadata.extend([
                    {"company": company_id, "source": file.filename, "chunk": i, "type": "json", "text": chunks[i]}
                    for i in range(len(chunks))
                ])
                print(f"📋 JSON file: {len(chunks)} chunks")

        # Embed and store text chunks
        if texts:
            # Create FRESH store for retraining, or load existing for new uploads
            if self.store is None:
                self.store = FaissStore.load_or_create(user_id=company_id, fresh=fresh)
            
            print(f"🧠 Embedding {len(texts)} text chunks from {len(processed_files)} files...")
            embeddings = embed_texts(texts)
            self.store.add(embeddings, metadata)
            self.store.save(user_id=company_id)
            print(f"✅ FAISS index saved with {self.store.index.ntotal} vectors")
            
            # Rebuild hybrid search index
            self._rebuild_hybrid_index(company_id)
        else:
            print(f"⚠️ No text chunks to embed")

        # Build knowledge graph from tables (always fresh for consistency)
        if tables:
            print(f"🔗 Building knowledge graph from {len(tables)} tables...")
            GraphBuilder.build(company_id, tables)
            print(f"✅ Knowledge graph built")
        else:
            print(f"ℹ️ No tables found for graph building")

        result = {"chunks": len(texts), "tables": len(tables), "files_processed": len(processed_files)}
        print(f"✅ Ingestion complete: {result}")
        return result
    
    def _create_table_summary_chunks(self, df, source_file: str, user_id: str = None) -> list:
        """
        Create aggregated summary chunks from tabular data for accurate RAG.
        This ensures questions like "top customers" get CORRECT aggregated answers.
        """
        import re
        import json
        chunks = []
        
        # DETECT CURRENCY FROM ACTUAL DATA FIRST (most reliable)
        currency_symbol = '₹'  # Default
        currency_detected = False
        
        # Strategy 1: Detect from amount values in DataFrame
        amount_cols = [c for c in df.columns if any(
            term in c.lower() for term in ['amount', 'total', 'price', 'revenue', 'sales', 'value', 'cost']
        )]
        
        for col in amount_cols:
            sample = df[col].dropna().head(20).astype(str)
            for val in sample:
                val_str = str(val)
                if '$' in val_str:
                    currency_symbol = '$'
                    currency_detected = True
                    print(f"💰 Detected USD ($) from data column {col}")
                    break
                elif '€' in val_str:
                    currency_symbol = '€'
                    currency_detected = True
                    print(f"💰 Detected EUR (€) from data column {col}")
                    break
                elif '₹' in val_str:
                    currency_symbol = '₹'
                    currency_detected = True
                    print(f"💰 Detected INR (₹) from data column {col}")
                    break
                elif '£' in val_str:
                    currency_symbol = '£'
                    currency_detected = True
                    print(f"💰 Detected GBP (£) from data column {col}")
                    break
            if currency_detected:
                break
        
        # Strategy 2: Check for currency column
        if not currency_detected:
            currency_cols = [c for c in df.columns if 'currency' in c.lower()]
            if currency_cols:
                currency_val = str(df[currency_cols[0]].iloc[0]).upper()
                currency_map = {'USD': '$', 'EUR': '€', 'INR': '₹', 'GBP': '£'}
                if currency_val in currency_map:
                    currency_symbol = currency_map[currency_val]
                    currency_detected = True
                    print(f"💰 Detected {currency_val} from currency column")
        
        # Strategy 3: Check filename
        if not currency_detected:
            filename_lower = source_file.lower()
            if 'usd' in filename_lower or 'dollar' in filename_lower or 'us_' in filename_lower:
                currency_symbol = '$'
                currency_detected = True
                print(f"💰 Detected USD from filename: {source_file}")
            elif 'euro' in filename_lower or 'eur' in filename_lower:
                currency_symbol = '€'
                currency_detected = True
                print(f"💰 Detected EUR from filename: {source_file}")
            elif 'gbp' in filename_lower or 'pound' in filename_lower:
                currency_symbol = '£'
                currency_detected = True
                print(f"💰 Detected GBP from filename: {source_file}")
        
        # Strategy 4: Fall back to stored metadata only if nothing detected
        if not currency_detected and user_id:
            try:
                metadata_path = Settings.STORAGE / "users" / user_id / "metadata.json"
                if metadata_path.exists():
                    with open(metadata_path, 'r') as f:
                        meta = json.load(f)
                        stored_currency = meta.get('currency', 'INR')
                        currency_map = {'INR': '₹', 'USD': '$', 'EUR': '€', 'GBP': '£'}
                        currency_symbol = currency_map.get(stored_currency, '₹')
                        print(f"💰 Using stored currency: {stored_currency} ({currency_symbol})")
            except Exception as e:
                print(f"⚠️ Could not read user metadata: {e}")
        
        print(f"💰 Final currency symbol for {source_file}: {currency_symbol}")
        
        # Make a copy to avoid modifying original
        df = df.copy()
        
        # Detect column names (case-insensitive)
        cols_lower = {col.lower().strip(): col for col in df.columns}
        
        # Helper function to find column by partial match
        def find_column(keywords):
            # First try exact match
            for key in keywords:
                if key in cols_lower:
                    return cols_lower[key]
            # Then try partial/contains match
            for col_lower, col_orig in cols_lower.items():
                for key in keywords:
                    if key in col_lower or col_lower in key:
                        return col_orig
            return None
        
        # Find customer column
        customer_col = find_column(['customer', 'customer_name', 'client', 'client_name', 'buyer', 'name'])
        
        # Find amount column - be more specific to avoid wrong columns
        amount_col = None
        amount_keywords = ['total', 'amount', 'total_amount', 'revenue', 'sales', 'price', 'value', 'grand_total', 'eur', 'usd', 'inr']
        
        # First try exact match
        for key in amount_keywords:
            if key in cols_lower:
                amount_col = cols_lower[key]
                break
        
        # If not found, try partial match
        if not amount_col:
            for col_lower, col_orig in cols_lower.items():
                for key in ['amount', 'total', 'revenue', 'price', 'sales', 'value']:
                    if key in col_lower:
                        # Verify it looks like a numeric column
                        try:
                            sample_val = df[col_orig].dropna().iloc[0] if len(df[col_orig].dropna()) > 0 else None
                            if sample_val is not None:
                                test_str = str(sample_val)
                                if test_str.count('₹') <= 1 and test_str.count('$') <= 1 and test_str.count('€') <= 1:
                                    amount_col = col_orig
                                    break
                        except:
                            continue
                if amount_col:
                    break
        
        # Find product column
        product_col = find_column(['product', 'product_name', 'item', 'item_name', 'sku', 'goods'])
        
        # Find date column
        date_col = find_column(['date', 'order_date', 'invoice_date', 'transaction_date', 'created'])
        
        print(f"📊 Detected columns: customer={customer_col}, amount={amount_col}, product={product_col}, date={date_col}")
        print(f"📊 All columns: {list(df.columns)}")
        
        # Clean amount column if found - with robust error handling
        import pandas as pd_local  # Local import to avoid closure issue
        amount_valid = False
        if amount_col:
            try:
                def clean_amount(x):
                    if pd_local.isna(x):
                        return 0.0
                    s = str(x).strip()
                    # Remove currency symbols and spaces
                    s = re.sub(r'[₹$€£,\s]', '', s)
                    # If still has multiple numbers concatenated, take only the first
                    if s and not s.replace('.', '').replace('-', '').isdigit():
                        # Try to extract first number
                        match = re.search(r'[\d.]+', s)
                        if match:
                            s = match.group()
                    try:
                        return float(s) if s else 0.0
                    except:
                        return 0.0
                
                df['_amount_clean'] = df[amount_col].apply(clean_amount)
                amount_col = '_amount_clean'
                amount_valid = True
                print(f"📊 Amount column cleaned successfully, sample: {df[amount_col].head(3).tolist()}")
            except Exception as e:
                print(f"⚠️ Error cleaning amount column: {e}")
                amount_valid = False
        
        # Create summary statistics chunk
        summary = f"=== DATA SUMMARY FROM {source_file} ===\n"
        summary += f"Total Records: {len(df)}\n"
        
        if amount_valid:
            total_revenue = df[amount_col].sum()
            avg_order = df[amount_col].mean()
            summary += f"Total Revenue: {currency_symbol}{total_revenue:,.2f}\n"
            summary += f"Average Order Value: {currency_symbol}{avg_order:,.2f}\n"
        
        if customer_col:
            unique_customers = df[customer_col].nunique()
            summary += f"Unique Customers: {unique_customers}\n"
        
        if product_col:
            unique_products = df[product_col].nunique()
            summary += f"Unique Products: {unique_products}\n"
        
        chunks.append(summary)
        
        # Create CUSTOMER REVENUE RANKINGS (TOP and BOTTOM)
        if customer_col and amount_valid:
            try:
                customer_revenue = df.groupby(customer_col)[amount_col].agg(['sum', 'count']).reset_index()
                customer_revenue.columns = [customer_col, 'total_revenue', 'order_count']
                customer_revenue_desc = customer_revenue.sort_values('total_revenue', ascending=False)
                customer_revenue_asc = customer_revenue.sort_values('total_revenue', ascending=True)
                
                # TOP customers chunk
                top_customers_chunk = f"=== TOP REVENUE CUSTOMERS (AGGREGATED FROM ALL {len(df)} RECORDS) ===\n"
                top_customers_chunk += f"Source: {source_file}\n"
                top_customers_chunk += f"Total Unique Customers: {len(customer_revenue)}\n\n"
                top_customers_chunk += "TOP 20 CUSTOMERS BY TOTAL REVENUE (HIGHEST SPENDERS):\n"
                
                for idx, (_, row) in enumerate(customer_revenue_desc.head(20).iterrows(), 1):
                    top_customers_chunk += f"{idx}. {row[customer_col]}: {currency_symbol}{row['total_revenue']:,.2f} ({int(row['order_count'])} orders)\n"
                
                top_customers_chunk += f"\nTOP 3 HIGHEST SPENDING CUSTOMERS:\n"
                for idx, (_, row) in enumerate(customer_revenue_desc.head(3).iterrows(), 1):
                    top_customers_chunk += f"  #{idx}: {row[customer_col]} - Total Revenue: {currency_symbol}{row['total_revenue']:,.2f} from {int(row['order_count'])} orders\n"
                
                chunks.append(top_customers_chunk)
                
                # BOTTOM/LOWEST customers chunk
                bottom_customers_chunk = f"=== LOWEST REVENUE CUSTOMERS (AGGREGATED FROM ALL {len(df)} RECORDS) ===\n"
                bottom_customers_chunk += f"Source: {source_file}\n"
                bottom_customers_chunk += f"Total Unique Customers: {len(customer_revenue)}\n\n"
                bottom_customers_chunk += "BOTTOM 20 CUSTOMERS BY TOTAL REVENUE (LOWEST SPENDERS):\n"
                
                for idx, (_, row) in enumerate(customer_revenue_asc.head(20).iterrows(), 1):
                    bottom_customers_chunk += f"{idx}. {row[customer_col]}: {currency_symbol}{row['total_revenue']:,.2f} ({int(row['order_count'])} orders)\n"
                
                bottom_customers_chunk += f"\nBOTTOM 3 LOWEST SPENDING CUSTOMERS:\n"
                for idx, (_, row) in enumerate(customer_revenue_asc.head(3).iterrows(), 1):
                    bottom_customers_chunk += f"  #{idx}: {row[customer_col]} - Total Revenue: {currency_symbol}{row['total_revenue']:,.2f} from {int(row['order_count'])} orders\n"
                
                # Add the single lowest customer explicitly
                lowest = customer_revenue_asc.iloc[0]
                bottom_customers_chunk += f"\n🔻 LOWEST SPENDING CUSTOMER: {lowest[customer_col]} with {currency_symbol}{lowest['total_revenue']:,.2f} from {int(lowest['order_count'])} orders\n"
                
                chunks.append(bottom_customers_chunk)
                print(f"📊 Created customer revenue summaries (top & bottom) with {len(customer_revenue)} customers")
            except Exception as e:
                print(f"⚠️ Error creating customer summary: {e}")
        
        # Create PRODUCT REVENUE RANKINGS (TOP and BOTTOM)
        if product_col and amount_valid:
            try:
                product_revenue = df.groupby(product_col)[amount_col].agg(['sum', 'count']).reset_index()
                product_revenue.columns = [product_col, 'total_revenue', 'order_count']
                product_revenue_desc = product_revenue.sort_values('total_revenue', ascending=False)
                product_revenue_asc = product_revenue.sort_values('total_revenue', ascending=True)
                
                # TOP products chunk
                top_products_chunk = f"=== TOP REVENUE PRODUCTS (AGGREGATED FROM ALL {len(df)} RECORDS) ===\n"
                top_products_chunk += f"Source: {source_file}\n"
                top_products_chunk += f"Total Unique Products: {len(product_revenue)}\n\n"
                top_products_chunk += "TOP PRODUCTS BY TOTAL REVENUE (BEST SELLERS):\n"
                
                for idx, (_, row) in enumerate(product_revenue_desc.head(15).iterrows(), 1):
                    top_products_chunk += f"{idx}. {row[product_col]}: {currency_symbol}{row['total_revenue']:,.2f} ({int(row['order_count'])} sales)\n"
                
                chunks.append(top_products_chunk)
                
                # BOTTOM products chunk
                bottom_products_chunk = f"=== LOWEST REVENUE PRODUCTS (AGGREGATED FROM ALL {len(df)} RECORDS) ===\n"
                bottom_products_chunk += f"Source: {source_file}\n"
                bottom_products_chunk += f"Total Unique Products: {len(product_revenue)}\n\n"
                bottom_products_chunk += "BOTTOM PRODUCTS BY TOTAL REVENUE (LOWEST SELLERS):\n"
                
                for idx, (_, row) in enumerate(product_revenue_asc.head(10).iterrows(), 1):
                    bottom_products_chunk += f"{idx}. {row[product_col]}: {currency_symbol}{row['total_revenue']:,.2f} ({int(row['order_count'])} sales)\n"
                
                # Add the single lowest product explicitly
                lowest_prod = product_revenue_asc.iloc[0]
                bottom_products_chunk += f"\n🔻 LOWEST SELLING PRODUCT: {lowest_prod[product_col]} with {currency_symbol}{lowest_prod['total_revenue']:,.2f} from {int(lowest_prod['order_count'])} sales\n"
                
                chunks.append(bottom_products_chunk)
                print(f"📊 Created product revenue summaries (top & bottom) with {len(product_revenue)} products")
            except Exception as e:
                print(f"⚠️ Error creating product summary: {e}")
        
        # Create monthly trends if date column exists
        if date_col and amount_valid:
            try:
                df['_date_parsed'] = pd_local.to_datetime(df[date_col], errors='coerce')
                df_dated = df[df['_date_parsed'].notna()].copy()
                
                if not df_dated.empty:
                    df_dated['_month'] = df_dated['_date_parsed'].dt.to_period('M')
                    monthly = df_dated.groupby('_month')[amount_col].sum().reset_index()
                    
                    trends_chunk = f"=== MONTHLY REVENUE TRENDS ===\n"
                    trends_chunk += f"Source: {source_file}\n\n"
                    
                    for _, row in monthly.iterrows():
                        trends_chunk += f"{row['_month']}: {currency_symbol}{row[amount_col]:,.2f}\n"
                    
                    chunks.append(trends_chunk)
                    print(f"📊 Created monthly trends with {len(monthly)} months")
            except Exception as e:
                print(f"⚠️ Error creating trends: {e}")
        
        return chunks
    
    def _create_row_based_chunks(self, df, source_file: str, rows_per_chunk: int = 25) -> list:
        """
        Create chunks where each chunk contains complete rows of data.
        This ensures transaction integrity - no row is split across chunks.
        
        Args:
            df: DataFrame to chunk
            source_file: Source filename
            rows_per_chunk: Number of rows per chunk (default 25 for ~500 tokens)
            
        Returns:
            List of text chunks with complete row data
        """
        chunks = []
        columns = list(df.columns)
        header = f"=== DATA RECORDS FROM {source_file} ===\nColumns: {', '.join(columns)}\n\n"
        
        total_rows = len(df)
        
        for start_idx in range(0, total_rows, rows_per_chunk):
            end_idx = min(start_idx + rows_per_chunk, total_rows)
            chunk_df = df.iloc[start_idx:end_idx]
            
            chunk_text = f"{header}Records {start_idx + 1} to {end_idx} of {total_rows}:\n\n"
            
            for idx, (_, row) in enumerate(chunk_df.iterrows(), start_idx + 1):
                row_text = f"Record {idx}: "
                row_parts = []
                for col in columns:
                    value = row[col]
                    if pd.notna(value):
                        row_parts.append(f"{col}={value}")
                row_text += ", ".join(row_parts)
                chunk_text += row_text + "\n"
            
            chunks.append(chunk_text)
        
        print(f"📊 Created {len(chunks)} row-based chunks from {total_rows} records")
        return chunks
    
    def _invalidate_user_cache(self, company_id: str):
        """Invalidate query cache when data changes"""
        try:
            from core.cache import get_cache
            cache = get_cache()
            cache.invalidate(user_id=company_id)
            print(f"🗑️ Cache invalidated for {company_id}")
        except ImportError:
            pass
        except Exception as e:
            print(f"⚠️ Cache invalidation error: {e}")
    
    def _rebuild_hybrid_index(self, company_id: str):
        """Rebuild BM25 index for hybrid search"""
        try:
            from vector.hybrid_search import HybridSearcher
            store = FaissStore.load_or_create(user_id=company_id)
            searcher = HybridSearcher(store)
            searcher.rebuild_index()
            print(f"✅ Hybrid search index rebuilt")
        except ImportError:
            print(f"ℹ️ Hybrid search not available")
        except Exception as e:
            print(f"⚠️ Hybrid index rebuild error: {e}")

