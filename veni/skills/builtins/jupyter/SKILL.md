---
name: "Jupyter"
description: "Notebook best practices, reproducibility, and clean cell generation"
triggers: ["notebook", "jupyter", "ipynb", "cell", "kernel", "colab", "kaggle"]
version: "1.0.0"
author: "veni-team"
---

# Jupyter Skill

## Cell Generation Rules
When writing notebook cells:
- Each cell does one thing — load data, clean data, visualise, model (separate cells)
- First cell: imports only — no logic
- Second cell: constants and config — no computation
- Use `# %%` section markers for logical groupings
- End analysis cells with a display call so output is visible without running manually

## Reproducibility — Always Include
```python
# At the top of every notebook
import random, numpy as np
SEED = 42
random.seed(SEED)
np.random.seed(SEED)
# torch.manual_seed(SEED) if using PyTorch
```

## Common Mistakes to Flag
- Mutable global state modified across cells — execution order matters
- `df = df[df['col'] > 0]` reassigning the original — use a new name or `.copy()`
- Cell outputs committed to git — add `nbstripout` or `.gitattributes` filter
- `!pip install` inside a notebook cell — use requirements.txt instead
- Hardcoded file paths like `/home/username/data/` — use `pathlib.Path` relative paths

## Before Sharing a Notebook
1. Kernel → Restart & Run All — verify it runs clean from top to bottom
2. Check all outputs are current (no stale cell outputs)
3. Strip large outputs (images, DataFrames >20 rows) before committing
4. Add a markdown cell at the top: purpose, data source, last updated

## Display Helpers
```python
# Always set display options at the top
pd.set_option('display.max_columns', 50)
pd.set_option('display.float_format', '{:.4f}'.format)

# Show shape + sample together
def peek(df, n=5):
    print(df.shape)
    return df.head(n)
```
