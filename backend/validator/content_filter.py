"""
MetaPilot AI - Content Filter

Filters AI responses for inappropriate or unwanted content.
"""

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union, Set
import re

logger = logging.getLogger(__name__)


class ContentCategory(Enum):
    """Categories of content to filter."""
    PROFANITY = "profanity"
    HATE_SPEECH = "hate_speech"
    VIOLENCE = "violence"
    SEXUAL = "sexual"
    PERSONAL_INFO = "personal_info"
    SPAM = "spam"
    ILLEGAL = "illegal"
    MISINFORMATION = "misinformation"
    HARMFUL = "harmful"
    SELF_HARM = "self_harm"


class FilterAction(Enum):
    """Actions to take when content is flagged."""
    BLOCK = "block"  # Completely block the content
    WARNING = "warning"  # Allow with warning
    ALLOW = "allow"  # Allow without warning
    REDACT = "redact"  # Redact the problematic parts


@dataclass
class FilterResult:
    """Result of content filtering."""
    is_clean: bool
    categories: Dict[ContentCategory, float] = field(default_factory=dict)
    action: FilterAction = FilterAction.ALLOW
    warnings: List[str] = field(default_factory=list)
    redacted_content: Optional[str] = None
    confidence: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_clean": self.is_clean,
            "categories": {k.value: v for k, v in self.categories.items()},
            "action": self.action.value,
            "warnings": self.warnings,
            "confidence": self.confidence
        }


@dataclass
class FilterRule:
    """A filtering rule."""
    category: ContentCategory
    patterns: List[str]
    action: FilterAction = FilterAction.BLOCK
    confidence: float = 1.0
    description: str = ""


