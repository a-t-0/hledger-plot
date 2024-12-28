import os
from argparse import Namespace
from typing import Dict, List

import pandas as pd
from pandas.core.frame import DataFrame
from plotly.graph_objs._figure import Figure
from plotly.subplots import make_subplots
from typeguard import typechecked

from hledger_plot import HledgerCategories
from hledger_plot.create_plots.create_sankey_plot import (
    pysankey_plot_with_manual_pos,
    to_sankey_df,
)
from hledger_plot.create_plots.create_treemap_plot import combined_treemap_plot
from hledger_plot.parse_journal import read_balance_report


@typechecked
def manage_plotting(
    *,
    args: Namespace,
    journal_filepath: str,
    top_level_account_categories: List[str],
    hledgerCategories: HledgerCategories,
    random_words: List[str],
    separator: str,
) -> None:
    merged_account_categories = " ".join(top_level_account_categories)

    # Get all balances information used to create plot.
    all_balances_df: DataFrame = read_balance_report(
        args=args,
        filename=journal_filepath,
        account_categories=merged_account_categories,
        top_level_account_categories=top_level_account_categories,
    )

    # Create incomve vs expense dataframe. It's used to create the Sankey plot.
    income_vs_expenses_df: DataFrame = read_balance_report(
        args=args,
        filename=journal_filepath,
        account_categories=hledgerCategories.expense_categories
        + " "
        + hledgerCategories.income_categories,
        top_level_account_categories=top_level_account_categories,
    )

    # Create incomve vs expense dataframe. It's used to create the Sankey plot.
    net_worth_df: DataFrame = read_balance_report(
        args=args,
        filename=journal_filepath,
        account_categories=hledgerCategories.liability_categories
        + " "
        + hledgerCategories.asset_categories,
        top_level_account_categories=top_level_account_categories,
    )

    [
        net_worth_treemap,
        income_vs_expenses_treemap,
        expenses_treemap,
        income_treemap,
        all_balances_sankey_man_pos,
        income_expenses_sankey_man_pos,
    ] = create_plot_objects(
        args=args,
        all_balances_df=all_balances_df,
        top_level_account_categories=top_level_account_categories,
        hledgerCategories=hledgerCategories,
        income_expenses_df=income_vs_expenses_df,
        net_worth_df=net_worth_df,
        random_words=random_words,
        separator=separator,
    )

    export_plots(
        args=args,
        # income_vs_expenses_treemap=income_vs_expenses_treemap, TODO: support.
        expenses_treemap=expenses_treemap,
        all_balances_sankey=all_balances_sankey_man_pos,
        income_expenses_sankey=income_expenses_sankey_man_pos,
        net_worth_treemap=net_worth_treemap,
    )
    show_plots(
        args=args,
        some_figs=[
            net_worth_treemap,
            income_vs_expenses_treemap,
            expenses_treemap,
            income_treemap,
            all_balances_sankey_man_pos,
            income_expenses_sankey_man_pos,
        ],
    )


