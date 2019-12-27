import multiprocessing as mp
import itertools
import pickle
from ctypes import c_longlong
import time


def get_print(q):
    while True:
        a = q.get(timeout=1)
        print(a)


def find_the_best_hand(board, hand, ranked_hands_dict):
    seven_card_hand = set(board) | hand
    evaluated_all_possible_hands = []

    all_possible_hands = itertools.combinations(seven_card_hand, 5)
    for hand in all_possible_hands:
        evaluated_all_possible_hands.append(ranked_hands_dict[tuple(sorted(hand))])

    return max(evaluated_all_possible_hands)


def populate_boards(q, hand1, hand2):
    ranks = ['2', '3', '4', '5', '6', '7', '8', '9', 'T', 'J', 'Q', 'K', 'A']
    suits = ['h', 's', 'd', 'c']
    cards = set()
    for suit in suits:
        for rank in ranks:
            cards.add(rank + suit)

    deadcards = hand1 | hand2

    possible_boards = itertools.combinations(cards - deadcards, 5)
    for pb in possible_boards:
        q.put(pb)

    # poison pills here
    for i in range(8):
        q.put('STOP')


def populate_boards2(hand1, hand2):
    ranks = ['2', '3', '4', '5', '6', '7', '8', '9', 'T', 'J', 'Q', 'K', 'A']
    suits = ['h', 's', 'd', 'c']
    cards = set()
    for suit in suits:
        for rank in ranks:
            cards.add(rank + suit)

    deadcards = hand1 | hand2

    return tuple(itertools.combinations(cards - deadcards, 5))


def get_board_and_score(queue, hand1, hand2, ranked_hands_dict, n, one, two):
    n_local = 0
    one_local = 0
    two_local = 0

    while True:
        board = queue.get()
        if board != 'STOP':
            # print(f"Board = {board}")
            hand1rank = find_the_best_hand(board, hand1, ranked_hands_dict)
            hand2rank = find_the_best_hand(board, hand2, ranked_hands_dict)

            if hand1rank > hand2rank:
                one_local += 1
            elif hand1rank < hand2rank:
                two_local += 1
            else:
                n_local += 1
        else:
            break

    with one.get_lock():
        one.value += one_local

    with two.get_lock():
        two.value += two_local

    with n.get_lock():
        n.value += n_local


def get_board_and_score2(ls, hand1, hand2, ranked_hands_dict, n, one, two,i):
    n_local = 0
    one_local = 0
    two_local = 0
    print(len(ls),'--',i)

    for board in ls:

        hand1rank = find_the_best_hand(board, hand1, ranked_hands_dict)
        hand2rank = find_the_best_hand(board, hand2, ranked_hands_dict)

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
    print(n_local,one_local,two_local,"--",i)


if __name__ == '__main__':

    tic = time.time()
    n = mp.Value(typecode_or_type=c_longlong)
    one = mp.Value(typecode_or_type=c_longlong)
    two = mp.Value(typecode_or_type=c_longlong)

    with open(r'hands.p', 'rb') as f:
        ranked_hands_dict = pickle.load(f)

    hand1 = {'2h', '7d'}
    hand2 = {'Ad', 'Ah'}

    possible_boards = populate_boards2(hand1, hand2)
    print(len(possible_boards))

    processes = []
    num_processes = 4
    for i in range(num_processes):
        processes.append(mp.Process(target=get_board_and_score2,
                                    args=(possible_boards[i::num_processes], hand1, hand2, ranked_hands_dict, n, one, two,i)))
        processes[i].start()

    for p in processes:
        p.join()

    print("Joined")
    print(n.value, one.value, two.value)
    toc = time.time()
    print(toc - tic)
