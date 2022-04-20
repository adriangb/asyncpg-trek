import sys

if sys.version_info < (3, 8):
    from typing_extensions import Literal as Literal  # noqa: F401
    from typing_extensions import Protocol as Protocol  # noqa: F401
else:
    from typing import Literal as Literal  # noqa: F401
    from typing import Protocol as Protocol  # noqa: F401
