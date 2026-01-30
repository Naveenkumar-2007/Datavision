"""
🗣️ NLP ENGINE - DataVision Natural Language Processing
=======================================================

Enterprise NLP capabilities:
- Named Entity Recognition (business entities)
- Intent Classification with confidence
- Sentiment Analysis for feedback data
- Keyword Extraction
- Text Summarization

FREE: Uses Groq/Gemini LLMs + local spaCy when available
"""

import re
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json

from core.llm import chat

logger = logging.getLogger(__name__)

# Try to import spaCy for better NER
SPACY_AVAILABLE = False
nlp = None
try:
    import spacy
    nlp = spacy.load("en_core_web_sm")
    SPACY_AVAILABLE = True
    logger.info("✅ spaCy loaded for NLP")
except:
    logger.info("⚠️ spaCy not available, using LLM-based NLP")


class EntityType(Enum):
    """Types of entities we care about in business data"""
    COMPANY = "company"
    PRODUCT = "product"
    PERSON = "person"
    METRIC = "metric"
    DATE = "date"
    MONEY = "money"
    PERCENTAGE = "percentage"
    QUANTITY = "quantity"
    LOCATION = "location"
    COLUMN = "column"  # Data column reference


@dataclass
class Entity:
    """An extracted entity"""
    text: str
    type: EntityType
    start: int
    end: int
    confidence: float = 1.0


@dataclass
class Sentiment:
    """Sentiment analysis result"""
    label: str  # positive, negative, neutral
    score: float  # -1 to 1
    confidence: float
    aspects: Dict[str, str] = field(default_factory=dict)  # aspect -> sentiment


@dataclass
class NLPResult:
    """Complete NLP analysis result"""
    original_text: str
    entities: List[Entity]
    sentiment: Optional[Sentiment]
    keywords: List[str]
    summary: Optional[str]
    processing_time_ms: int