@typechecked
def create_plot_objects(
    *,
    args: Namespace,
    all_balances_df: DataFrame,
    top_level_account_categories: List[str],
    hledgerCategories: HledgerCategories,
    income_expenses_df: DataFrame,
    net_worth_df: DataFrame,
    random_words: List[str],
    separator: str,
) -> List[Figure]:
    net_worth_sankey: pd.DataFrame = to_sankey_df(
        args=args,
        df=all_balances_df,
        top_level_account_categories=top_level_account_categories,
        desired_left_top_level_categories=[
            hledgerCategories.liability_categories
        ],
        desired_right_top_level_categories=[hledgerCategories.asset_categories],
        random_words=random_words,
        separator=separator,
    )

    # Get all balances plot.
    all_balances_sankey_man_pos: Figure = pysankey_plot_with_manual_pos(
        sankey_df=net_worth_sankey,
        title="Sankey plot - How your assets cover your liabilities:",
    )

    # Create the income vs expense Sankey plot.
    income_vs_expenses_sankey_df: pd.DataFrame = to_sankey_df(
        args=args,
        df=income_expenses_df,
        top_level_account_categories=top_level_account_categories,
        desired_left_top_level_categories=[hledgerCategories.income_categories],
        desired_right_top_level_categories=[
            hledgerCategories.expense_categories
        ],
        random_words=random_words,
        separator=separator,
    )
    income_expenses_sankey_man_pos: Figure = pysankey_plot_with_manual_pos(
        sankey_df=income_vs_expenses_sankey_df,
        title=(
            "Sankey plot - Change over time: how your income covered your"
            " expenses:"
        ),
    )

    # Generate the Treemap plot for the expenses.
    income_vs_expenses_treemap: Figure = combined_treemap_plot(
        income_expenses_df,
        [
            hledgerCategories.income_categories,
            hledgerCategories.expense_categories,
        ],
        title=(
            "Treemap - Change over time: how your income covered your expenses:"
        ),
    )

    expenses_treemap: Figure = combined_treemap_plot(
        income_expenses_df,
        [hledgerCategories.expense_categories],
        title="Treemap - Overview of your expenses:",
    )
    income_treemap: Figure = combined_treemap_plot(
        income_expenses_df,
        [hledgerCategories.income_categories],
        title="Treemap - Overview of your income:",
    )

    net_worth_treemap: Figure = combined_treemap_plot(
        net_worth_df,
        [
            hledgerCategories.liability_categories,
            hledgerCategories.asset_categories,
        ],
        title="Treemap - Your financial state/position:",
    )
    return [
        net_worth_treemap,
        income_vs_expenses_treemap,
        expenses_treemap,
        income_treemap,
        all_balances_sankey_man_pos,
        income_expenses_sankey_man_pos,
    ]


@typechecked
def show_plots(
    *,
    args: Namespace,
    some_figs: List[Figure],
) -> None:
    if args.show_plots:

        specs: List[List[Dict[str, str]]] = []
        for some_fig in some_figs:
            specs.append([{"type": some_fig.layout.meta}])
        subplot_titles = [fig.layout.title.text for fig in some_figs]
        # Display all three graphs in a column.
        fig = make_subplots(
            rows=len(some_figs),
            cols=1,
            specs=specs,
            subplot_titles=subplot_titles,
        )
        for i, some_fig in enumerate(some_figs):
            # Expenses treemap first
            fig.add_trace(some_fig.data[0], row=i + 1, col=1)
            # fig.update_xaxes(title_text=some_fig.layout.title, row=i + 1)
            fig.update_xaxes(title_text=some_fig.layout.title, row=i + 1)

        fig.update_layout(
            title_text="Insight in financial situation",
            height=len(some_figs) * 900,
        )  # n plots x 900 px

        fig.show()


@typechecked
def export_plots(
    *,
    args: Namespace,
    expenses_treemap: Figure,
    all_balances_sankey: Figure,
    income_expenses_sankey: Figure,
    net_worth_treemap: Figure,
) -> None:

    output_dir: str = os.path.dirname(args.journal_filepath)
    journal_filename: str = os.path.basename(args.journal_filepath)
    # Validate the filename extension
    if journal_filename[-8:] != ".journal":
        raise ValueError("Journal filename must end in .journal")

    journal_filename_without_ext: str = journal_filename[
        :-8
    ]  # Remove the .journal suffix
    if len(journal_filename_without_ext) < 1:
        raise ValueError("Journal should have a filename")

    # Export options
    if args.export_sankey:
        # Export the first Sankey diagram
        income_expenses_sankey.write_image(
            f"{output_dir}/{journal_filename_without_ext}_income_expenses_sank"
            + "ey.png",
            format="png",
        )
        # Export the second Sankey diagram
        all_balances_sankey.write_image(
            f"{output_dir}/{journal_filename_without_ext}_all_balances_sanke"
            + "y.png",
            format="png",
        )

    if args.export_treemap:
        # Export the treemap
        expenses_treemap.write_image(
            f"{output_dir}/{journal_filename_without_ext}_expense_treemap.png",
            format="png",
        )

        net_worth_treemap.write_image(
            f"{output_dir}/{journal_filename_without_ext}_net_worth_treemap."
            + "png",
            format="png",
        )
