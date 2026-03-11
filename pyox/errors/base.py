class ParseError(Exception):
    """Base class for parser errors."""
    pass

class LL1ConflictError(Exception):
    """Base class for LL(1) parser conflict errors."""
    pass

class SLR1ConflictError(Exception):
    """Base class for SLR(1) parser conflict errors."""
    pass