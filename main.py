from __future__ import annotations

import itertools
import queue
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


# todo: this could probably be optimised by using itertools more rather than looping
def get_possible_hands_and_boards(
    hand1: set[int], hand2: set[int], board: set[int]
) -> tuple[tuple[set[int], ...], ...]:
    """Find all possible hand2 and board combinations given the known cards"""

    cards = set(cardsutils.fifty_two_primes)
    possible_combinations = []
    possible_boards = get_possible_boards(hand1, hand2, board)
    if len(hand2) == 2:
        possible_combinations = zip((hand2,) * len(possible_boards), possible_boards)
    else:
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


def evaluate_hand(
    hand1: set[int],
    possible_hands_and_boards: tuple[tuple[set[int], ...], ...],
    ranked_hands_dict: dict[int, int],
) -> tuple[int, int, int]:
    """Determine result for given hand for all possible boards and opposing hands, and update counters accordingly"""

    draw_local = 0
    one_local = 0
    two_local = 0

    for hand2, board in possible_hands_and_boards:
        hand1rank = find_best_score(board, hand1, ranked_hands_dict)
        hand2rank = find_best_score(board, hand2, ranked_hands_dict)

        if hand1rank > hand2rank:
            one_local += 1
        elif hand1rank < hand2rank:
            two_local += 1
        else:
            draw_local += 1

    return draw_local, one_local, two_local


def evaluate_hand__counters(
    hand1: set[int],
    possible_hands_and_boards: tuple[tuple[set[int], ...], ...],
    ranked_hands_dict: dict[int, int],
    draw_counter: Synchronized,
    hand1_win_counter: Synchronized,
    hand2_win_counter: Synchronized,
    parallelism_index: int,
) -> None:
    print(len(possible_hands_and_boards), "--", parallelism_index)
    try:
        this_process = psutil.Process()
        this_process.cpu_affinity([parallelism_index])
    except AttributeError:
        print("CPU affinity not supported")

    draw_local, one_local, two_local = evaluate_hand(hand1, possible_hands_and_boards, ranked_hands_dict)

    with hand1_win_counter.get_lock():
        hand1_win_counter.value += one_local

    with hand2_win_counter.get_lock():
        hand2_win_counter.value += two_local

    with draw_counter.get_lock():
        draw_counter.value += draw_local
    print(draw_local, one_local, two_local, "--", parallelism_index)


def evaluate_hand__queues(
    in_queue: mp.Queue | queue.Queue,
    out_queue: mp.Queue | queue.Queue,
    ranked_hands_dict: dict[int, int],
    parallelism_index: int,
) -> None:

    try:
        this_process = psutil.Process()
        this_process.cpu_affinity([parallelism_index])
    except AttributeError:
        # print("CPU affinity not supported")
        ...

    while True:
        hand1, possible_hands_and_boards = in_queue.get()
        print(len(possible_hands_and_boards), "--", parallelism_index)
        draw_local, one_local, two_local = evaluate_hand(hand1, possible_hands_and_boards, ranked_hands_dict)
        print(draw_local, one_local, two_local, "--", parallelism_index)
        out_queue.put((draw_local, one_local, two_local))


def initialise_workers(ranked_hands_dict: dict[int, int], num_parallels: int, process_parallelism: bool):
    if process_parallelism:
        para = mp.Process
        q = mp.Queue
    else:
        para = tr.Thread
        q = queue.Queue

    in_queue = q()
    out_queue = q()

    workers = [para(target=evaluate_hand__queues, args=(in_queue, out_queue, ranked_hands_dict, x)) for x in range(num_parallels)]
    [worker.start() for worker in workers]

    return in_queue, out_queue, workers


def calculate_probabilities(
    hand1: set[int],
    hand2: set[int] | None,
    board: set[int] | None,
    ranked_hands_dict: dict,
    num_parallels: int = 0,
    process_parallelism: bool = True,
):
    draws = mp.Value(typecode_or_type=c_longlong)
    hand1_wins = mp.Value(typecode_or_type=c_longlong)
    hand2_wins = mp.Value(typecode_or_type=c_longlong)

    possible_hands_and_boards = get_possible_hands_and_boards(hand1, hand2, board)

    if num_parallels == 0:
        evaluate_hand__counters(
            hand1,
            possible_hands_and_boards,
            ranked_hands_dict,
            draws,
            hand1_wins,
            hand2_wins,
            0,
        )
    else:
        parallels = []
        parallel = mp.Process if process_parallelism else tr.Thread
        for i in range(num_parallels):
            parallels.append(
                parallel(
                    target=evaluate_hand__counters,
                    args=(
                        hand1,
                        possible_hands_and_boards[i::num_parallels],
                        ranked_hands_dict,
                        draws,
                        hand1_wins,
                        hand2_wins,
                        i,
                    ),
                )
            )
            parallels[i].start()

        for p in parallels:
            p.join()

        print("Joined")

    return draws.value, hand1_wins.value, hand2_wins.value


def calculate_probabilities__workers(
    hand1: set[int],
    hand2: set[int] | None,
    board: set[int] | None,
    num_parallels: int,
    in_queue: mp.Queue | queue.Queue,
    out_queue: mp.Queue | queue.Queue,
):
    # This step is really slow on M1 CPython - I guess itertools hasn't been optimised for ARM yet?
    possible_hands_and_boards = get_possible_hands_and_boards(hand1, hand2, board)
    [in_queue.put((hand1, possible_hands_and_boards[i::num_parallels])) for i in range(num_parallels)]
    results = [out_queue.get() for x in range(num_parallels)]

    return tuple(sum(x) for x in tuple(zip(*results)))


def load_ranked_hands_dict(filepath: str = "hands_prime.json"):
    with open(filepath, "r") as f:
        return {int(k): v for k, v in json.load(f).items()}


def get_arg_parser():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--hand1", "-h1", help="Cards in hand one as a string", type=str, default=None
    )
    parser.add_argument(
        "--hand2", "-h2", help="Cards in hand two as a string", type=str, default=set()
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

    parser.add_argument(
        "--force-no-workers",
        "-f",
        help="Force use of old-school method without pre-heated workers",
        action=argparse.BooleanOptionalAction,
        default=False,
    )

    return parser


if __name__ == "__main__":

    print("Poker hand calculator, initialising...")
    ranked_hands_dict = load_ranked_hands_dict()
    print("Loaded hand ranks")

    parser = get_arg_parser()
    args = parser.parse_args()

    num_parallels = args.num_parallels
    process_parallelism = (not args.thread_parallelism)

    if num_parallels > 0 and not args.force_no_workers:
        in_queue, out_queue, workers = initialise_workers(ranked_hands_dict, num_parallels, process_parallelism)
    print(f"Initialised {num_parallels} workers")

    first_run = True
    interactive = True if not args.hand1 else False

    while interactive or first_run:
        if interactive:
            raw_args = input("Running in interactive mode, please enter your arguments: ")
            args = parser.parse_args(raw_args.split())

        hand1, hand2, board = [cardsutils.extract_cards_from_string(x) for x in (args.hand1, args.hand2, args.board)]

        tic = time.time()
        if num_parallels == 0 or args.force_no_workers:
            draws, hand1_wins, hand2_wins = calculate_probabilities(
                hand1,
                hand2,
                board,
                ranked_hands_dict,
                num_parallels=args.num_parallels,
                process_parallelism=(not args.thread_parallelism),
            )
        else:
            draws, hand1_wins, hand2_wins = calculate_probabilities__workers(hand1, hand2, board, num_parallels, in_queue, out_queue)
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
