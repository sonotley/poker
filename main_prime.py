from __future__ import annotations

import itertools
from ctypes import c_longlong
import time
import cardsutils
import json
from math import prod
import multiprocessing as mp
from multiprocessing.sharedctypes import Synchronized
import threading as tr
import argparse

try:
    import psutil
except ImportError:
    psutil = None


def find_best_score(
    board: set[int], hand: set[int], ranked_hands_dict: dict[int, int]
) -> int:
    """Find the best scoring hand of five cards from a hand of two and board of five and return the score of that hand"""

    all_possible_hands = itertools.combinations(board | hand, 5)
    evaluated_all_possible_hands = [
        ranked_hands_dict[prod(hand)] for hand in all_possible_hands
    ]

    return max(evaluated_all_possible_hands)


def get_possible_boards(
    hand1: set[int], hand2: set[int], board: set[int]
) -> tuple[set[int], ...]:
    """Find all possible five-card boards given the known cards"""

    cards = set(cardsutils.fifty_two_primes)
    deadcards = hand1 | hand2 | board

    return tuple(
        set(x).union(board)
        for x in itertools.combinations(cards - deadcards, 5 - len(board))
    )


def get_possible_hands_and_boards(
    hand1: set[int], hand2: set[int], board: set[int]
) -> tuple[tuple[set[int], ...], ...]:
    """Find all possible hand2 and board combinations given the known cards"""

    cards = set(cardsutils.fifty_two_primes)
    possible_combinations = []
    possible_boards = get_possible_boards(hand1, hand2, board)
    for possible_board in possible_boards:
        deadcards = hand1 | hand2 | possible_board
        possible_hands = [
            set(x).union(hand2)
            for x in itertools.combinations(cards - deadcards, 2 - len(hand2))
        ]
        possible_combinations.extend(
            zip(possible_hands, (possible_board,) * len(possible_hands))
        )
    return tuple(possible_combinations)


def get_board_and_score(
    hand1: set[int],
    possible_hands_and_boards: tuple[tuple[set[int], ...], ...],
    ranked_hands_dict: dict[int, int],
    draw_counter: Synchronized,
    hand1_win_counter: Synchronized,
    hand2_win_counter: Synchronized,
    parallelism_index: int,
) -> None:
    """Determine result for given hands for all possible boards and update counters accordingly"""

    draw_local = 0
    one_local = 0
    two_local = 0
    print(len(possible_hands_and_boards), "--", parallelism_index)

    try:
        this_process = psutil.Process()
        this_process.cpu_affinity([parallelism_index])
    except AttributeError:
        print("CPU affinity not supported")

    for hand2, board in possible_hands_and_boards:

        hand1rank = find_best_score(board, hand1, ranked_hands_dict)
        hand2rank = find_best_score(board, hand2, ranked_hands_dict)

        if hand1rank > hand2rank:
            one_local += 1
        elif hand1rank < hand2rank:
            two_local += 1
        else:
            draw_local += 1

    with hand1_win_counter.get_lock():
        hand1_win_counter.value += one_local

    with hand2_win_counter.get_lock():
        hand2_win_counter.value += two_local

    with draw_counter.get_lock():
        draw_counter.value += draw_local
    print(draw_local, one_local, two_local, "--", parallelism_index)


def calculate_probabilities(
    hand1: set[int],
    hand2: set[int] | None,
    board: set[int] | None,
    num_parallels: int = 0,
    process_parallelism: bool = True,
):
    draws = mp.Value(typecode_or_type=c_longlong)
    hand1Wins = mp.Value(typecode_or_type=c_longlong)
    hand2Wins = mp.Value(typecode_or_type=c_longlong)

    possible_hands_and_boards = get_possible_hands_and_boards(hand1, hand2, board)

    if num_parallels == 0:
        get_board_and_score(
            hand1,
            possible_hands_and_boards,
            ranked_hands_dict,
            draws,
            hand1Wins,
            hand2Wins,
            0,
        )
    else:
        parallels = []
        parallel = mp.Process if process_parallelism else tr.Thread
        for i in range(num_parallels):
            parallels.append(
                parallel(
                    target=get_board_and_score,
                    args=(
                        hand1,
                        possible_hands_and_boards[i::num_parallels],
                        ranked_hands_dict,
                        draws,
                        hand1Wins,
                        hand2Wins,
                        i,
                    ),
                )
            )
            parallels[i].start()

        for p in parallels:
            p.join()

        print("Joined")

    return draws.value, hand1Wins.value, hand2Wins.value


def load_ranked_hands_dict(filepath: str = "hands_prime.json"):
    with open(filepath, "r") as f:
        return {int(k): v for k, v in json.load(f).items()}


def get_arg_parser():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--hand1", "-h1", help="Cards in hand one as a string", type=str, default=None
    )
    parser.add_argument(
        "--hand2", "-h2", help="Cards in hand one as a string", type=str, default=set()
    )
    parser.add_argument(
        "--board",
        "-b",
        help="Cards in the flop and optionally turn and river",
        type=str,
        default=set(),
    )
    parser.add_argument(
        "--num-parallels",
        "-n",
        help="Number of parallel processing entities (0 means no parallelism)",
        type=int,
        default=0,
    )

    parser.add_argument(
        "--thread-parallelism",
        "-t",
        help="Use thread rather than process parallelism",
        type=bool,
        default=False,
    )

    return parser


if __name__ == "__main__":

    print("Poker hand calculator, initialising...")
    ranked_hands_dict = load_ranked_hands_dict()
    print("Initialisation complete")

    parser = get_arg_parser()
    args = parser.parse_args()

    first_run = True
    interactive = True if not args.hand1 else False

    while interactive or first_run:
        if interactive:
            raw_args = input("Running in interactive mode, please enter your arguments: ")
            args = parser.parse_args(raw_args.split())

        hand1, hand2, board = [cardsutils.extract_cards_from_string(x) for x in (args.hand1, args.hand2, args.board)]

        tic = time.time()
        draws, hand1_wins, hand2_wins = calculate_probabilities(
            hand1,
            hand2,
            board,
            num_parallels=args.num_parallels,
            process_parallelism=(not args.thread_parallelism),
        )
        toc = time.time()
        print(f"Calculation complete in {toc - tic:.1f} seconds")

        print(draws, hand1_wins, hand2_wins)
        total = draws + hand1_wins + hand2_wins
        print(
            f"Draw: {draws / total}",
            f"Hand 1: {hand1_wins / total}",
            f"Hand 2: {hand2_wins / total}",
            sep="\n",
        )
        first_run = False
