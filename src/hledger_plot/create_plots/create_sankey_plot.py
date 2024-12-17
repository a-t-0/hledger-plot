from typing import Dict, List

import pandas as pd
import plotly.graph_objects as go
from pandas.core.frame import DataFrame

# import plotly
from plotly.graph_objs._figure import Figure
from typeguard import typechecked


class ColumnNode:
    def __init__(self, index: int, name: str, value: float):
        self.index = index
        self.name = name
        self.value = value


class Position:
    def __init__(self, index: int, name: str, x: float, y: float):
        self.index = index
        self.name = name
        self.x = x
        self.y = y


@typechecked
def parent(transaction_category: str) -> str:
    return ":".join(transaction_category.split(":")[:-1])


@typechecked
def to_sankey_df(
    *,
    df: DataFrame,
    top_level_account_categories: List[str],
    desired_left_top_level_categories: List[str],
    desired_right_top_level_categories: List[str],
) -> pd.DataFrame:

    # TODO: assert full_transaction category does not contain duplicate values
    # like: assets:windows:assets:moon

    # Create a DataFrame to store the sankey data
    sankey_df: pd.DataFrame = pd.DataFrame(
        columns=["source", "target", "value"]
    )

    # A set of all accounts mentioned in the report, to check that parent
    # accounts have known balance.
    accounts = set(df[0].values)

    parent_acc: str

    # Convert report to the sankey dataframe
    for _, row in df.iterrows():
        full_transaction_category = row[0]
        balance = row[1]

        # Top-level accounts need to be connected to the special bucket that
        # divides input from output. The name for this bucket is randomly
        # chosen to be: BALANCE-LINE.

        if full_transaction_category in top_level_account_categories:
            parent_acc = "BALANCE-LINE"
        else:
            parent_acc = parent(transaction_category=full_transaction_category)
            if parent_acc not in accounts:
                raise Exception(
                    f"for account {full_transaction_category}, parent account"
                    f" {parent_acc} not found - have you forgotten --no-elide?"
                )

        # If no desired categories are found, do not add anything to the
        # sankey_df.
        if any(
            top_level_category in full_transaction_category
            for top_level_category in desired_left_top_level_categories
            + desired_right_top_level_categories
        ):
            if any(
                top_level_category in full_transaction_category
                for top_level_category in desired_left_top_level_categories
            ):
                if balance < 0:
                    source, target = full_transaction_category, parent_acc
                    print(
                        f"UP: {balance} -"
                        " S=full_transaction_category="
                        f"{full_transaction_category},T=parent_acc={parent_acc}"
                    )
                else:
                    source, target = parent_acc, full_transaction_category
                    print(
                        f"UP: {balance} -"
                        f" S=parent_acc={parent_acc},T="
                        f"full_transaction_category={full_transaction_category}"
                    )
            elif any(
                top_level_category in full_transaction_category
                for top_level_category in desired_right_top_level_categories
            ):
                if balance >= 0:
                    print(
                        f"DOWN: {balance} -"
                        f" S=parent_acc={parent_acc},T=f"
                        f"ull_transaction_category={full_transaction_category}"
                    )

                    source, target = parent_acc, full_transaction_category
                else:
                    print(
                        f"DOWN: {balance} -"
                        " S=full_transaction_category="
                        f"{full_transaction_category},T=parent_acc="
                        f"{parent_acc}"
                    )
                    source, target = full_transaction_category, parent_acc

            else:
                # Skip unwanted categories.
                pass
            sankey_df.loc[len(sankey_df)] = {
                "source": source,
                "target": target,
                "value": abs(balance),
            }

    sankey_df.to_csv("sankey.csv", index=False)

    return sankey_df


@typechecked
def sankey_plot(sankey_df: pd.DataFrame, title: str) -> Figure:
    # Sort DataFrame by either 'source' or 'target' column, to make sure that
    # related accounts stay close together in the initial layout.
    sankey_df.sort_values(by=["target", "source"], inplace=True)

    # Get unique sources and targets for node names
    nodes = pd.concat([sankey_df["source"], sankey_df["target"]]).unique()
    sources = sankey_df["source"].map(lambda x: nodes.tolist().index(x))

    target = sankey_df["target"].map(lambda x: nodes.tolist().index(x))
    values = sankey_df["value"]

    # Create Sankey diagram
    fig = go.Figure(
        data=[
            go.Sankey(
                node=dict(
                    pad=25,
                    thickness=20,
                    line=dict(color="black", width=0.5),
                    label=nodes,
                    color="blue",
                ),
                link=dict(
                    source=sources,
                    target=target,
                    value=values,
                ),
            )
        ],
        layout={"title": title, "meta": "sankey"},
    )

    return fig