class NLPEngine:
    """
    🗣️ DataVision NLP Engine
    
    Provides:
    - Entity extraction (companies, products, metrics, dates, etc.)
    - Sentiment analysis for feedback/reviews
    - Keyword extraction
    - Text summarization
    """
    
    def __init__(self):
        self.entity_patterns = self._build_entity_patterns()
    
    def _build_entity_patterns(self) -> Dict[EntityType, List[str]]:
        """Build regex patterns for entity extraction"""
        return {
            EntityType.MONEY: [
                r'\$[\d,]+\.?\d*',
                r'₹[\d,]+\.?\d*',
                r'€[\d,]+\.?\d*',
                r'£[\d,]+\.?\d*',
                r'\b\d+(?:,\d{3})*(?:\.\d+)?\s*(?:dollars?|USD|rupees?|INR|euros?|EUR)\b',
            ],
            EntityType.PERCENTAGE: [
                r'\b\d+(?:\.\d+)?%',
                r'\b\d+(?:\.\d+)?\s*percent\b',
            ],
            EntityType.DATE: [
                r'\b\d{4}-\d{2}-\d{2}\b',
                r'\b\d{2}/\d{2}/\d{4}\b',
                r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s*\d{4}\b',
                r'\bQ[1-4]\s*\d{4}\b',
                r'\b(?:last|next|this)\s+(?:week|month|year|quarter)\b',
            ],
            EntityType.QUANTITY: [
                r'\b\d+(?:,\d{3})*(?:\.\d+)?\s*(?:units?|items?|pieces?|orders?)\b',
            ],
        }
    
    async def analyze(
        self,
        text: str,
        extract_sentiment: bool = True,
        extract_keywords: bool = True,
        summarize: bool = False,
        max_summary_length: int = 150
    ) -> NLPResult:
        """
        Full NLP analysis of text
        
        Args:
            text: Text to analyze
            extract_sentiment: Whether to analyze sentiment
            extract_keywords: Whether to extract keywords
            summarize: Whether to generate summary
            max_summary_length: Max length of summary
            
        Returns:
            Complete NLP result
        """
        start_time = datetime.now()
        
        # 1. Extract entities
        entities = await self.extract_entities(text)
        
        # 2. Sentiment analysis
        sentiment = None
        if extract_sentiment:
            sentiment = await self.analyze_sentiment(text)
        
        # 3. Keyword extraction
        keywords = []
        if extract_keywords:
            keywords = await self.extract_keywords(text)
        
        # 4. Summarization
        summary = None
        if summarize and len(text) > max_summary_length * 2:
            summary = await self.summarize(text, max_summary_length)
        
        duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)
        
        return NLPResult(
            original_text=text,
            entities=entities,
            sentiment=sentiment,
            keywords=keywords,
            summary=summary,
            processing_time_ms=duration_ms
        )
    
    async def extract_entities(
        self, 
        text: str,
        data_columns: Optional[List[str]] = None
    ) -> List[Entity]:
        """Extract named entities from text"""
        entities = []
        
        # 1. Pattern-based extraction (fast, reliable)
        entities.extend(self._extract_pattern_entities(text))
        
        # 2. Extract column references if schema provided
        if data_columns:
            entities.extend(self._extract_column_references(text, data_columns))
        
        # 3. Use spaCy if available
        if SPACY_AVAILABLE and nlp:
            entities.extend(self._extract_spacy_entities(text))
        else:
            # Use LLM for complex entity extraction
            llm_entities = await self._extract_llm_entities(text)
            entities.extend(llm_entities)
        
        # Deduplicate and sort
        seen = set()
        unique_entities = []
        for e in sorted(entities, key=lambda x: x.start):
            key = (e.text.lower(), e.type)
            if key not in seen:
                seen.add(key)
                unique_entities.append(e)
        
        return unique_entities
    
    def _extract_pattern_entities(self, text: str) -> List[Entity]:
        """Extract entities using regex patterns"""
        entities = []
        
        for entity_type, patterns in self.entity_patterns.items():
            for pattern in patterns:
                for match in re.finditer(pattern, text, re.IGNORECASE):
                    entities.append(Entity(
                        text=match.group(),
                        type=entity_type,
                        start=match.start(),
                        end=match.end(),
                        confidence=0.9
                    ))
        
        return entities
    
    def _extract_column_references(
        self, 
        text: str, 
        columns: List[str]
    ) -> List[Entity]:
        """Extract references to data columns"""
        entities = []
        text_lower = text.lower()
        
        for col in columns:
            col_lower = col.lower()
            # Look for exact match or with underscores replaced
            patterns = [
                col_lower,
                col_lower.replace('_', ' '),
                col_lower.replace('_', ''),
            ]
            
            for pattern in patterns:
                idx = text_lower.find(pattern)
                if idx >= 0:
                    entities.append(Entity(
                        text=col,
                        type=EntityType.COLUMN,
                        start=idx,
                        end=idx + len(pattern),
                        confidence=0.95
                    ))
                    break
        
        return entities
    
    def _extract_spacy_entities(self, text: str) -> List[Entity]:
        """Extract entities using spaCy"""
        entities = []
        
        if not nlp:
            return entities
        
        doc = nlp(text)
        
        type_mapping = {
            'ORG': EntityType.COMPANY,
            'PRODUCT': EntityType.PRODUCT,
            'PERSON': EntityType.PERSON,
            'DATE': EntityType.DATE,
            'MONEY': EntityType.MONEY,
            'PERCENT': EntityType.PERCENTAGE,
            'QUANTITY': EntityType.QUANTITY,
            'GPE': EntityType.LOCATION,
            'LOC': EntityType.LOCATION,
        }
        
        for ent in doc.ents:
            if ent.label_ in type_mapping:
                entities.append(Entity(
                    text=ent.text,
                    type=type_mapping[ent.label_],
                    start=ent.start_char,
                    end=ent.end_char,
                    confidence=0.85
                ))
        
        return entities
    
    async def _extract_llm_entities(self, text: str) -> List[Entity]:
        """Extract entities using LLM"""
        entities = []
        
        if len(text) > 2000:
            text = text[:2000]
        
        prompt = f"""Extract named entities from this text. Return JSON array.

Text: "{text}"

Extract these types: COMPANY, PRODUCT, PERSON, METRIC, DATE

Format:
[{{"text": "entity text", "type": "ENTITY_TYPE"}}]

Return only the JSON array, nothing else."""

        try:
            response = chat(messages=prompt, temperature=0.1, max_tokens=500)
            
            # Parse JSON from response
            json_match = response[response.find('['):response.rfind(']')+1]
            if json_match:
                llm_entities = json.loads(json_match)
                for item in llm_entities:
                    entity_type = EntityType.COMPANY  # Default
                    type_str = item.get("type", "").upper()
                    type_map = {
                        'COMPANY': EntityType.COMPANY,
                        'PRODUCT': EntityType.PRODUCT,
                        'PERSON': EntityType.PERSON,
                        'METRIC': EntityType.METRIC,
                        'DATE': EntityType.DATE,
                    }
                    if type_str in type_map:
                        entity_type = type_map[type_str]
                    
                    text_val = item.get("text", "")
                    idx = text.find(text_val)
                    entities.append(Entity(
                        text=text_val,
                        type=entity_type,
                        start=idx if idx >= 0 else 0,
                        end=idx + len(text_val) if idx >= 0 else len(text_val),
                        confidence=0.75
                    ))
        except Exception as e:
            logger.warning(f"LLM entity extraction failed: {e}")
        
        return entities
    
    async def analyze_sentiment(
        self, 
        text: str,
        aspects: Optional[List[str]] = None
    ) -> Sentiment:
        """
        Analyze sentiment of text
        
        Args:
            text: Text to analyze
            aspects: Optional specific aspects to analyze (e.g., ['price', 'quality'])
            
        Returns:
            Sentiment analysis result
        """
        if len(text) > 1000:
            text = text[:1000]
        
        prompt = f"""Analyze the sentiment of this text.

Text: "{text}"

Provide:
1. Overall sentiment: positive, negative, or neutral
2. Score: -1.0 (very negative) to 1.0 (very positive)
3. Confidence: 0.0 to 1.0

Format your response exactly as:
SENTIMENT: [positive/negative/neutral]
SCORE: [number]
CONFIDENCE: [number]"""

        try:
            response = chat(messages=prompt, temperature=0.1, max_tokens=100)
            
            sentiment_match = re.search(r'SENTIMENT:\s*(\w+)', response, re.IGNORECASE)
            score_match = re.search(r'SCORE:\s*([-\d.]+)', response, re.IGNORECASE)
            conf_match = re.search(r'CONFIDENCE:\s*([\d.]+)', response, re.IGNORECASE)
            
            label = sentiment_match.group(1).lower() if sentiment_match else "neutral"
            score = float(score_match.group(1)) if score_match else 0.0
            confidence = float(conf_match.group(1)) if conf_match else 0.7
            
            # Clamp values
            score = max(-1.0, min(1.0, score))
            confidence = max(0.0, min(1.0, confidence))
            
            return Sentiment(
                label=label,
                score=score,
                confidence=confidence,
                aspects={}
            )
            
        except Exception as e:
            logger.warning(f"Sentiment analysis failed: {e}")
            return Sentiment(label="neutral", score=0.0, confidence=0.5)
    
    async def extract_keywords(
        self, 
        text: str, 
        max_keywords: int = 10
    ) -> List[str]:
        """Extract important keywords from text"""
        if len(text) > 1000:
            text = text[:1000]
        
        prompt = f"""Extract the {max_keywords} most important keywords from this text.

Text: "{text}"

Return only a comma-separated list of keywords, nothing else."""

        try:
            response = chat(messages=prompt, temperature=0.1, max_tokens=100)
            
            # Parse comma-separated keywords
            keywords = [k.strip() for k in response.split(',')]
            return [k for k in keywords if k and len(k) > 2][:max_keywords]
            
        except Exception as e:
            logger.warning(f"Keyword extraction failed: {e}")
            return []
    
    async def summarize(
        self, 
        text: str, 
        max_length: int = 150
    ) -> str:
        """Summarize long text"""
        if len(text) <= max_length:
            return text
        
        prompt = f"""Summarize this text in {max_length} characters or less. Be concise but capture key points.

Text: "{text[:3000]}"

Summary:"""

        try:
            response = chat(messages=prompt, temperature=0.3, max_tokens=200)
            return response.strip()[:max_length*2]  # Allow some flexibility
            
        except Exception as e:
            logger.warning(f"Summarization failed: {e}")
            return text[:max_length] + "..."
    
    async def analyze_reviews(
        self, 
        reviews: List[str]
    ) -> Dict[str, Any]:
        """
        Analyze a batch of reviews/feedback
        
        Returns aggregate sentiment, common themes, and issues
        """
        sentiments = []
        all_keywords = []
        
        for review in reviews[:50]:  # Limit to 50 reviews
            sentiment = await self.analyze_sentiment(review)
            sentiments.append(sentiment)
            
            keywords = await self.extract_keywords(review, max_keywords=5)
            all_keywords.extend(keywords)
        
        # Aggregate results
        avg_score = sum(s.score for s in sentiments) / len(sentiments) if sentiments else 0
        
        positive_count = sum(1 for s in sentiments if s.label == "positive")
        negative_count = sum(1 for s in sentiments if s.label == "negative")
        neutral_count = sum(1 for s in sentiments if s.label == "neutral")
        
        # Count keyword frequency
        keyword_freq = {}
        for kw in all_keywords:
            kw_lower = kw.lower()
            keyword_freq[kw_lower] = keyword_freq.get(kw_lower, 0) + 1
        
        top_keywords = sorted(keyword_freq.items(), key=lambda x: x[1], reverse=True)[:10]
        
        return {
            "total_reviews": len(reviews),
            "analyzed": len(sentiments),
            "average_sentiment_score": round(avg_score, 2),
            "sentiment_distribution": {
                "positive": positive_count,
                "negative": negative_count,
                "neutral": neutral_count
            },
            "top_keywords": [{"keyword": k, "count": c} for k, c in top_keywords],
            "overall_label": "positive" if avg_score > 0.2 else "negative" if avg_score < -0.2 else "neutral"
        }


# Global instance
_nlp_engine: Optional[NLPEngine] = None


def get_nlp_engine() -> NLPEngine:
    """Get or create the global NLP engine"""
    global _nlp_engine
    if _nlp_engine is None:
        _nlp_engine = NLPEngine()
    return _nlp_engine


async def extract_entities(
    text: str, 
    data_columns: Optional[List[str]] = None
) -> List[Dict]:
    """Quick function to extract entities"""
    engine = get_nlp_engine()
    entities = await engine.extract_entities(text, data_columns)
    return [
        {"text": e.text, "type": e.type.value, "confidence": e.confidence}
        for e in entities
    ]


async def analyze_sentiment(text: str) -> Dict:
    """Quick function for sentiment analysis"""
    engine = get_nlp_engine()
    result = await engine.analyze_sentiment(text)
    return {
        "label": result.label,
        "score": result.score,
        "confidence": result.confidence
    }
