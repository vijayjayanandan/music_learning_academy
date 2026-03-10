import re

import bleach
from django import template
from django.utils.safestring import mark_safe

register = template.Library()

ALLOWED_TAGS = [
    "a", "abbr", "b", "blockquote", "br", "code", "em", "h1", "h2", "h3",
    "h4", "h5", "h6", "hr", "i", "img", "li", "ol", "p", "pre", "span",
    "strong", "sub", "sup", "table", "tbody", "td", "th", "thead", "tr",
    "u", "ul", "div",
]

ALLOWED_ATTRIBUTES = {
    "a": ["href", "title", "target", "rel"],
    "img": ["src", "alt", "width", "height"],
    "td": ["colspan", "rowspan"],
    "th": ["colspan", "rowspan"],
    "*": ["class", "style"],
}

ALLOWED_PROTOCOLS = ["http", "https", "mailto"]

# Pre-strip patterns: remove <script> and <style> tags along with their
# content BEFORE bleach runs, because bleach.clean(strip=True) strips the
# tags but keeps the inner text (e.g. alert("xss") would survive).
_STRIP_PATTERNS = re.compile(
    r"<(script|style)\b[^>]*>.*?</\1>",
    re.IGNORECASE | re.DOTALL,
)


@register.filter(name="sanitize_html")
def sanitize_html(value):
    """Sanitize HTML content using bleach to prevent XSS attacks."""
    if not value:
        return ""
    # Remove <script>/<style> tags AND their content before bleach sees them
    value = _STRIP_PATTERNS.sub("", value)
    cleaned = bleach.clean(
        value,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        protocols=ALLOWED_PROTOCOLS,
        strip=True,
    )
    return mark_safe(cleaned)
