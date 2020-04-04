import os

if os.environ.get("SUPPRESS_WARNING", 1) == 1:
    import warnings
    warnings.simplefilter(action='ignore', category=FutureWarning)