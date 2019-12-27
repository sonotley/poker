import itertools
import time
import pickle
import multiprocessing as mp

# Function that given board and 2 cards gives back tuple of the best possible hand by searching through ranked_hands_dict keys
def find_the_best_hand(board, hand, ranked_hands_dict):

    seven_card_hand = set(board) | hand
    evaluated_all_possible_hands = []

    all_possible_hands = itertools.combinations(seven_card_hand, 5)
    for hand in all_possible_hands:
        evaluated_all_possible_hands.append(ranked_hands_dict[tuple(sorted(hand))])

    return max(evaluated_all_possible_hands)


def get_board_and_score(queue,hand1,hand2,out_queue,ranked_hands_dict):
    print("Doing")
    while not queue.empty():
        board = queue.get(timeout=1)
        print(f"Board = {board}")
        hand1rank = find_the_best_hand(board, hand1,ranked_hands_dict)
        hand2rank = find_the_best_hand(board, hand2,ranked_hands_dict)

        if hand1rank > hand2rank:
            out_queue.put(1)
        elif hand1rank < hand2rank:
            out_queue.put(2)
        else:
            out_queue.put(0)
    print("Done")



if __name__ == '__main__':
    ranks = ['2','3','4','5','6','7','8','9','T','J','Q','K','A']
    suits = ['h','s','d','c']
    cards = set()

    # Create all cards from suits and ranks
    for suit in suits:
        for rank in ranks:
            cards.add(rank + suit)

    with open(r'hands.p','rb') as f:
        ranked_hands_dict = pickle.load(f)

    hand1 = {'2h', '7d'}
    hand2 = {'Ad', 'Ah'}

    # HAND vs. HAND EVALUATOR

    t0 = time.time()

    one = 0
    two = 0
    tie = 0
    q2 = mp.Queue()
    q = mp.Queue()
    n = 0
    processes=[]

    deadcards = hand1 | hand2
    possible_boards = itertools.combinations(cards - deadcards, 5)
    for pb in possible_boards:
        q.put(pb)

    print(q.qsize())

    # for i in range(1):
    #     processes.append(mp.Process(target=get_board_and_score,args=(q,hand1,hand2,q2,ranked_hands_dict)))
    #     processes[i].start()
    #     print("Started process", i)
    #
    # for process in processes:
    #     process.join()
    #     print("joined process")

    p = mp.Process(target=get_board_and_score,args=(q,hand1,hand2,q2,ranked_hands_dict),daemon=True)
    p.start()
    p.join()

    # onepercent = (one/n)*100
    # twopercent = (two/n)*100
    # tiepercent = (tie/n)*100
    #
    # print(onepercent, twopercent, tiepercent)

    t1 = time.time()
    total = t1-t0
    print(total)