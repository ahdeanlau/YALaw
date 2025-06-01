# Helper for dot-notation access (private)
def _dig(self, obj: dict, dotted_field: str):
    """Return a nested value given dot-notation (e.g. 'a.b.c') or raise KeyError."""
    current = obj
    for key in dotted_field.split("."):
        current = current[key]          # KeyError if missing
    return current
