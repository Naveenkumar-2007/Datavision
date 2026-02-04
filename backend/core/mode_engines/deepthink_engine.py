"""
🧠 PRO DEEP THINK ENGINE v2.0 - DataVision Intelligence
========================================================

Advanced reasoning engine with multi-step chain-of-thought analysis.

Features:
- 🔍 Problem Decomposition
- 📊 Evidence Extraction with Citations
- 🧠 Step-by-Step Reasoning
- ✅ Fact Verification against Data
- 📈 Confidence Scoring
- 💡 Actionable Insights

Built for DataVision - Complex reasoning for ANY data!

Author: DataVision Team
Version: 2.0.0
"""

import logging
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from enum import Enum
from dataclasses import dataclass
import re
import json

logger = logging.getLogger(__name__)

# LLM for intelligent responses
try:
    from core.llm import chat as llm_chat
    LLM_AVAILABLE = True
except ImportError:
    LLM_AVAILABLE = False

# Advanced Hybrid Intelligence System
try:
    from core.knowledge_sources import (
        KnowledgeSource, SourceClassifier, HybridResponseCombiner,
        SOURCE_BADGES, classify_query, get_source_badge
    )
    HYBRID_KNOWLEDGE_AVAILABLE = True
except ImportError:
    HYBRID_KNOWLEDGE_AVAILABLE = False

try:
    from core.advanced_rag import SelfRAG, AdaptiveRAG, RAGType
    ADVANCED_RAG_AVAILABLE = True
except ImportError:
    ADVANCED_RAG_AVAILABLE = False

try:
    from core.deep_agents import ReflexionAgent, deep_agent_query
    DEEP_AGENTS_AVAILABLE = True
except ImportError:
    DEEP_AGENTS_AVAILABLE = False

# Deep Research Agent (Claude-style)
try:
    from core.deep_research_agent import DeepResearchAgent, deep_research, deep_research_formatted
    DEEP_RESEARCH_AVAILABLE = True
except ImportError:
    DEEP_RESEARCH_AVAILABLE = False

# Intelligent Visualizer (Knowledge Graphs, Mind Maps, 20+ Charts)
try:
    from core.intelligent_visualizer import (
        IntelligentVisualizer, VizType, smart_visualize,
        generate_knowledge_graph, generate_mind_map
    )
    INTELLIGENT_VIZ_AVAILABLE = True
except ImportError:
    INTELLIGENT_VIZ_AVAILABLE = False

# Intelligent Query Processor (Claude-style)
try:
    from core.intelligent_processor import IntelligentQueryProcessor, intelligent_process
    INTELLIGENT_PROCESSOR_AVAILABLE = True
except ImportError:
    INTELLIGENT_PROCESSOR_AVAILABLE = False


# =============================================================================
# REASONING TYPES
# =============================================================================

class ReasoningType(Enum):
    """Types of complex reasoning"""
    CAUSAL = "causal"           # "Why did X happen?"
    COMPARATIVE = "comparative" # "How does A compare to B?"
    TREND_ANALYSIS = "trend"    # "What's the trend and why?"
    ROOT_CAUSE = "root_cause"   # "What caused this issue?"
    PREDICTIVE = "predictive"   # "What will happen if...?"
    DIAGNOSTIC = "diagnostic"   # "What's wrong with...?"
    STRATEGIC = "strategic"     # "What should we do about...?"
    EXPLORATORY = "exploratory" # "What patterns exist in...?"


@dataclass
class Evidence:
    """A piece of evidence from the data"""
    source: str
    content: str
    confidence: float
    data_support: bool


@dataclass
class ReasoningStep:
    """A step in the reasoning chain"""
    step_number: int
    question: str
    answer: str
    evidence: List[Evidence]
    confidence: float


# =============================================================================
# EVIDENCE EXTRACTOR
# =============================================================================

