import os
import random
from pprint import pprint
from typing import Dict, List, Union

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
    text_column_headers: List[Union[str, int]],
    numeric_column_headers: List[Union[str, int]],
) -> pd.DataFrame:
    unique_atomic_categories = set()

    for text_column_header in text_column_headers:
        unique_atomic_categories.update(
            get_unique_atomic_categories(
                some_df_list=list(sankey_df[text_column_header])
            )
        )
    top_level_categories_copy = top_level_categories.copy() + [separator]
    for skipped_entry in top_level_categories_copy:
        if skipped_entry in unique_atomic_categories:
            unique_atomic_categories.remove(skipped_entry)

    scrambler_map: Dict[str, str] = map_original_to_randomized(
        random_words=random_words,
        original_list=sorted(list(unique_atomic_categories)),
    )
    pprint(scrambler_map)
    if len(set(scrambler_map.keys())) != len(scrambler_map.keys()):
        raise ValueError("Found dupes in randomization.")
    if len(set(scrambler_map.values())) != len(scrambler_map.values()):
        raise ValueError("Found dupes in randomization values.")

    # Randomize the dataframe column by column.
    for text_column_header in text_column_headers:
        sankey_df[text_column_header] = scramble_df_column(
            scrambler_map=scrambler_map, some_col=sankey_df[text_column_header]
        )
    for numeric_column_header in numeric_column_headers:
        sankey_df[numeric_column_header] = randomize_list_order_magnitude(
            numbers=list(sankey_df[numeric_column_header]),
            lower=0.12,
            upper=10.2,
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

        some_col[i + 1] = ":".join(atomic_categories)

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
    used_words = set()
    if len(random_words) < len(original_list):
        raise ValueError(
            f"Please provide more random words than:{len(original_list)}"
        )

    for category, random_words in shuffle_dict.items():
        while True:
            random_index = int(random.uniform(0, len(random_words)))  # nosec
            selected_word = random_words[random_index]
            if selected_word not in used_words:
                shuffle_dict[category] = selected_word
                used_words.add(selected_word)
                break

    return shuffle_dict


def determine_magnitude_sequence(lst):
    """Determines the relative magnitude sequence of a list of numbers.

    Args:
      lst: A list of numbers.

    Returns:
      A list of integers representing the relative magnitudes of the numbers
      in the input list.
    """

    # Normalize the list to have a maximum value of 1.
    max_val = max(abs(x) for x in lst)
    normalized_lst = [x / max_val for x in lst]

    # Determine the rank of each element.
    ranked_lst = sorted(
        range(len(normalized_lst)), key=lambda k: normalized_lst[k]
    )

    # Assign a relative magnitude to each element based on its rank.
    magnitude_sequence = [i for i, _ in enumerate(ranked_lst)]

    return magnitude_sequence


def randomize_list_order_magnitude1(numbers: List[float]) -> List[float]:
    """Generates a list of numbers with the specified relative magnitude
    sequence.

    Args:
      desired_sequence: A list of integers representing the desired order of
                        magnitudes (e.g., [4, 1, 2, 0, 3]).
      some_min: The minimum value for the generated numbers.
      some_max: The maximum value for the generated numbers.

    Returns:
      A list of numbers with the specified relative magnitude sequence.
    """
    desired_sequence: List[int] = determine_magnitude_sequence(lst=numbers)
    # Normalize the desired_sequence to a range between 0 and 1.
    max_seq = max(desired_sequence)
    normalized_seq = [float(x) / max_seq for x in desired_sequence]

    # Generate random numbers within the normalized range.
    random_values = [
        random.random() * normalized_seq[i]
        for i in range(len(desired_sequence))
    ]

    # Scale the random numbers to the desired range.
    scaled_values = [
        (max(numbers) - min(numbers)) * x + min(numbers) for x in random_values
    ]

    # Introduce random sign (positive or negative) for each number.
    #   numbers = [random.choice([-1, 1]) * x for x in scaled_values]

    return scaled_values


@typechecked
def randomize_list_order_magnitude(
    numbers: List[float], lower: float, upper: float
) -> List[float]:
    """Randomizes a list of numbers while preserving the order and maintaining
    roughly the same magnitude.

    Args:
        numbers: The input list of numbers.

    Returns:
        A new list with the numbers randomized while preserving order
        and roughly maintaining majgnitude.
    """

    # mean = sum(numbers) / len(numbers)
    multipliers = sorted(
        [random.uniform(lower, upper) for _ in range(len(numbers))]  # nosec
    )

    output_nrs: List[float] = [
        round(num * multiplier, 2)
        for num, multiplier in zip(numbers, multipliers)
    ]
    return output_nrs
