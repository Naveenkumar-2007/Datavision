# Agent workflow orchestration
"""
Enterprise workflow with:
1. CacheRAG - Cached responses for speed/cost
2. Adaptive RAG - Intelligent routing
3. Persistent Memory - Personalization
4. Graph-First Architecture - Knowledge graph priority
"""
from agents.state import AgentState
from agents.router import route_question
from agents.nodes import rag_answer, graph_answer, hybrid_answer, fallback_answer
from graph.query import load_graph
from vector.store_faiss import FaissStore


def run_business_query(
    company_id: str,
    question: str,
    use_cache: bool = True,
    use_memory: bool = True
) -> dict:
    """
    Main workflow: Route question and execute appropriate agent
    
    Args:
        company_id: Company identifier
        question: Business question from user
        use_cache: Enable query caching (default: True)
        use_memory: Enable personalized context (default: True)
        
    Returns:
        Dictionary with answer, route, and metadata
    """
    # Check cache first (CacheRAG)
    if use_cache:
        try:
            from core.cache import get_cache
            cache = get_cache()
            cached = cache.get(question, company_id)
            
            if cached:
                return {
                    "question": question,
                    "answer": cached.response,
                    "route": cached.route,
                    "company_id": company_id,
                    "cached": True,
                    "cache_hits": cached.hit_count
                }
        except ImportError:
            pass
        except Exception as e:
            print(f"⚠️ Cache lookup error: {e}")
    
    # Get personalized context (Persistent Memory)
    user_context = ""
    if use_memory:
        try:
            from core.memory import get_user_context
            user_context = get_user_context(company_id)
        except ImportError:
            pass
        except Exception as e:
            print(f"⚠️ Memory lookup error: {e}")
    
    # Initialize state
    state = AgentState(
        company_id=company_id,
        question=question,
        route="auto",
        answer="",
        context={"user_context": user_context} if user_context else {}
    )
    
    # Check if company has any data
    has_graph = load_graph(company_id) is not None
    faiss_store = FaissStore.load_or_create(user_id=company_id)
    has_vectors = faiss_store.index.ntotal > 0
    
    if not has_graph and not has_vectors:
        state = fallback_answer(state)
        return {
            "question": question,
            "answer": state.answer,
            "route": state.route,
            "company_id": company_id,
            "cached": False
        }
    
    # Use Adaptive RAG for intelligent routing
    try:
        from agents.adaptive_rag import get_query_analysis
        analysis = get_query_analysis(question)
        route = analysis.recommended_route
        
        # Store analysis in state context for potential use
        state.context["query_analysis"] = {
            "type": analysis.query_type.value,
            "confidence": analysis.confidence,
            "entities": analysis.entities,
            "time_refs": analysis.time_references
        }
        
        print(f"🎯 Adaptive routing: {route} (type={analysis.query_type.value}, conf={analysis.confidence:.2f})")
        
    except ImportError:
        # Fallback to basic routing
        route = route_question(question)
    except Exception as e:
        print(f"⚠️ Adaptive routing error: {e}, using basic router")
        route = route_question(question)
    
    state.route = route
    
    # Execute appropriate node (Graph-First Architecture)
    # Priority: graph > hybrid > rag
    if route == "graph":
        state = graph_answer(state)
    elif route == "hybrid":
        state = hybrid_answer(state)
    elif route == "rag":
        # For RAG, check if graph is available and use it as supplementary
        if has_graph:
            state = hybrid_answer(state)  # Use hybrid for better results
        else:
            state = rag_answer(state)
    else:
        state = graph_answer(state)  # Default to graph (graph-first)
    
    result = {
        "question": question,
        "answer": state.answer,
        "route": state.route,
        "company_id": company_id,
        "cached": False
    }
    
    # Cache the result
    if use_cache:
        try:
            from core.cache import get_cache
            cache = get_cache()
            cache.set(
                query=question,
                response=state.answer,
                route=state.route,
                sources=state.sources if hasattr(state, 'sources') else [],
                user_id=company_id
            )
        except Exception as e:
            print(f"⚠️ Cache save error: {e}")
    
    # Learn from query for personalization
    if use_memory:
        try:
            from core.memory import get_memory
            memory = get_memory()
            memory.learn_from_query(company_id, question, state.answer)
        except Exception as e:
            print(f"⚠️ Memory learn error: {e}")
    
    return result


def invalidate_user_cache(company_id: str):
    """
    Invalidate cache when user uploads new data
    
    Args:
        company_id: Company/user identifier
    """
    try:
        from core.cache import get_cache
        cache = get_cache()
        cache.invalidate_on_data_change(company_id)
    except Exception as e:
        print(f"⚠️ Cache invalidation error: {e}")