@typechecked
def create_column_nodes(
    *,
    nodes: List[str],
    node_columns: Dict[str, int],
    node_values: Dict[int, float],
    max_column: int,
) -> Dict[int, List[ColumnNode]]:
    """Creates a dictionary mapping column indices to lists of nodes.

    Args:
        nodes: A list of node names.
        node_columns: A dictionary mapping node names to their corresponding
        column indices.
        node_values: A list of node values.
        max_column: The maximum column index.

    Returns:
        A dictionary where keys are column indices and values are lists of
        dictionaries,
        each representing a node with its index, name, and value.
    """
    column_nodes: Dict[int, List[ColumnNode]] = {
        i: [] for i in range(max_column + 1)
    }
    for i, node in enumerate(nodes):
        coumn_node: ColumnNode = ColumnNode(
            index=i, name=node, value=node_values[i]
        )
        new_index: int = node_columns[node]
        column_nodes[new_index].append(coumn_node)
    return column_nodes


@typechecked
def calculate_positions(
    column_nodes: Dict[int, List[ColumnNode]],
    max_column: int,
) -> List[Position]:
    """Calculates the x and y positions for each node based on its column and
    value.

    Args:
        column_nodes: A dictionary mapping column indices to lists of nodes.
        max_column: The maximum column index.

    Returns:
        A list of dictionaries, each containing the index, name, x-coordinate,
        and y-coordinate of a node.
    """
    positions: List[Position] = []
    for column, nodes_in_column in column_nodes.items():
        total_value: float = 0
        for columnNode in nodes_in_column:
            total_value += columnNode.value
        # total_value: int = sum(node["value"] for node in nodes_in_column)
        if total_value == 0:  # Handle nodes with no value.

            positions.append(
                Position(
                    index=nodes_in_column[0].index,
                    name=nodes_in_column[0].name,
                    x=0,
                    y=0.5,
                )
            )
            continue
        y_offset: int = 0
        for node in nodes_in_column:
            y_position = y_offset + (node.value / (2 * total_value))
            positions.append(
                Position(
                    index=node.index,
                    name=node.name,
                    x=column / max_column,
                    y=y_position,
                )
            )
            y_offset += int(float(node.value) / total_value)
    return positions


@typechecked
def compute_node_positions(
    *,
    nodes: List[str],
    sources: List[int],
    targets: List[int],
    values: List[float],
) -> List[Position]:
    node_columns: Dict[str, int] = {}
    node_values: Dict[int, float] = {i: 0 for i in range(len(nodes))}

    for i, (source, target) in enumerate(zip(sources, targets)):
        node_columns[nodes[source]] = node_columns.get(nodes[source], 0)
        node_columns[nodes[target]] = max(
            node_columns.get(nodes[target], 0), node_columns[nodes[source]] + 1
        )
        node_values[target] += values[i]

    # Handle cases where the widest node may not be at the start column.
    max_column = max(node_columns.values())

    column_nodes: Dict[int, List[ColumnNode]] = create_column_nodes(
        nodes=nodes,
        node_columns=node_columns,
        node_values=node_values,
        max_column=max_column,
    )

    return calculate_positions(
        column_nodes=column_nodes,
        max_column=max_column,
    )


@typechecked
def pysankey_plot_with_manual_pos(
    sankey_df: pd.DataFrame, title: str
) -> Figure:

    # Define nodes and links.
    # Sort DataFrame by either 'source' or 'target' column, to make sure that
    # relate accounts stay close together in the initial layout.
    sankey_df.sort_values(by=["target", "source"], inplace=True)

    # Get unique sources and targets for node names
    nodes = pd.concat([sankey_df["source"], sankey_df["target"]]).unique()
    sources: List[int] = []
    targets: List[int] = []
    values: List[float] = []
    for i, x in enumerate(sankey_df["source"]):
        sources.append(list(nodes).index(x))
    for i, x in enumerate(sankey_df["target"]):
        targets.append(list(nodes).index(x))
    for i, x in enumerate(sankey_df["value"]):
        values.append(x)

    node_positions = compute_node_positions(
        nodes=nodes.tolist(), sources=sources, targets=targets, values=values
    )

    # Extract x and y coordinates
    # [pos["x"] for pos in node_positions]
    y_coords = [pos.y for pos in node_positions]

    # Create Sankey diagram

    # Create Sankey diagram
    fig: Figure = go.Figure(
        data=[
            go.Sankey(
                node=dict(
                    pad=15,
                    thickness=20,
                    line=dict(color="black", width=0.5),
                    label=nodes,
                    # x=x_coords,
                    y=y_coords,
                ),
                link=dict(
                    source=sources,
                    target=targets,
                    value=values,
                ),
            ),
        ],
        layout={"title": title, "meta": "sankey"},
    )
    return fig
