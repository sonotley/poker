import multiprocessing as mp
import itertools
import pickle
from ctypes import c_longlong
import time
import psutil


def find_best_score(board, hand, ranked_hands_dict):
    seven_card_hand = set(board) | hand
    evaluated_all_possible_hands = []

    all_possible_hands = itertools.combinations(seven_card_hand, 5)
    for hand in all_possible_hands:
        evaluated_all_possible_hands.append(ranked_hands_dict[tuple(sorted(hand))])

    return max(evaluated_all_possible_hands)


def populate_boards(hand1, hand2):
    ranks = ['2', '3', '4', '5', '6', '7', '8', '9', 'T', 'J', 'Q', 'K', 'A']
    suits = ['h', 's', 'd', 'c']
    cards = set()
    for suit in suits:
        for rank in ranks:
            cards.add(rank + suit)

    deadcards = hand1 | hand2

    return tuple(itertools.combinations(cards - deadcards, 5))


def get_board_and_score(ls, hand1, hand2, ranked_hands_dict, n, one, two, i):
    n_local = 0
    one_local = 0
    two_local = 0
    print(len(ls),'--',i)
    this_process = psutil.Process()
    try:
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
    print(n_local, one_local, two_local,"--",i)


if __name__ == '__main__':

    tic = time.time()
    draws = mp.Value(typecode_or_type=c_longlong)
    hand1Wins = mp.Value(typecode_or_type=c_longlong)
    hand2Wins = mp.Value(typecode_or_type=c_longlong)

    with open(r'hands.p', 'rb') as f:
        ranked_hands_dict = pickle.load(f)

    hand1 = {'2h', '7d'}
    hand2 = {'Ad', '3h'}

    possible_boards = populate_boards(hand1, hand2)

    processes = []
    num_processes = 4
    if num_processes == 0:
        get_board_and_score(possible_boards,hand1,hand2,ranked_hands_dict, draws, hand1Wins, hand2Wins, 0)
    else:
        for i in range(num_processes):
            processes.append(mp.Process(target=get_board_and_score,
                                        args=(possible_boards[i::num_processes], hand1, hand2, ranked_hands_dict, draws, hand1Wins, hand2Wins, i)))
            processes[i].start()

        for p in processes:
            p.join()

        print("Joined")
    print(draws.value, hand1Wins.value, hand2Wins.value)
    toc = time.time()
    print(toc - tic)
