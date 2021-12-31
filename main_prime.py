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
from os import environ

env_parallelism = environ.get("POKER_PARALLELISM")
env_num = environ.get("POKER_NUM_PARA")

PARALLELISM = "PROCESS" if env_parallelism is None else env_parallelism
NUM_PARALLELS = 0 if env_num is None else int(env_num)

if PARALLELISM == "PROCESS":
    try:
        import psutil
    except ImportError:
        psutil = None
    parallel = mp.Process
elif PARALLELISM == "THREAD":
    parallel = tr.Thread
else:
    parallel = None


def find_best_score(
    board: set[int], hand: set[int], ranked_hands_dict: dict[int, int]
) -> int:
    """Find the best scoring hand of five cards from a hand of two and board of five and return the score of that hand"""

    all_possible_hands = itertools.combinations(board | hand, 5)
    evaluated_all_possible_hands = [
        ranked_hands_dict[prod(hand)] for hand in all_possible_hands
    ]

    return max(evaluated_all_possible_hands)


def populate_boards(
    hand1: set[int], hand2: set[int], board: set[int] | None = None
) -> tuple[set[int], ...]:
    """Find all possible five-card boards given the known cards"""

    cards = set(cardsutils.fifty_two_primes)
    if board is None:
        deadcards = hand1 | hand2
        return tuple(set(x) for x in itertools.combinations(cards - deadcards, 5))
    elif len(board) < 5:
        deadcards = hand1 | hand2 | board
        return tuple(
            set(x).union(board)
            for x in itertools.combinations(cards - deadcards, 5 - len(board))
        )
    else:
        return (board,)


def get_board_and_score(
    possible_boards: tuple[set[int], ...],
    hand1: set[int],
    hand2: set[int],
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
    print(len(possible_boards), "--", parallelism_index)
    if PARALLELISM == "PROCESS":
        try:
            this_process = psutil.Process()
            this_process.cpu_affinity([parallelism_index])

        except AttributeError:
            print("CPU affinity not supported")

    for board in possible_boards:

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


if __name__ == "__main__":

    print("Poker hand calculator, initialising...")

    draws = mp.Value(typecode_or_type=c_longlong)
    hand1Wins = mp.Value(typecode_or_type=c_longlong)
    hand2Wins = mp.Value(typecode_or_type=c_longlong)

    with open("hands_prime.json", "r") as f:
        ranked_hands_dict = {int(k): v for k, v in json.load(f).items()}

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--hand1", "-h1", help="Cards in hand one as a string", type=str
    )
    parser.add_argument(
        "--hand2", "-h2", help="Cards in hand one as a string", type=str, default=None
    )
    parser.add_argument(
        "--board",
        "-b",
        help="Cards in the flop and optionally turn and river",
        type=str,
        default=None,
    )

    args = parser.parse_args()

    hand1 = (
        cardsutils.extract_cards_from_string(args.hand1)
        if args.hand1 is not None
        else None
    )
    hand2 = (
        cardsutils.extract_cards_from_string(args.hand2)
        if args.hand2 is not None
        else None
    )
    board = (
        cardsutils.extract_cards_from_string(args.board)
        if args.board is not None
        else None
    )

    tic = time.time()
    possible_boards = populate_boards(hand1, hand2, board)

    parallels = []
    if NUM_PARALLELS == 0 or parallel is None:
        get_board_and_score(
            possible_boards,
            hand1,
            hand2,
            ranked_hands_dict,
            draws,
            hand1Wins,
            hand2Wins,
            0,
        )
    else:
        for i in range(NUM_PARALLELS):
            parallels.append(
                parallel(
                    target=get_board_and_score,
                    args=(
                        possible_boards[i::NUM_PARALLELS],
                        hand1,
                        hand2,
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
    print(draws.value, hand1Wins.value, hand2Wins.value)
    total = draws.value + hand1Wins.value + hand2Wins.value
    print(
        f"Draw: {draws.value/total}",
        f"Hand 1: {hand1Wins.value / total}",
        f"Hand 2: {hand2Wins.value/total}",
        sep="\n",
    )
    toc = time.time()
    print(toc - tic)
