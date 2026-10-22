"""Template extensions for the Nautobot MCP Server app.

No object-detail extensions are shipped today; this module exists to follow
the standard Nautobot app layout and provide an obvious place to add
``TemplateExtension`` subclasses later. Imported only inside Nautobot.
"""

from __future__ import annotations

template_extensions: list = []
