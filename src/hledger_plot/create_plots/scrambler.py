import os
import random
from typing import Dict, List

import pandas as pd
from pandas.core.series import Series
from typeguard import typechecked

# vulture
pd.options.mode.copy_on_write = True


@typechecked
def load_words_from_file(*, filename: str) -> List[str]:
    """Loads a list of words from a given file.

    Args:
      filename: The path to the file containing the words.

    Returns:
      A list of words read from the file.
    """
    if not os.path.isfile(filename):
        raise FileNotFoundError(f"Did not find: {filename}")
    with open(filename) as f:
        words = f.read().splitlines()
    return sorted(list(set(words)))


@typechecked
def scramble_sankey_data(
    *,
    sankey_df: pd.DataFrame,
    random_words: List[str],
    top_level_categories: List[str],
    separator: str,
) -> pd.DataFrame:
    unique_atomic_categories = get_unique_atomic_categories(
        some_df_list=list(sankey_df["source"])
    )
    unique_atomic_categories = (
        unique_atomic_categories
        | get_unique_atomic_categories(some_df_list=list(sankey_df["target"]))
    )
    top_level_categories_copy = top_level_categories.copy() + [separator]
    for skipped_entry in top_level_categories_copy:
        if skipped_entry in unique_atomic_categories:
            unique_atomic_categories.remove(skipped_entry)

    scrambler_map: Dict[str, str] = map_original_to_randomized(
        random_words=random_words,
        original_list=sorted(list(unique_atomic_categories)),
    )

    # Randomize the dataframe column by column..
    sankey_df["source"] = scramble_df_column(
        scrambler_map=scrambler_map, some_col=sankey_df["source"]
    )
    sankey_df["target"] = scramble_df_column(
        scrambler_map=scrambler_map, some_col=sankey_df["target"]
    )
    sankey_df["value"] = randomize_list_order_magnitude(
        numbers=list(sankey_df["value"])
    )
    return sankey_df


@typechecked
def scramble_df_column(
    *, scrambler_map: Dict[str, str], some_col: Series
) -> Series:
    for i, entry in enumerate(some_col):
        atomic_categories: List[str] = entry.split(":")
        for j, atomic_category in enumerate(atomic_categories):

            if atomic_category in scrambler_map.keys():
                atomic_categories[j] = scrambler_map[atomic_category]

        some_col[i] = ":".join(atomic_categories)
    return some_col


@typechecked
def get_unique_atomic_categories(*, some_df_list: List[str]) -> set[str]:

    unique_atomic_categories: set[str] = set()
    for entry in some_df_list:
        atomic_categories: List[str] = entry.split(":")
        atomic_categories
        for atomic_category in atomic_categories:
            unique_atomic_categories.add(atomic_category)
    return unique_atomic_categories


@typechecked
def map_original_to_randomized(
    *, random_words: List[str], original_list: List[str]
) -> Dict[str, str]:
    """Creates a dictionary mapping elements of original_list to randomly
    selected words from random_words.

    Args:
    random_words: A list of words to be used for mapping.
    original_list: A list of elements to be mapped.

    Returns:
    A dictionary where keys are elements from original_list and values are
    randomly selected words from random_words.
    """
    shuffle_dict: Dict[str, str] = {}
    if len(random_words) < len(original_list):
        raise ValueError(
            f"Please provide more random words than:{len(original_list)}"
        )
    for category in original_list:

        # shuffle_dict[category]=random.choice(random_words) # No seed.
        shuffle_dict[category] = random_words[
            int(random.uniform(0, len(random_words)))  # nosec
        ]

    return shuffle_dict


@typechecked
def randomize_list_order_magnitude(numbers: List[float]) -> List[float]:
    """Randomizes a list of numbers while preserving the order and maintaining
    roughly the same magnitude.

    Args:
        numbers: The input list of numbers.

    Returns:
        A new list with the numbers randomized while preserving order
        and roughly maintaining magnitude.
    """

    # mean = sum(numbers) / len(numbers)
    multipliers = [
        random.uniform(0.11, 10.1) for _ in range(len(numbers))  # nosec
    ]
    return [
        round(num * multiplier, 2)
        for num, multiplier in zip(numbers, multipliers)
    ]
