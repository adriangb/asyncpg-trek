import sys
if sys.version_info < (3, 9):
    from typing_extensions import Literal as Literal
else:
    from typing import Literal as Literal
