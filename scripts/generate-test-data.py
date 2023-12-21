import pandas as pd

# This dataframe includes tree-level attributes provided in the 4 example
# section of the NSVB GTR.
trees = pd.DataFrame(
    {
        "spcd": [202, 316, 631, 802],
        "division": ["240", "M210", "M240", "M220"],
        "dia": [20.0, 11.1, 11.3, 18.1],
        "ht": [110.0, 38.0, 28.0, 65.0],
        "actual_ht": [110.0, 38.0, 21.0, 59.0],
        "decay_class": [0, 0, 2, 0],
        "cull": [0.0, 3.0, 10.0, 2.0],
    }
)

print(trees)
trees.to_csv("example_trees.csv", index=False)
