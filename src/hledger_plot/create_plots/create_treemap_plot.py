from argparse import Namespace
from typing import Dict, List

import plotly.express as px
from pandas.core.frame import DataFrame
from plotly.graph_objs._figure import Figure
from typeguard import typechecked

from hledger_plot.create_plots.scrambler import scramble_sankey_data
from hledger_plot.HledgerCategories import get_parent


def check_negative_assets(df, identifier: str):
    # Look at original values in column 1 before abs() was applied
    negative_assets = df[
        (df[0].str.startswith(identifier)) & (df[1].astype(int) < 0)
    ]

    if not negative_assets.empty:
        problematic_assets = negative_assets[[0, 1]].values.tolist()
        # Create formatted string with name-value pairs on new lines.
        error_details = "\n".join(
            f"{name}: {value}" for name, value in problematic_assets
        )
        raise ValueError(
            f"Negative values found for assets:\n{error_details}\nAsset values"
            " should not be negative. (Probably your opening balance is"
            " incorrect or set for a different account."
        )


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

    if len(set(filtered_df[0])) != len(filtered_df[0]):
        raise ValueError("Found dupes.")

    # Prepare the DataFrame
    filtered_df.loc[:, "name"] = filtered_df[0]
    filtered_df.loc[:, "value"] = abs(filtered_df[1].astype(int))
    filtered_df.loc[:, "parent"] = filtered_df["name"].apply(get_parent)

    check_negative_assets(df=filtered_df, identifier="assets")

    if args.randomize:
        scramble_sankey_data(
            sankey_df=filtered_df,
            random_words=random_words,
            top_level_categories=account_categories,
            separator=separator,
            text_column_headers=[0],
            numeric_column_headers=[1],
        )

        if len(set(filtered_df[0])) != len(filtered_df[0]):
            raise ValueError("Found dupes after randomization.")

        set_parent_to_child_sum(df=filtered_df)
        filtered_df.loc[:, "name"] = filtered_df[0]
        filtered_df.loc[:, "value"] = abs(filtered_df[1].astype(int))
        filtered_df.loc[:, "parent"] = filtered_df["name"].apply(get_parent)

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


@typechecked
def get_max_level_to_min_level(
    ordered_children: Dict[int, List[str]],
) -> List[int]:
    return sorted(ordered_children.keys())


@typechecked
def set_parent_to_child_sum(*, df: DataFrame) -> None:
    ordered_entries: Dict[int, List[str]] = get_level_dict(df=df)
    levels: List[int] = get_max_level_to_min_level(
        ordered_children=ordered_entries
    )
    for level in reversed(levels):
        for ordered_entry in ordered_entries[level]:
            if level > 0:

                # get parent, make its value its current value plus this value.
                add_to_value_of_category(
                    df=df,
                    entry_name=get_parent(ordered_entry),
                    amount=get_values_of_children(
                        df=df, child_name=ordered_entry
                    ),
                )


@typechecked
def add_to_value_of_category(
    *, df: DataFrame, entry_name: str, amount: float
) -> None:
    """Adds the specified amount to the value of the given entry in the
    DataFrame.

    Args:
        df: The DataFrame containing the data.
        entry_name: The name of the entry to modify.
        amount: The amount to add to the entry's value.

    Raises:
        ValueError: If the entry_name is not found in the DataFrame.
    """

    try:
        df.loc[df[0] == entry_name, 1] += amount
    except KeyError:
        raise ValueError(f"Did not find entry_name:{entry_name}")


@typechecked
def get_values_of_children(*, df: DataFrame, child_name: str) -> float:
    some = df.loc[df[0] == child_name, 1]
    if len(some) != 1:
        raise ValueError("returning something other than a single number.")
    some_float: float = float(some.iloc[0])
    return some_float


@typechecked
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


def get_level_dict(df: DataFrame) -> Dict[int, List[str]]:
    children: Dict[int, List[str]] = {}
    for category in df[0]:
        if category != "":

            if category.count(":") in children.keys():
                children[category.count(":")].append(category)
            else:
                children[category.count(":")] = [category]
        else:
            raise ValueError(f"Empty categories not supported:{category}")
    for key, value in children.items():
        children[key] = list(set(value))
    return children
