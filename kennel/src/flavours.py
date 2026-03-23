# kennel/src/flavours.py
from dataclasses import dataclass, field


@dataclass
class FlavourDef:
    name:         str
    parent:       str | None        # None = build from template
    scripts:      list[str]         # provision scripts to run in order
    template:     str  = "ubuntu"
    release:      str  = "release"
    description:  str  = ""


FLAVOURS: dict[str, FlavourDef] = {
    "base": FlavourDef(
        name        = "base",
        parent      = None,
        scripts     = ["00-base.sh"],
        template    = "ubuntu",
        release     = "noble",
        description = "Ubuntu noble + system essentials",
    ),
    "dev": FlavourDef(
        name        = "dev",
        parent      = "base",
        scripts     = ["01-dev.sh"],
        description = "base + build tools, python, node",
    ),
    "cuda": FlavourDef(
        name        = "cuda",
        parent      = "dev",
        scripts     = ["02-cuda.sh"],
        description = "dev + CUDA toolkit, PyTorch",
    ),
}


def build_order(flavour: str) -> list[str]:
    """
    Returns the full ancestry chain in build order.
    e.g. build_order("cuda") → ["base", "dev", "cuda"]
    """
    chain = []
    current = flavour
    while current:
        chain.append(current)
        current = FLAVOURS[current].parent
    chain.reverse()
    return chain