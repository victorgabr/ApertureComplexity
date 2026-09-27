#!/usr/bin/env python
"""Legacy entry point.

The CLI now lives in ``complexity.__main__`` and is also exposed as the
``aperture-complexity`` console script. This wrapper is kept for backwards
compatibility with ``python ComplexityScript.py <file>``.
"""

from complexity.__main__ import main

if __name__ == "__main__":
    main()
