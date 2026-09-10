---
name: "Data Analysis"
description: "Pandas, NumPy, visualization — performance patterns and common pitfalls"
triggers: ["pandas", "numpy", "data analysis", "visualization", "statistics", "dataframe", "plot", "matplotlib", "seaborn"]
version: "2.0.0"
author: "veni-team"
---

# Data Analysis Skill

## Pandas Performance — Flag These Patterns
- `df.iterrows()` or `df.itertuples()` in a loop → replace with vectorized ops or `apply`
- `df[df['col'] == x]` in a loop → use `.query()` or boolean indexing once
- `pd.concat` inside a loop → collect list, concat once at the end
- `df['col'].apply(lambda x: ...)` when a vectorized equivalent exists (`.str.`, `.dt.`, arithmetic)
- Reading a full CSV when only a few columns are needed → use `usecols=`

## Data Quality Checks (Always Run First)
```python
df.shape, df.dtypes, df.isnull().sum(), df.duplicated().sum()
df.describe(include='all')  # spot unexpected ranges
```
- Flag columns with >20% nulls before any analysis
- Flag object columns that should be categorical or datetime

## Visualization Rules
- Use `fig, ax = plt.subplots()` — never `plt.plot()` directly (not composable)
- Always set `ax.set_xlabel`, `ax.set_ylabel`, `ax.set_title`
- For distributions: histogram + KDE together (`sns.histplot(kde=True)`)
- For correlations: heatmap with `annot=True, fmt='.2f'`
- Save with `fig.savefig('name.png', dpi=150, bbox_inches='tight')`

## Statistical Pitfalls to Flag
- Comparing means without checking variance — suggest Mann-Whitney U for non-normal data
- Correlation reported without scatter plot — always visualize first
- Percentage change on small base numbers — flag misleading results
- Multiple comparisons without Bonferroni or FDR correction