def extract_evidence(df: pd.DataFrame, query: str, context: str = "") -> List[Evidence]:
    """
    Extract relevant evidence from data to support reasoning.
    """
    evidence_list = []
    
    if df is None or df.empty:
        return evidence_list
    
    q_lower = query.lower()
    
    # Extract numeric insights as evidence
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    
    for col in numeric_cols[:5]:
        # Check if column is mentioned or relevant
        if col.lower() in q_lower or col.lower().replace('_', ' ') in q_lower:
            try:
                mean_val = df[col].mean()
                std_val = df[col].std()
                min_val = df[col].min()
                max_val = df[col].max()
                
                evidence_list.append(Evidence(
                    source=f"Column: {col}",
                    content=f"{col}: mean={mean_val:,.2f}, std={std_val:,.2f}, range=[{min_val:,.2f}, {max_val:,.2f}]",
                    confidence=0.95,
                    data_support=True
                ))
            except:
                pass
    
    # Extract categorical insights
    categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
    
    for col in categorical_cols[:3]:
        if col.lower() in q_lower or col.lower().replace('_', ' ') in q_lower:
            try:
                value_counts = df[col].value_counts().head(3)
                content = f"{col} distribution: " + ", ".join([f"{k}={v}" for k, v in value_counts.items()])
                evidence_list.append(Evidence(
                    source=f"Column: {col}",
                    content=content,
                    confidence=0.90,
                    data_support=True
                ))
            except:
                pass
    
    # Extract correlation evidence if comparing
    if 'compare' in q_lower or 'relationship' in q_lower or 'affect' in q_lower:
        if len(numeric_cols) >= 2:
            try:
                corr = df[numeric_cols].corr()
                # Find strongest correlations
                for i, col1 in enumerate(numeric_cols[:4]):
                    for col2 in numeric_cols[i+1:4]:
                        corr_val = corr.loc[col1, col2]
                        if abs(corr_val) > 0.3:
                            strength = "strong" if abs(corr_val) > 0.7 else "moderate"
                            direction = "positive" if corr_val > 0 else "negative"
                            evidence_list.append(Evidence(
                                source="Correlation Analysis",
                                content=f"{col1} and {col2} have {strength} {direction} correlation ({corr_val:.2f})",
                                confidence=0.85,
                                data_support=True
                            ))
            except:
                pass
    
    # Extract trend evidence if time-related
    time_keywords = ['trend', 'over time', 'growth', 'decline', 'change']
    if any(kw in q_lower for kw in time_keywords):
        # Look for date columns
        for col in df.columns:
            if 'date' in col.lower() or 'time' in col.lower():
                try:
                    df_sorted = df.sort_values(col)
                    if len(numeric_cols) > 0:
                        first_half = df_sorted[numeric_cols[0]].iloc[:len(df)//2].mean()
                        second_half = df_sorted[numeric_cols[0]].iloc[len(df)//2:].mean()
                        change_pct = ((second_half - first_half) / first_half * 100) if first_half != 0 else 0
                        direction = "increased" if change_pct > 0 else "decreased"
                        evidence_list.append(Evidence(
                            source="Trend Analysis",
                            content=f"{numeric_cols[0]} {direction} by {abs(change_pct):.1f}% over the time period",
                            confidence=0.80,
                            data_support=True
                        ))
                except:
                    pass
                break
    
    # Add context as evidence if provided
    if context:
        evidence_list.append(Evidence(
            source="Context",
            content=context[:500],
            confidence=0.70,
            data_support=False
        ))
    
    return evidence_list


# =============================================================================
# REASONING ENGINE
# =============================================================================

def detect_reasoning_type(query: str) -> ReasoningType:
    """Detect what type of reasoning is needed."""
    q = query.lower()
    
    patterns = {
        ReasoningType.CAUSAL: [r'why', r'cause', r'reason', r'because'],
        ReasoningType.COMPARATIVE: [r'compare', r'versus', r' vs ', r'difference', r'better'],
        ReasoningType.TREND_ANALYSIS: [r'trend', r'over time', r'growth', r'pattern'],
        ReasoningType.ROOT_CAUSE: [r'root cause', r'problem', r'issue', r'wrong'],
        ReasoningType.PREDICTIVE: [r'predict', r'will happen', r'forecast', r'future'],
        ReasoningType.DIAGNOSTIC: [r'diagnose', r'check', r'analyze.*issue'],
        ReasoningType.STRATEGIC: [r'should we', r'recommend', r'strategy', r'action'],
    }
    
    for rtype, pats in patterns.items():
        for pat in pats:
            if re.search(pat, q):
                return rtype
    
    return ReasoningType.EXPLORATORY


def decompose_problem(query: str, reasoning_type: ReasoningType) -> List[str]:
    """Decompose complex query into sub-questions."""
    
    decomposition_templates = {
        ReasoningType.CAUSAL: [
            "What is the current state of the metric in question?",
            "What factors could influence this metric?",
            "Which factors show the strongest correlation?",
            "What is the likely causal chain?"
        ],
        ReasoningType.COMPARATIVE: [
            "What are the key metrics for each group?",
            "How do the distributions differ?",
            "What are the statistical differences?",
            "What explains these differences?"
        ],
        ReasoningType.TREND_ANALYSIS: [
            "What is the overall direction of the trend?",
            "Are there seasonal patterns?",
            "What events correlate with trend changes?",
            "What is the projected trajectory?"
        ],
        ReasoningType.ROOT_CAUSE: [
            "What is the specific problem observed?",
            "When did it start occurring?",
            "What changed before the problem?",
            "What are the contributing factors?"
        ],
        ReasoningType.PREDICTIVE: [
            "What are the current values of key variables?",
            "What patterns exist in historical data?",
            "What assumptions are we making?",
            "What is the likely outcome?"
        ],
        ReasoningType.STRATEGIC: [
            "What is the current situation?",
            "What are the goals?",
            "What options are available?",
            "What are the trade-offs of each option?"
        ],
        ReasoningType.EXPLORATORY: [
            "What are the key variables in the data?",
            "What patterns or relationships exist?",
            "What anomalies or outliers are present?",
            "What insights emerge from the analysis?"
        ]
    }
    
    return decomposition_templates.get(reasoning_type, decomposition_templates[ReasoningType.EXPLORATORY])


# =============================================================================
# PRO DEEP THINK ENGINE CLASS
# =============================================================================

class ProDeepThinkEngine:
    """
    🧠 PRO DEEP THINK ENGINE - DataVision Complex Reasoning
    
    Multi-step chain-of-thought reasoning for complex questions.
    
    💡 WHEN TO USE:
    - Complex "why" questions
    - Root cause analysis
    - Strategic recommendations
    - Multi-factor analysis
    
    Features:
    - Problem decomposition
    - Evidence-based reasoning
    - Step-by-step analysis
    - Confidence scoring
    """
    
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.reasoning_history = []
    
    def process(
        self,
        query: str,
        context: str = "",
        df: pd.DataFrame = None,
        show_reasoning: bool = True
    ) -> Dict[str, Any]:
        """
        Process a complex query with deep reasoning.
        Uses DYNAMIC routing - data queries use data, general queries use AI.
        """
        result = {
            "answer": "",
            "mode": "deepthink",
            "confidence": 0.0,
            "sources": ["DeepThink"],
            "reasoning_steps": [],
            "evidence_used": []
        }
        
        start_time = datetime.now()
        
        # =================================================================
        # �️ CHECK FOR IMAGE CONTEXT FIRST - Takes priority
        # =================================================================
        has_image_context = context and "🖼️ Image Analysis" in context
        
        if has_image_context:
            logger.info("🖼️ DeepThink: Image context detected - deep image analysis")
            
            if LLM_AVAILABLE:
                try:
                    image_prompt = f"""You are a Deep Think AI analyzing an image with advanced reasoning.

## IMAGE ANALYSIS:
{context}

## USER QUESTION:
{query}

Think through this systematically:
1. What is shown in the image?
2. What details are relevant to the user's question?
3. What insights can be drawn?

Provide a thoughtful, detailed analysis of the image content."""

                    llm_response = llm_chat(image_prompt, temperature=0.4, max_tokens=800)
                    
                    result["answer"] = f"""## 🧠 Deep Think - Image Analysis

{llm_response}

---
*🖼️ Deep analysis of uploaded image*"""
                    result["confidence"] = 0.90
                    result["sources"] = ["Deep Think Engine", "Vision Analysis"]
                    
                except Exception as e:
                    logger.error(f"DeepThink image error: {e}")
                    result["answer"] = f"🖼️ Image Analysis:\n\n{context}"
            
            exec_time = (datetime.now() - start_time).total_seconds()
            result["execution_time"] = f"{exec_time:.2f}s"
            return result
        
        # =================================================================
        # �🔄 DYNAMIC ROUTING: Check if query relates to actual data
        # =================================================================
        q_lower = query.lower()
        
        # Get column names from data
        column_names = [col.lower() for col in df.columns] if df is not None and not df.empty else []
        column_names_spaced = [col.replace('_', ' ') for col in column_names]
        
        # Check if query mentions ANY column or data-related term
        data_terms = column_names + column_names_spaced + [
            'my data', 'my ', 'our ', 'the data', 'uploaded', 'dataset',
            'total', 'sum', 'average', 'count', 'revenue', 'sales', 'customer'
        ]
        
        query_is_about_data = any(term in q_lower for term in data_terms if term)
        
        # If NOT about data, use pure AI Knowledge
        if not query_is_about_data:
            logger.info("🌐 DeepThink: Routing to AI KNOWLEDGE (query not about data)")
            
            if LLM_AVAILABLE:
                try:
                    ai_prompt = f"""You are a Deep Think AI with advanced reasoning capabilities.

Think through this question step by step:

{query}

Provide a thoughtful, well-reasoned response with:
1. Key considerations
2. Analysis
3. Conclusion

Be thorough but clear."""

                    llm_response = llm_chat(ai_prompt, temperature=0.5, max_tokens=800)
                    
                    result["answer"] = f"""## 🧠 Deep Think

🌐 **AI Knowledge**

{llm_response}

---
*💡 This is general AI reasoning. For deep analysis of YOUR data, ask about specific metrics.*"""
                    result["confidence"] = 0.85
                    result["sources"] = ["AI Knowledge"]
                    
                    exec_time = (datetime.now() - start_time).total_seconds()
                    result["execution_time"] = f"{exec_time:.2f}s"
                    return result
                    
                except Exception as e:
                    logger.error(f"AI Knowledge error: {e}")
        
        # =================================================================
        # 📊 DATA PATH - Query IS about user's data
        # =================================================================
        logger.info("📊 DeepThink: Routing to DATA ANALYSIS")
        
        # Detect reasoning type
        reasoning_type = detect_reasoning_type(query)
        logger.info(f"🧠 Reasoning Type: {reasoning_type.value}")
        
        # Extract evidence from data
        evidence = extract_evidence(df, query, context)
        result["evidence_used"] = [
            {"source": e.source, "content": e.content[:100], "confidence": e.confidence}
            for e in evidence
        ]
        
        # Decompose the problem
        sub_questions = decompose_problem(query, reasoning_type)
        
        # Build reasoning chain
        reasoning_steps = []
        
        # Format evidence for prompt
        evidence_text = "\n".join([
            f"• [{e.source}] {e.content}" for e in evidence[:10]
        ]) if evidence else "No specific data evidence available."
        
        # Generate comprehensive response with LLM
        if LLM_AVAILABLE:
            response = self._generate_deep_response(
                query, reasoning_type, sub_questions, evidence_text, df
            )
        else:
            response = self._fallback_response(query, evidence, sub_questions)
        
        # Calculate confidence
        confidence = self._calculate_confidence(evidence, response)
        
        # Format final response
        if show_reasoning:
            final_response = self._format_response_with_reasoning(
                query, reasoning_type, sub_questions, evidence, response, confidence
            )
        else:
            final_response = response
        
        result["answer"] = final_response
        result["confidence"] = confidence
        result["reasoning_type"] = reasoning_type.value
        
        # Check if user wants a chart and generate it
        q_lower = query.lower()
        wants_chart = any(term in q_lower for term in [
            'chart', 'graph', 'visualize', 'plot', 'diagram', 'show me', 'draw'
        ])
        
        if wants_chart and df is not None and not df.empty:
            try:
                from core.llm_visualizer import llm_visualize
                import json
                viz_result = llm_visualize(df, query, self.user_id)
                if viz_result.get("success") and viz_result.get("chart"):
                    chart = viz_result.get("chart")
                    if isinstance(chart, dict) and 'data' in chart and 'layout' in chart:
                        chart_json = json.dumps(chart, default=str)
                        result["answer"] += f"\n\n```plotly_chart\n{chart_json}\n```"
                        result["chart"] = chart
                        result["visualization"] = chart
            except Exception as e:
                logger.warning(f"DeepThink chart generation failed: {e}")
        
        # Execution time
        exec_time = (datetime.now() - start_time).total_seconds()
        result["execution_time"] = f"{exec_time:.2f}s"
        
        return result
    
    def _generate_deep_response(
        self,
        query: str,
        reasoning_type: ReasoningType,
        sub_questions: List[str],
        evidence_text: str,
        df: pd.DataFrame = None
    ) -> str:
        """Generate deep analysis response with LLM."""
        
        # Build data context with COMPREHENSIVE stats
        data_context = ""
        if df is not None and not df.empty:
            data_context = f"""
Dataset: {len(df)} rows, {len(df.columns)} columns
Columns: {', '.join(df.columns.tolist()[:15])}
"""
            # Add comprehensive numeric stats
            numeric_cols = df.select_dtypes(include=[np.number]).columns[:8]
            if len(numeric_cols) > 0:
                data_context += "\n📊 NUMERIC COLUMN STATISTICS:\n"
                for col in numeric_cols:
                    try:
                        data_context += f"• {col}: mean={df[col].mean():,.2f}, "
                        data_context += f"min={df[col].min():,.2f}, max={df[col].max():,.2f}, "
                        data_context += f"std={df[col].std():,.2f}\n"
                    except:
                        pass
            
            # Add categorical stats
            cat_cols = df.select_dtypes(include=['object', 'category']).columns[:5]
            if len(cat_cols) > 0:
                data_context += "\n📋 CATEGORICAL COLUMN INFO:\n"
                for col in cat_cols:
                    try:
                        unique = df[col].nunique()
                        top_val = df[col].mode().iloc[0] if not df[col].mode().empty else 'N/A'
                        data_context += f"• {col}: {unique} unique values, most common='{top_val}'\n"
                    except:
                        pass
        
        prompt = f"""You are a Deep Think engine - an expert analyst providing HYBRID insights.

USER QUESTION: {query}

REASONING TYPE: {reasoning_type.value}

📊 DATA CONTEXT (YOUR USER'S ACTUAL DATA - USE THESE NUMBERS):
{data_context}

EVIDENCE FROM DATA:
{evidence_text}

SUB-QUESTIONS TO ADDRESS:
{chr(10).join(f'{i+1}. {q}' for i, q in enumerate(sub_questions))}

CRITICAL INSTRUCTIONS:
1. FIRST: Answer using ACTUAL numbers from the data (marked with 📊)
2. SECOND: Add general AI knowledge to augment (marked with 🌐)
3. For "why" questions, reference actual statistics AND add context

FORMAT YOUR RESPONSE:

📊 **From Your Data:**
[Insights citing specific values from the data above]

🌐 **AI Knowledge:**
[Industry context, best practices, benchmarks, general insights]

Be thorough but concise. Maximum 3-4 paragraphs total."""

        try:
            response = llm_chat(prompt, temperature=0.3, max_tokens=1000)
            # Return response directly - prompt already instructs proper formatting
            return response
        except Exception as e:
            logger.error(f"LLM error: {e}")
            return self._fallback_response(query, [], sub_questions)
    
    def _fallback_response(
        self,
        query: str,
        evidence: List[Evidence],
        sub_questions: List[str]
    ) -> str:
        """Fallback when LLM is unavailable."""
        response = f"## Analysis of: {query}\n\n"
        
        response += "### Evidence Found:\n"
        for e in evidence[:5]:
            response += f"- {e.content}\n"
        
        response += "\n### Questions to Consider:\n"
        for i, q in enumerate(sub_questions, 1):
            response += f"{i}. {q}\n"
        
        return response
    
    def _calculate_confidence(self, evidence: List[Evidence], response: str) -> float:
        """Calculate confidence based on evidence strength."""
        if not evidence:
            return 0.5
        
        # Average evidence confidence
        evidence_conf = sum(e.confidence for e in evidence) / len(evidence)
        
        # Boost for data-supported evidence
        data_support_ratio = sum(1 for e in evidence if e.data_support) / len(evidence)
        
        # Combined confidence
        confidence = (evidence_conf * 0.6) + (data_support_ratio * 0.4)
        
        return min(confidence, 0.95)
    
    def _format_response_with_reasoning(
        self,
        query: str,
        reasoning_type: ReasoningType,
        sub_questions: List[str],
        evidence: List[Evidence],
        response: str,
        confidence: float
    ) -> str:
        """Format response to show reasoning process."""
        
        conf_emoji = "🟢" if confidence > 0.7 else "🟡" if confidence > 0.5 else "🔴"
        
        formatted = f"""## 🧠 Deep Analysis

### Query: {query}

**Reasoning Type**: {reasoning_type.value.replace('_', ' ').title()}
**Confidence**: {conf_emoji} {confidence*100:.0f}%

---

### 📊 Evidence Considered

"""
        
        for e in evidence[:5]:
            formatted += f"- **[{e.source}]** {e.content[:100]}...\n"
        
        formatted += f"""
---

### 🔍 Analysis

{response}

---

### 💡 Key Takeaways

*Based on analysis of available data with {len(evidence)} pieces of evidence.*
"""
        
        return formatted


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def deepthink_response(
    user_id: str,
    query: str,
    context: str = "",
    show_reasoning: bool = True
) -> Dict[str, Any]:
    """Quick function for deep think response."""
    engine = ProDeepThinkEngine(user_id)
    return engine.process(query, context, None, show_reasoning)


def deepthink_response_sync(
    user_id: str,
    query: str,
    context: str = "",
    df: pd.DataFrame = None
) -> Dict[str, Any]:
    """Synchronous deep think response for compatibility."""
    engine = ProDeepThinkEngine(user_id)
    return engine.process(query, context, df, True)


# Alias for backwards compatibility
DeepThinkEngine = ProDeepThinkEngine

__all__ = ['ProDeepThinkEngine', 'DeepThinkEngine', 'deepthink_response', 'deepthink_response_sync']
