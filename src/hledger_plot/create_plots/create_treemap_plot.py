from typing import List

import plotly.express as px
from pandas.core.frame import DataFrame
from plotly.graph_objs._figure import Figure

from hledger_plot.create_plots.create_sankey_plot import parent


def combined_treemap_plot(
    balances_df: DataFrame, account_categories: List[str], title: str
) -> Figure:
    # Filter the DataFrame for the specified categories
    filtered_df = balances_df[
        balances_df[0].str.contains("|".join(account_categories))
    ].copy()  # Make a copy to avoid modifying the original DataFrame

    # Prepare the DataFrame
    filtered_df.loc[:, "name"] = filtered_df[0]
    filtered_df.loc[:, "value"] = abs(filtered_df[1].astype(int))
    filtered_df.loc[:, "parent"] = filtered_df["name"].apply(parent)

    # Create the treemap
    fig = px.treemap(
        data_frame=filtered_df,
        names="name",
        parents="parent",
        values="value",
        branchvalues="total",
        title=f"{title} {account_categories}",
    )
    fig.layout.meta = "treemap"
    return fig
