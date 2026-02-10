"""
Filter utilities module for Rob of the Shire game.

Provides flexible filtering functionality for items, inventory,
and other game data. Supports interactive and programmatic filtering.
"""

from __future__ import annotations
from typing import Optional, Any, Callable
from dataclasses import dataclass


@dataclass
class FilterConfig:
    """
    Configuration for a filter operation.
    
    Attributes:
        filter_key: What is being filtered (e.g., "item type").
        end_code: Input to finish filtering.
        all_code: Input to select all (no filter).
        prompt_template: Template for input prompt.
        case_sensitive: Whether matching is case-sensitive.
    """
    filter_key: str = "item"
    end_code: str = "done"
    all_code: str = "all"
    prompt_template: str = "Input your {filter_key} filter ('{end_code}' to finish, '{all_code}' for all): "
    case_sensitive: bool = False


def get_filter(
    filter_key: str,
    end_code: str = 'done',
    all_code: str = 'all'
) -> Optional[list[str]]:
    """
    Interactive filter input from user.
    
    Prompts user to enter filter values one at a time until
    they type the end code, or all code for no filter.
    
    Args:
        filter_key: Description of what's being filtered.
        end_code: Input to finish entering filters.
        all_code: Input to skip filtering (return None).
        
    Returns:
        List of filter values, or None for no filter.
        
    Example:
        >>> filters = get_filter("item type", end_code="q", all_code="*")
        Input your item type filter ('q' to finish, '*' for all): weapon
        Input your item type filter ('q' to finish, '*' for all): potion
        Input your item type filter ('q' to finish, '*' for all): q
        >>> filters
        ['weapon', 'potion']
    """
    type_filters: list[str] = []
    
    while True:
        prompt = f"Input your {filter_key} filter ('{end_code}' to finish, '{all_code}' for all): "
        user_input = input(prompt).strip()
        
        if user_input == end_code:
            break
        elif user_input == all_code:
            return None
        elif user_input:
            type_filters.append(user_input)
    
    return type_filters if type_filters else None


def get_filter_advanced(config: FilterConfig) -> Optional[list[str]]:
    """
    Advanced interactive filter with configuration.
    
    Args:
        config: FilterConfig with filter settings.
        
    Returns:
        List of filter values, or None for no filter.
    """
    filters: list[str] = []
    
    prompt = config.prompt_template.format(
        filter_key=config.filter_key,
        end_code=config.end_code,
        all_code=config.all_code
    )
    
    while True:
        user_input = input(prompt).strip()
        
        if not config.case_sensitive:
            compare_input = user_input.lower()
            compare_end = config.end_code.lower()
            compare_all = config.all_code.lower()
        else:
            compare_input = user_input
            compare_end = config.end_code
            compare_all = config.all_code
        
        if compare_input == compare_end:
            break
        elif compare_input == compare_all:
            return None
        elif user_input:
            filters.append(user_input)
    
    return filters if filters else None


def get_single_filter(
    filter_key: str,
    options: Optional[list[str]] = None,
    allow_custom: bool = True
) -> Optional[str]:
    """
    Get a single filter value with optional choices.
    
    Args:
        filter_key: Description of what's being filtered.
        options: Optional list of valid options to display.
        allow_custom: Allow custom input if not in options.
        
    Returns:
        Selected filter value, or None if cancelled.
    """
    if options:
        print(f"\n{filter_key.capitalize()} options:")
        for i, option in enumerate(options, 1):
            print(f"  {i}. {option}")
        if allow_custom:
            print("  Enter number or custom value (blank to cancel)")
        else:
            print("  Enter number (blank to cancel)")
    
    user_input = input(f"Select {filter_key}: ").strip()
    
    if not user_input:
        return None
    
    if options:
        try:
            idx = int(user_input) - 1
            if 0 <= idx < len(options):
                return options[idx]
        except ValueError:
            pass
        
        if allow_custom:
            return user_input
        
        print("Invalid selection.")
        return None
    
    return user_input


def apply_filter(
    items: list[dict],
    filters: Optional[list[str]],
    filter_field: str = "type"
) -> list[dict]:
    """
    Apply filters to a list of items.
    
    Args:
        items: List of item dictionaries.
        filters: List of values to include, or None for all.
        filter_field: The field to filter on.
        
    Returns:
        Filtered list of items.
    """
    if filters is None:
        return items.copy()
    
    # Normalize filters to lowercase
    normalized_filters = [f.lower() for f in filters]
    
    return [
        item for item in items
        if str(item.get(filter_field, "")).lower() in normalized_filters
    ]


