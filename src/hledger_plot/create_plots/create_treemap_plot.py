from argparse import Namespace
from typing import Dict, List

import plotly.express as px
from pandas.core.frame import DataFrame
from plotly.graph_objs._figure import Figure

from hledger_plot.create_plots.create_sankey_plot import get_parent
from hledger_plot.create_plots.scrambler import scramble_sankey_data
from hledger_plot.HledgerCategories import get_parent


def combined_treemap_plot(
    *,
    args: Namespace,
    balances_df: DataFrame,
    account_categories: List[str],
    title: str,
    random_words: List[str],
    separator: str,
) -> Figure:
    # Filter the DataFrame for the specified categories
    filtered_df = balances_df[
        balances_df[0].str.contains("|".join(account_categories))
    ].copy()  # Make a copy to avoid modifying the original DataFrame

    print("BEFORE filtered_df")
    print(filtered_df)

    if args.randomize:
        scrambled_df = scramble_sankey_data(
            sankey_df=filtered_df,
            random_words=random_words,
            top_level_categories=account_categories,
            separator=separator,
            text_column_headers=[0],
            numeric_column_headers=[1],
        )
        # input("scrambled_df")
        # input(scrambled_df)
        filtered_df = scrambled_df

    # Prepare the DataFrame
    filtered_df.loc[:, "name"] = filtered_df[0]
    filtered_df.loc[:, "value"] = abs(filtered_df[1].astype(int))
    filtered_df.loc[:, "parent"] = filtered_df["name"].apply(get_parent)

    # print(f'filtered_df=')
    # print(filtered_df)
    # restore_magnitudes(filtered_df=filtered_df)

    print(f"\n\nAFTER SWAP filtered_df=")
    input(filtered_df)
    set_parent_to_child_sum(df=filtered_df)

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


def get_max_level_to_min_level(
    ordered_children: Dict[int, List[str]],
) -> List[int]:
    return sorted(ordered_children.keys())


def set_parent_to_child_sum(*, df: DataFrame):
    ordered_entries: Dict[int, List[str]] = get_parent_level_dict(df=df)
    # input(f"ordered_entries={ordered_entries}")
    levels: List[int] = get_max_level_to_min_level(
        ordered_children=ordered_entries
    )
    for level in reversed(levels):
        for ordered_entry in ordered_entries[level]:
            input(
                f"{level} ordered_entry={ordered_entry},"
                f" parent={get_parent(ordered_entry)}"
            )
            if level > 0:

                # get parent, make its value its current value plus this value.
                add_to_value_of_category(
                    df=df,
                    entry_name=get_parent(ordered_entry),
                    amount=get_values_of_children(
                        df=df, child_name=ordered_entry
                    ),
                )


def add_to_value_of_category(*, df: DataFrame, entry_name: str, amount) -> None:
    for row_index, name in enumerate(df[0]):
        if name == entry_name:
            df[1][row_index] += amount
            return
    raise ValueError(f"Did not find entry_name:{entry_name}")


def get_values_of_children(*, df: DataFrame, child_name: str) -> float:
    for row_index, name in enumerate(df[0]):
        if name == child_name:
            return df[1][row_index]
    raise ValueError(f"Did not find child:{child_name}")


def get_parent_level_dict(df: DataFrame) -> Dict[int, List[str]]:
    children: Dict[int, List[str]] = {}
    for parent in df["parent"]:
        if parent != "":

            if parent.count(":") in children.keys():
                children[parent.count(":")].append(parent)
            else:
                children[parent.count(":")] = [parent]
    for key, value in children.items():
        children[key] = list(set(value))
    return children