class ContentFilter:
    """
    Filters AI responses for inappropriate or unwanted content.
    
    Uses pattern matching and keyword lists to detect and handle
    problematic content.
    """
    
    def __init__(self, 
                 rules: Optional[List[FilterRule]] = None,
                 default_action: FilterAction = FilterAction.BLOCK,
                 enable_redaction: bool = True,
                 custom_blocklists: Optional[Dict[ContentCategory, List[str]]] = None):
        """
        Initialize the content filter.
        
        Args:
            rules: List of custom filter rules
            default_action: Default action for flagged content
            enable_redaction: Whether to enable content redaction
            custom_blocklists: Custom blocklists for each category
        """
        self.default_action = default_action
        self.enable_redaction = enable_redaction
        self.custom_blocklists = custom_blocklists or {}
        
        # Initialize default rules
        self.rules: List[FilterRule] = rules or []
        self._initialize_default_rules()
        
        # Add custom rules
        if rules:
            self.rules.extend(rules)
    
    def _initialize_default_rules(self):
        """Initialize default filtering rules."""
        # Profanity
        profanity_words = [
            # Common profanity (this is a simplified list)
            "fuck", "shit", "asshole", "bitch", "bastard", "damn",
            "cunt", "dick", "pussy", "cock", "whore", "slut",
            "motherfucker", "bullshit", "crap"
        ]
        self.rules.append(FilterRule(
            category=ContentCategory.PROFANITY,
            patterns=profanity_words,
            action=FilterAction.BLOCK,
            confidence=0.9,
            description="Profanity detected"
        ))
        
        # Hate speech
        hate_speech_terms = [
            "nigger", "kike", "spic", "chink", "gook", "faggot",
            "dyke", "tranny", "retard", "cunt", "slut", "whore"
        ]
        self.rules.append(FilterRule(
            category=ContentCategory.HATE_SPEECH,
            patterns=hate_speech_terms,
            action=FilterAction.BLOCK,
            confidence=1.0,
            description="Hate speech detected"
        ))
        
        # Violence
        violence_terms = [
            "kill", "murder", "rape", "bomb", "shoot", "stab",
            "torture", "beat", "attack", "terror", "war",
            "destroy", "annihilate", "exterminate"
        ]
        self.rules.append(FilterRule(
            category=ContentCategory.VIOLENCE,
            patterns=violence_terms,
            action=FilterAction.WARNING,
            confidence=0.8,
            description="Violent content detected"
        ))
        
        # Sexual content
        sexual_terms = [
            "sex", "fuck", "porn", "erotic", "orgasm", "masturbate",
            "blowjob", "fellatio", "cunnilingus", "intercourse",
            "arousal", "turn on", "horny", "lust"
        ]
        self.rules.append(FilterRule(
            category=ContentCategory.SEXUAL,
            patterns=sexual_terms,
            action=FilterAction.WARNING,
            confidence=0.7,
            description="Sexual content detected"
        ))
        
        # Personal information patterns
        pi_patterns = [
            r"\d{3}-\d{2}-\d{4}",  # SSN
            r"\d{16}",  # Credit card number
            r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",  # Email
            r"\d{10}",  # Phone number
            r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}"  # IP address
        ]
        self.rules.append(FilterRule(
            category=ContentCategory.PERSONAL_INFO,
            patterns=pi_patterns,
            action=FilterAction.REDACT,
            confidence=0.9,
            description="Personal information detected"
        ))
        
        # Spam patterns
        spam_patterns = [
            r"http[s]?://",  # URLs
            r"www\.",  # Web addresses
            r"@\w+",  # Mentions
            r"#\w+",  # Hashtags
            r"click here",
            r"visit our site",
            r"buy now",
            r"limited time"
        ]
        self.rules.append(FilterRule(
            category=ContentCategory.SPAM,
            patterns=spam_patterns,
            action=FilterAction.WARNING,
            confidence=0.6,
            description="Spam content detected"
        ))
        
        # Add custom blocklists
        for category, terms in self.custom_blocklists.items():
            try:
                category_enum = ContentCategory(category)
                self.rules.append(FilterRule(
                    category=category_enum,
                    patterns=terms,
                    action=FilterAction.BLOCK,
                    confidence=0.9
                ))
            except ValueError:
                logger.warning(f"Unknown content category: {category}")
    
    def filter(self, 
               content: str,
               response: Optional[Dict[str, Any]] = None) -> FilterResult:
        """
        Filter content for inappropriate material.
        
        Args:
            content: The content to filter
            response: Optional full response (for additional context)
        
        Returns:
            FilterResult with filtering details
        """
        categories: Dict[ContentCategory, float] = {}
        warnings: List[str] = []
        highest_action = FilterAction.ALLOW
        redacted_content = content
        
        for rule in self.rules:
            # Check if content matches any pattern in this rule
            matched = False
            confidence = 0.0
            
            for pattern in rule.patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    matched = True
                    confidence = max(confidence, rule.confidence)
                    break
            
            if matched:
                # Update category score
                categories[rule.category] = max(
                    categories.get(rule.category, 0),
                    confidence
                )
                
                # Update highest action
                action_priority = {
                    FilterAction.BLOCK: 3,
                    FilterAction.REDACT: 2,
                    FilterAction.WARNING: 1,
                    FilterAction.ALLOW: 0
                }
                
                if action_priority.get(rule.action, 0) > action_priority.get(highest_action, 0):
                    highest_action = rule.action
                
                # Add warning
                if rule.action != FilterAction.BLOCK:
                    warnings.append(rule.description)
        
        # Redact if needed
        if highest_action == FilterAction.REDACT and self.enable_redaction:
            redacted_content = self._redact_content(content, categories)
        
        # Determine if content is clean
        is_clean = highest_action == FilterAction.ALLOW
        
        # Calculate overall confidence
        confidence = max(categories.values()) if categories else 0.0
        
        return FilterResult(
            is_clean=is_clean,
            categories=categories,
            action=highest_action,
            warnings=warnings,
            redacted_content=redacted_content if redacted_content != content else None,
            confidence=confidence
        )
    
    def _redact_content(self, content: str, categories: Dict[ContentCategory, float]) -> str:
        """Redact sensitive content."""
        redacted = content
        
        # Redact personal information
        pi_patterns = [
            (r"\d{3}-\d{2}-\d{4}", "[SSN REDACTED]"),
            (r"\d{4}-\d{4}-\d{4}-\d{4}", "[CC REDACTED]"),
            (r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", "[EMAIL REDACTED]"),
            (r"\d{3}-\d{3}-\d{4}", "[PHONE REDACTED]"),
            (r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}", "[IP REDACTED]")
        ]
        
        for pattern, replacement in pi_patterns:
            redacted = re.sub(pattern, replacement, redacted)
        
        # Redact profanity
        profanity_words = [
            "fuck", "shit", "asshole", "bitch", "bastard", "damn",
            "cunt", "dick", "pussy", "cock", "whore", "slut"
        ]
        
        for word in profanity_words:
            # Case-insensitive replacement
            redacted = re.sub(f"\b{word}\b", "[REDACTED]", redacted, flags=re.IGNORECASE)
        
        return redacted
    
    def filter_batch(self, 
                     contents: List[str],
                     responses: Optional[List[Dict[str, Any]]] = None) -> List[FilterResult]:
        """
        Filter multiple contents.
        
        Args:
            contents: List of contents to filter
            responses: Optional list of full responses
        
        Returns:
            List of FilterResult objects
        """
        responses = responses or [{}] * len(contents)
        return [self.filter(content, responses[i]) for i, content in enumerate(contents)]
    
    def is_clean(self, content: str) -> bool:
        """
        Quick check if content is clean.
        
        Args:
            content: The content to check
        
        Returns:
            True if content passes all filters
        """
        result = self.filter(content)
        return result.is_clean
    
    def add_rule(self, rule: FilterRule) -> None:
        """Add a custom filter rule."""
        self.rules.append(rule)
    
    def remove_rule(self, category: ContentCategory) -> bool:
        """Remove all rules for a category."""
        initial_count = len(self.rules)
        self.rules = [r for r in self.rules if r.category != category]
        return len(self.rules) < initial_count
    
    def add_blocklist(self, category: ContentCategory, terms: List[str]) -> None:
        """Add terms to a category's blocklist."""
        # Add to custom blocklists
        if category not in self.custom_blocklists:
            self.custom_blocklists[category] = []
        self.custom_blocklists[category].extend(terms)
        
        # Add to rules
        self.rules.append(FilterRule(
            category=category,
            patterns=terms,
            action=FilterAction.BLOCK,
            confidence=0.9
        ))
    
    def get_flagged_categories(self, content: str) -> List[ContentCategory]:
        """Get list of flagged categories for content."""
        result = self.filter(content)
        return [c for c, score in result.categories.items() if score > 0]


# Global content filter instance
content_filter = None


def get_content_filter(rules: Optional[List[FilterRule]] = None,
                       default_action: FilterAction = FilterAction.BLOCK,
                       enable_redaction: bool = True,
                       custom_blocklists: Optional[Dict[ContentCategory, List[str]]] = None) -> ContentFilter:
    """Get or create the global content filter."""
    global content_filter
    if content_filter is None:
        content_filter = ContentFilter(
            rules,
            default_action,
            enable_redaction,
            custom_blocklists
        )
    return content_filter