def apply_multi_filter(
    items: list[dict],
    filters: dict[str, Any]
) -> list[dict]:
    """
    Apply multiple field filters to items.
    
    Args:
        items: List of item dictionaries.
        filters: Dictionary of field: value pairs to match.
        
    Returns:
        Filtered list of items.
        
    Example:
        >>> apply_multi_filter(items, {"type": "weapon", "damage": 30})
    """
    result = items.copy()
    
    for field, value in filters.items():
        if value is None:
            continue
        
        if isinstance(value, list):
            result = [item for item in result if item.get(field) in value]
        elif callable(value):
            result = [item for item in result if value(item.get(field))]
        else:
            result = [item for item in result if item.get(field) == value]
    
    return result


def create_range_filter(
    min_val: Optional[int] = None,
    max_val: Optional[int] = None
) -> Callable[[Any], bool]:
    """
    Create a range filter function.
    
    Args:
        min_val: Minimum value (inclusive).
        max_val: Maximum value (inclusive).
        
    Returns:
        Filter function that checks if value is in range.
    """
    def filter_func(value: Any) -> bool:
        if value is None:
            return False
        try:
            num = int(value)
            if min_val is not None and num < min_val:
                return False
            if max_val is not None and num > max_val:
                return False
            return True
        except (TypeError, ValueError):
            return False
    
    return filter_func


def search_items(
    items: list[dict],
    query: str,
    search_fields: list[str] = None
) -> list[dict]:
    """
    Search items by text query.
    
    Args:
        items: List of item dictionaries.
        query: Search query string.
        search_fields: Fields to search in (default: ["name"]).
        
    Returns:
        List of items matching the query.
    """
    if not query:
        return items.copy()
    
    if search_fields is None:
        search_fields = ["name"]
    
    query_lower = query.lower()
    
    results = []
    for item in items:
        for field in search_fields:
            value = item.get(field, "")
            if isinstance(value, str) and query_lower in value.lower():
                results.append(item)
                break
    
    return results


def sort_items(
    items: list[dict],
    sort_field: str,
    reverse: bool = False
) -> list[dict]:
    """
    Sort items by a field.
    
    Args:
        items: List of item dictionaries.
        sort_field: Field to sort by.
        reverse: Sort in descending order.
        
    Returns:
        Sorted list of items.
    """
    return sorted(
        items,
        key=lambda x: x.get(sort_field, 0),
        reverse=reverse
    )


def group_items_by(
    items: list[dict],
    group_field: str
) -> dict[str, list[dict]]:
    """
    Group items by a field value.
    
    Args:
        items: List of item dictionaries.
        group_field: Field to group by.
        
    Returns:
        Dictionary of group_value: items.
    """
    groups: dict[str, list[dict]] = {}
    
    for item in items:
        key = str(item.get(group_field, "other"))
        if key not in groups:
            groups[key] = []
        groups[key].append(item)
    
    return groups


class ItemFilter:
    """
    Class-based filter for chaining filter operations.
    
    Provides a fluent interface for building complex filters.
    """
    
    def __init__(self, items: list[dict]):
        """Initialize with a list of items."""
        self._items = items.copy()
        self._original = items.copy()
    
    def by_type(self, *types: str) -> 'ItemFilter':
        """Filter by item type(s)."""
        type_list = [t.lower() for t in types]
        self._items = [
            item for item in self._items
            if item.get("type", "").lower() in type_list
        ]
        return self
    
    def by_name(self, pattern: str) -> 'ItemFilter':
        """Filter by name containing pattern."""
        pattern_lower = pattern.lower()
        self._items = [
            item for item in self._items
            if pattern_lower in item.get("name", "").lower()
        ]
        return self
    
    def by_damage(
        self,
        min_val: Optional[int] = None,
        max_val: Optional[int] = None
    ) -> 'ItemFilter':
        """Filter by damage range."""
        filter_func = create_range_filter(min_val, max_val)
        self._items = [
            item for item in self._items
            if filter_func(item.get("damage"))
        ]
        return self
    
    def by_defense(
        self,
        min_val: Optional[int] = None,
        max_val: Optional[int] = None
    ) -> 'ItemFilter':
        """Filter by defense range."""
        filter_func = create_range_filter(min_val, max_val)
        self._items = [
            item for item in self._items
            if filter_func(item.get("defense"))
        ]
        return self
    
    def by_property(self, key: str, value: Any) -> 'ItemFilter':
        """Filter by custom property."""
        self._items = [
            item for item in self._items
            if item.get(key) == value
        ]
        return self
    
    def sort_by(self, field: str, reverse: bool = False) -> 'ItemFilter':
        """Sort results by field."""
        self._items = sort_items(self._items, field, reverse)
        return self
    
    def limit(self, count: int) -> 'ItemFilter':
        """Limit number of results."""
        self._items = self._items[:count]
        return self
    
    def reset(self) -> 'ItemFilter':
        """Reset to original items."""
        self._items = self._original.copy()
        return self
    
    def get(self) -> list[dict]:
        """Get the filtered results."""
        return self._items.copy()
    
    def first(self) -> Optional[dict]:
        """Get the first matching item."""
        return self._items[0] if self._items else None
    
    def count(self) -> int:
        """Get count of matching items."""
        return len(self._items)
