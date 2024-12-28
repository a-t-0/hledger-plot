import subprocess  # nosec
from argparse import Namespace
from io import StringIO
from typing import List

import pandas as pd
from pandas.core.frame import DataFrame
from typeguard import typechecked


@typechecked
def read_balance_report(
    args: Namespace,
    filename: str,
    account_categories: str,
    top_level_account_categories: List[str],
) -> DataFrame:
    disp_currency: str = args.display_currency
    optional_balance_args = [
        # not:desc:opening: Excludes entries with descriptions containing the
        # word 'opening'.
        # If you only want the balance (changes) of this year, you want to
        # exclude opening statements because they carry over values from assets
        # of previous years.
        "not:desc:opening",
    ]

    required_exotic_args = [
        " --tree --no-elide",  # Ensures that parent accounts are listed even
        # if they dont have balance changes. Ensures Sankey flows don't have
        # gaps.
        # Not shown in CLI --help, but probably part of the [QUERY] segment:
        f"--cost --value=then,{disp_currency} --infer-value",  # Convert
        # everything to a single commodity, e.g. £,$, EUR etc.
    ]

    # read_balance_report--cost: Reads cost-related data in the balance report.
    default_command = (
        f"hledger -f {filename} balance {account_categories} --no-total"
        " --output-format csv"
        + " ".join(required_exotic_args)
    )

    # Call hledger to compute balances.
    if args.verbose:
        print(f"Ignoring options:{optional_balance_args}\n")
        print(f"default_command=:{default_command}\n")
    process_output = subprocess.run(  # nosec
        default_command.split(" "),
        stdout=subprocess.PIPE,
        text=True,
        # shell=False,
    ).stdout

    # Read the process output into a DataFrame, and clean it up, removing
    # headers.
    raw_df: DataFrame = pd.read_csv(StringIO(process_output), header=None)
    df: DataFrame = raw_df[
        raw_df[0].str.contains("|".join(top_level_account_categories))
    ]
    # Remove currency symbol from the balance values, and convert them to float.
    df[1] = df[1].str.replace(disp_currency, "")
    df[1] = df[1].str.replace(",", ".").astype(float)
    df[1] = pd.to_numeric(df[1], errors="coerce")
    return df
