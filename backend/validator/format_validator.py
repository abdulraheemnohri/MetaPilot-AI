"""
MetaPilot AI - Format Validator

Validates the format of AI responses.
"""

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union, Set
import re
import json

logger = logging.getLogger(__name__)


class FormatType(Enum):
    """Types of formats to validate."""
    TEXT = "text"
    MARKDOWN = "markdown"
    JSON = "json"
    HTML = "html"
    CODE = "code"
    LIST = "list"
    TABLE = "table"
    CUSTOM = "custom"


@dataclass
class FormatValidationResult:
    """Result of format validation."""
    is_valid: bool
    format_type: Optional[FormatType] = None
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    score: float = 1.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_valid": self.is_valid,
            "format_type": self.format_type.value if self.format_type else None,
            "errors": self.errors,
            "warnings": self.warnings,
            "score": self.score
        }


@dataclass
class FormatRule:
    """A format validation rule."""
    format_type: FormatType
    required: bool = True
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    pattern: Optional[str] = None
    validator: Optional[Any] = None
    error_message: str = "Invalid format"


class FormatValidator:
    """
    Validates the format of AI responses.
    
    Checks if responses conform to expected formats.
    """
    
    def __init__(self, 
                 rules: Optional[List[FormatRule]] = None,
                 default_format: FormatType = FormatType.TEXT,
                 strict_mode: bool = False):
        """
        Initialize the format validator.
        
        Args:
            rules: List of format validation rules
            default_format: Default expected format
            strict_mode: Whether to be strict about format validation
        """
        self.default_format = default_format
        self.strict_mode = strict_mode
        self.rules = rules or []
        
        # Initialize default rules
        self._initialize_default_rules()
    
    def _initialize_default_rules(self):
        """Initialize default format rules."""
        # Text format
        self.rules.append(FormatRule(
            format_type=FormatType.TEXT,
            required=False,
            min_length=10,
            error_message="Text is too short"
        ))
        
        # JSON format
        self.rules.append(FormatRule(
            format_type=FormatType.JSON,
            required=False,
            validator=self._validate_json,
            error_message="Invalid JSON format"
        ))
        
        # Markdown format
        self.rules.append(FormatRule(
            format_type=FormatType.MARKDOWN,
            required=False,
            validator=self._validate_markdown,
            error_message="Invalid Markdown format"
        ))
        
        # Code format
        self.rules.append(FormatRule(
            format_type=FormatType.CODE,
            required=False,
            validator=self._validate_code,
            error_message="Invalid code format"
        ))
        
        # List format
        self.rules.append(FormatRule(
            format_type=FormatType.LIST,
            required=False,
            validator=self._validate_list,
            error_message="Invalid list format"
        ))
    
    def validate(self, 
                 content: str,
                 expected_format: Optional[FormatType] = None,
                 rules: Optional[List[FormatRule]] = None) -> FormatValidationResult:
        """
        Validate the format of content.
        
        Args:
            content: The content to validate
            expected_format: Expected format type
            rules: Optional list of rules to use
        
        Returns:
            FormatValidationResult with validation details
        """
        effective_format = expected_format or self.default_format
        effective_rules = rules or self.rules
        
        errors: List[str] = []
        warnings: List[str] = []
        score = 1.0
        
        # Check each rule
        for rule in effective_rules:
            if rule.format_type != effective_format:
                continue
            
            # Check required
            if rule.required and not content:
                errors.append(f"{rule.error_message}: Content is required")
                score -= 0.5
                continue
            
            # Check min length
            if rule.min_length and len(content) < rule.min_length:
                errors.append(f"{rule.error_message}: Minimum length is {rule.min_length}")
                score -= 0.3
            
            # Check max length
            if rule.max_length and len(content) > rule.max_length:
                errors.append(f"{rule.error_message}: Maximum length is {rule.max_length}")
                score -= 0.2
            
            # Check pattern
            if rule.pattern:
                if not re.search(rule.pattern, content):
                    errors.append(f"{rule.error_message}: Does not match pattern")
                    score -= 0.4
            
            # Check custom validator
            if rule.validator:
                try:
                    is_valid, error_msg = rule.validator(content)
                    if not is_valid:
                        errors.append(f"{rule.error_message}: {error_msg}")
                        score -= 0.5
                except Exception as e:
                    errors.append(f"{rule.error_message}: Validation error - {str(e)}")
                    score -= 0.5
        
        # Check format-specific validation
        format_errors, format_warnings = self._validate_format(content, effective_format)
        errors.extend(format_errors)
        warnings.extend(format_warnings)
        
        # Calculate final score
        score = max(0, min(1, score))
        
        is_valid = not errors if self.strict_mode else (len(errors) == 0 and score >= 0.7)
        
        return FormatValidationResult(
            is_valid=is_valid,
            format_type=effective_format,
            errors=errors,
            warnings=warnings,
            score=round(score, 4)
        )
    
    def _validate_format(self, 
                         content: str,
                         format_type: FormatType) -> Tuple[List[str], List[str]]:
        """Validate content based on format type."""
        errors: List[str] = []
        warnings: List[str] = []
        
        if format_type == FormatType.JSON:
            try:
                json.loads(content)
            except json.JSONDecodeError as e:
                errors.append(f"Invalid JSON: {str(e)}")
        
        elif format_type == FormatType.MARKDOWN:
            # Check for unclosed code blocks
            code_blocks = re.findall(r'```\w*', content)
            if len(code_blocks) % 2 != 0:
                warnings.append("Unclosed code block in Markdown")
            
            # Check for unclosed bold/italic
            bold_count = content.count("**")
            if bold_count % 2 != 0:
                warnings.append("Unclosed bold formatting in Markdown")
            
            italic_count = content.count("*")
            if italic_count % 2 != 0:
                warnings.append("Unclosed italic formatting in Markdown")
        
        elif format_type == FormatType.HTML:
            # Basic HTML validation
            if "<" in content and ">" not in content:
                errors.append("Unclosed HTML tag")
            
            # Check for unclosed tags (simplified)
            open_tags = re.findall(r'<\w+', content)
            close_tags = re.findall(r'</\w+>', content)
            if len(open_tags) != len(close_tags):
                warnings.append("Possible unclosed HTML tags")
        
        elif format_type == FormatType.CODE:
            # Check for syntax errors (language-specific)
            # This is a placeholder - actual implementation would need language detection
            pass
        
        elif format_type == FormatType.LIST:
            # Check for list format
            lines = content.split('\n')
            list_items = [l for l in lines if l.strip().startswith(('- ', '* ', '1. ', '   '))]
            
            if not list_items:
                warnings.append("No list items detected")
        
        return errors, warnings
    
    def _validate_json(self, content: str) -> Tuple[bool, str]:
        """Validate JSON format."""
        try:
            json.loads(content)
            return True, ""
        except json.JSONDecodeError as e:
            return False, str(e)
    
    def _validate_markdown(self, content: str) -> Tuple[bool, str]:
        """Validate Markdown format."""
        # Basic validation - just check for common issues
        # This is a simplified validation
        issues = []
        
        # Check for unclosed code blocks
        code_blocks = re.findall(r'```\w*', content)
        if len(code_blocks) % 2 != 0:
            issues.append("Unclosed code block")
        
        # Check for unclosed bold
        if content.count("**") % 2 != 0:
            issues.append("Unclosed bold formatting")
        
        # Check for unclosed italic
        if content.count("*") % 2 != 0:
            issues.append("Unclosed italic formatting")
        
        if issues:
            return False, "; ".join(issues)
        
        return True, ""
    
    def _validate_code(self, content: str) -> Tuple[bool, str]:
        """Validate code format."""
        # This is a placeholder - actual validation would be language-specific
        # For now, just check for basic syntax issues
        
        # Check for unclosed brackets
        open_brackets = content.count('{') + content.count('[') + content.count('(')
        close_brackets = content.count('}') + content.count(']') + content.count(')')
        
        if open_brackets != close_brackets:
            return False, "Unclosed brackets"
        
        # Check for unclosed quotes
        single_quotes = content.count("'")
        double_quotes = content.count('"')
        
        if single_quotes % 2 != 0 or double_quotes % 2 != 0:
            return False, "Unclosed quotes"
        
        return True, ""
    
    def _validate_list(self, content: str) -> Tuple[bool, str]:
        """Validate list format."""
        lines = content.split('\n')
        list_items = [l for l in lines if l.strip().startswith(('- ', '* ', '1. '))]
        
        if not list_items:
            return False, "No list items found"
        
        # Check for consistent list format
        formats = set()
        for item in list_items:
            if item.startswith('- '):
                formats.add('dash')
            elif item.startswith('* '):
                formats.add('star')
            elif re.match(r'\d+\. ', item):
                formats.add('number')
        
        if len(formats) > 1:
            return False, "Inconsistent list format"
        
        return True, ""
    
    def detect_format(self, content: str) -> FormatType:
        """
        Detect the format of content.
        
        Args:
            content: The content to analyze
        
        Returns:
            Detected format type
        """
        # Check for JSON
        try:
            json.loads(content)
            return FormatType.JSON
        except:
            pass
        
        # Check for code (has consistent indentation, special characters)
        if self._is_code(content):
            return FormatType.CODE
        
        # Check for HTML
        if '<' in content and '>' in content:
            return FormatType.HTML
        
        # Check for Markdown
        if ('# ' in content or 
            '**' in content or 
            '*' in content or 
            '```' in content or
            '[' in content or
            ']' in content):
            return FormatType.MARKDOWN
        
        # Check for list
        lines = content.split('\n')
        list_lines = [l for l in lines if l.strip().startswith(('- ', '* ', '1. '))]
        if list_lines and len(list_lines) / len(lines) > 0.5:
            return FormatType.LIST
        
        # Default to text
        return FormatType.TEXT
    
    def _is_code(self, content: str) -> bool:
        """Check if content looks like code."""
        # Check for common code patterns
        code_patterns = [
            r'def\s+\w+',  # Python function
            r'function\s+\w+',  # JavaScript function
            r'class\s+\w+',  # Class definition
            r'import\s+',  # Import statement
            r'from\s+',  # From import
            r'//',  # Comment
            r'/*',  # Block comment
            r'#',  # Shell/Python comment
            r'\{\s*\}',  # Empty braces
            r'\[\s*\]',  # Empty brackets
            r'\(\s*\)',  # Empty parens
        ]
        
        for pattern in code_patterns:
            if re.search(pattern, content):
                return True
        
        # Check for consistent indentation
        lines = content.split('\n')
        indented_lines = [l for l in lines if l.startswith('    ') or l.startswith('\t')]
        
        if indented_lines and len(indented_lines) / len(lines) > 0.3:
            return True
        
        return False
    
    def add_rule(self, rule: FormatRule) -> None:
        """Add a custom format rule."""
        self.rules.append(rule)
    
    def remove_rules(self, format_type: FormatType) -> int:
        """Remove all rules for a format type."""
        initial_count = len(self.rules)
        self.rules = [r for r in self.rules if r.format_type != format_type]
        return initial_count - len(self.rules)


# Global format validator instance
format_validator = None


def get_format_validator(rules: Optional[List[FormatRule]] = None,
                         default_format: FormatType = FormatType.TEXT,
                         strict_mode: bool = False) -> FormatValidator:
    """Get or create the global format validator."""
    global format_validator
    if format_validator is None:
        format_validator = FormatValidator(rules, default_format, strict_mode)
    return format_validator
