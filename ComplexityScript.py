#!/usr/bin/env python
"""Legacy entry point.

The CLI is in ``complexity.__main__``, which the ``aperture-complexity``
console script also runs. This wrapper keeps compatibility with
``python ComplexityScript.py <file>``.
"""

from complexity.__main__ import main

if __name__ == "__main__":
    main()
