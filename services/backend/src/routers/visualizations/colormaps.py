from __future__ import annotations

import numpy as np
from matplotlib import cm, colors


def truncate_colormap(cmap_name: str, minval: float = 0.4, maxval: float = 1.0, n: int = 256):
    base = cm.get_cmap(cmap_name)
    new_colors = base(np.linspace(minval, maxval, n))
    return colors.LinearSegmentedColormap.from_list(f"{cmap_name}_trunc_{minval}_{maxval}", new_colors)


purples_trunc = truncate_colormap("Purples", minval=0.4, maxval=1.0)
reds_trunc = truncate_colormap("Reds", minval=0.4, maxval=1.0)
