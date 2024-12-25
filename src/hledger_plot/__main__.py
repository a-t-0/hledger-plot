"""Entry point for the project."""

from typing import Any, List

from typeguard import typechecked

from hledger_plot.arg_parser import create_arg_parser, verify_args
from hledger_plot.create_plots.manage_plotting import manage_plotting
from hledger_plot.create_plots.scrambler import load_words_from_file
from hledger_plot.HledgerCategories import HledgerCategories
from hledger_plot.journal_parsing.get_top_level_domains import (
    get_top_level_account_categories,
)


@typechecked
def main() -> None:
    # For the Sankey diagram,  top-level accounts need to be connected to the
    #  special bucket that divides input from output. The name for this bucket
    # is randomly chosen to be: BALANCE-LINE.
    separator: str = "BALANCE-LINE"
    parser = create_arg_parser()

    args: Any = verify_args(parser=parser)
    hledgerCategories: HledgerCategories = HledgerCategories.from_args(
        args=args
    )
    random_wordlist_filename: str = "random_categories.txt"

    random_words = load_words_from_file(filename=random_wordlist_filename)

    if args.journal_filepath:
        top_level_account_categories: List[str] = (
            get_top_level_account_categories(
                journal_filepath=args.journal_filepath
            )
        )
        print(
            "The top_level_account_categories found in your journals"
            f" are:\n{top_level_account_categories}"
        )
        manage_plotting(
            args=args,
            journal_filepath=args.journal_filepath,
            top_level_account_categories=top_level_account_categories,
            hledgerCategories=hledgerCategories,
            random_words=random_words,
            separator=separator,
        )
        exit()
