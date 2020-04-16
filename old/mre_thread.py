import threading as th
import itertools
import pickle
import time
from queue import Queue

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


def populate_boards(q,hand1,hand2):
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


def get_board_and_score(queue,hand1,hand2,ranked_hands_dict):
    global n,one,two,lk
    while not queue.empty():
        board = queue.get()

        # print(f"Board = {board}")
        hand1rank = find_the_best_hand(board, hand1,ranked_hands_dict)
        hand2rank = find_the_best_hand(board, hand2,ranked_hands_dict)

        lk.acquire()
        if hand1rank > hand2rank:
            one += 1
        elif hand1rank < hand2rank:
            two += 1
        else:
            n += 1
        lk.release()


if __name__ == '__main__':

    tic = time.time()
    n = 0
    one = 0
    two = 0
    lk = th.Lock()

    q = Queue()

    with open(r'../hands.p', 'rb') as f:
        ranked_hands_dict = pickle.load(f)

    hand1 = {'2h', '7d'}
    hand2 = {'Ad', 'Ah'}

    p0 = th.Thread(target=populate_boards, args=(q, hand1, hand2))
    p0.start()
    threads = []

    for i in range(7):
        threads.append(th.Thread(target=get_board_and_score, args=(q, hand1, hand2, ranked_hands_dict)))
        threads[i].start()

    p0.join()

    for p in threads:
        p.join()

    print("Joined")
    print(n, one, two)
    toc = time.time()
    print(toc-tic)
