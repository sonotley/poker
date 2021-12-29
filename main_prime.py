import itertools
from ctypes import c_longlong
import time
import cardsutils
import json
from math import prod
import multiprocessing as mp
import threading as tr
from sys import argv
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
    

def find_best_score(board, hand, ranked_hands_dict):
    all_possible_hands = itertools.combinations(board | hand, 5)
    evaluated_all_possible_hands = [
        ranked_hands_dict[prod(hand)] for hand in all_possible_hands
    ]

    return max(evaluated_all_possible_hands)


def populate_boards(hand1, hand2, board=None):
    cards = {cardsutils.deck_dict_with_primes[x] for x in cardsutils.deck_as_set}
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


def get_board_and_score(ls, hand1, hand2, ranked_hands_dict, n, one, two, i):
    n_local = 0
    one_local = 0
    two_local = 0
    print(len(ls), "--", i)
    if PARALLELISM == "PROCESS":
        try:
            this_process = psutil.Process()
            this_process.cpu_affinity([i])

        except AttributeError:
            print("CPU affinity not supported")

    for board in ls:

        hand1rank = find_best_score(board, hand1, ranked_hands_dict)
        hand2rank = find_best_score(board, hand2, ranked_hands_dict)

        if hand1rank > hand2rank:
            one_local += 1
        elif hand1rank < hand2rank:
            two_local += 1
        else:
            n_local += 1

    with one.get_lock():
        one.value += one_local

    with two.get_lock():
        two.value += two_local

    with n.get_lock():
        n.value += n_local
    print(n_local, one_local, two_local, "--", i)


if __name__ == "__main__":

    print("Poker hand calculator, initialising...")

    draws = mp.Value(typecode_or_type=c_longlong)
    hand1Wins = mp.Value(typecode_or_type=c_longlong)
    hand2Wins = mp.Value(typecode_or_type=c_longlong)

    with open("hands_prime.json", "r") as f:
        ranked_hands_dict = {int(k): v for k, v in json.load(f).items()}

    hands = []
    flop = []
    board = None

    if len(argv) == 1:
        for hand in range(2):
            for card in range(2):
                valid_input = False
                while not valid_input:
                    c = input(f"Enter hand {hand}, card {card}: ")
                    try:
                        hands.append(cardsutils.deck_dict_with_primes[c])
                        valid_input = True
                    except KeyError:
                        print("Not a valid input")

        if input("Do you know the flop? ").lower() in ["y", "yes"]:
            for card in range(3):
                valid_input = False
                while not valid_input:
                    c = input(f"Enter flop card {card}: ")
                    try:
                        flop.append(cardsutils.deck_dict_with_primes[c])
                        valid_input = True
                    except KeyError:
                        print("Not a valid input")
            board = set(flop)

    elif len(argv) in (5, 8):
        [hands.append(cardsutils.deck_dict_with_primes[x]) for x in argv[1:]]

        if len(argv) == 8:
            [flop.append(cardsutils.deck_dict_with_primes[x]) for x in argv[5:7]]
            board = set(flop)
    else:
        raise IOError("Invalid number of arguments")

    hand1_primes = set(hands[:2])
    hand2_primes = set(hands[2:])

    tic = time.time()
    possible_boards = populate_boards(hand1_primes, hand2_primes, board)

    parallels = []
    if NUM_PARALLELS == 0 or parallel is None:
        get_board_and_score(
            possible_boards,
            hand1_primes,
            hand2_primes,
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
                        hand1_primes,
                        hand2_primes,
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
