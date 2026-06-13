"""Make the standalone scripts in ``scripts/`` importable from tests.

The pipeline scripts are run as files, not installed as a package, so add the
``scripts/`` directory to ``sys.path`` (the same trick ``scripts/extract.py`` uses
internally for its vendored parsers).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
