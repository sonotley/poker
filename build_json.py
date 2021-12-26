import itertools
import time
import json
import cardsutils
import math

# Function dict_hand_rank ranks every board and returns a tuple (board) (value)
def hand_rank_dict(hand, use_prime_key=False):

    suits = []
    ranks_alphabetical = []
    ranks_numerical = []
    ranks_histogram = []
    ranks = cardsutils.ranks

    is_flush = False
    is_straight = False
    handrank_value = 0
    straight_height = -1

    for card in hand:
        suits.append(card[1])
        ranks_alphabetical.append(card[0])

    # create ranks_histogram where from A 2 ... J Q K A every card has the corresponding number of occurencies, A double counted
    ranks_histogram.append(str(ranks_alphabetical.count("A")))

    for rank in ranks:
        ranks_histogram.append(str(ranks_alphabetical.count(rank)))

    joined_histogram = "".join(ranks_histogram)

    # create ranks numerical instead of T, J, Q, K
    for card in hand:
        ranks_numerical.append(cardsutils.ranks_map[card[0]])

    # create kickers
    kickers = sorted(
        [x for x in ranks_numerical if ranks_numerical.count(x) < 2], reverse=True
    )

    # check if a hand is a straight
    if "11111" in joined_histogram:
        is_straight = True
        straight_height = joined_histogram.find("11111") + 5
        handrank_value = (4,) + (straight_height,)

    # check if a hand is a flush
    if all(x == suits[0] for x in suits):
        is_flush = True
        handrank_value = (5,) + tuple(kickers)

    # check if a hand is a straight and a flush
    if is_flush & is_straight:
        handrank_value = (8,) + (straight_height,)

    # check if a hand is four of a kind
    if "4" in joined_histogram:
        handrank_value = (7,) + ((joined_histogram[1:].find("4") + 2),) + tuple(kickers)

    # check if a hand is a full house
    if ("3" in joined_histogram) & ("2" in joined_histogram):
        handrank_value = (
            (6,)
            + ((joined_histogram[1:].find("3") + 2),)
            + ((joined_histogram[1:].find("2") + 2),)
            + tuple(kickers)
        )

    # check if a hand is three of a kind
    if ("3" in joined_histogram) & (len(kickers) == 2):
        handrank_value = (3,) + ((joined_histogram[1:].find("3") + 2),) + tuple(kickers)

    # check if a hand is two pairs
    if ("2" in joined_histogram) & (len(kickers) == 1):
        lowerpair = joined_histogram[1:].find("2") + 2
        higherpair = joined_histogram[lowerpair:].find("2") + 1 + lowerpair
        handrank_value = (2,) + (higherpair, lowerpair) + tuple(kickers)

    # check if a hand is one pair
    if ("2" in joined_histogram) & (len(kickers) == 3):
        lowerpair = joined_histogram[1:].find("2") + 2
        handrank_value = (1,) + (lowerpair,) + tuple(kickers)

    # evaluate high card hand
    if (
        (len(ranks_numerical) == len(set(ranks_numerical)))
        & (is_straight == False)
        & (is_flush == False)
    ):
        handrank_value = (0,) + tuple(kickers)

    if use_prime_key:
        return {
            math.prod(
                [cardsutils.deck_dict_with_primes[x] for x in hand]
            ): rank_integer(handrank_value)
        }
    else:
        return {"".join(sorted(hand)): rank_integer(handrank_value)}


def build_hands_dict(deck, path, use_prime_key=False):

    ranked_hands_dict = {}
    t0 = time.time()
    for five_card_hand in itertools.combinations(deck, 5):
        ranked_hands_dict.update(hand_rank_dict(five_card_hand, use_prime_key))
    t1 = time.time()
    total = t1 - t0
    print(total)
    with open(path, "w") as f:
        json.dump(ranked_hands_dict, f)


def rank_integer(rank_tuple):
    m = 100 ** 5
    score = 0
    for x in rank_tuple:
        score += x * m
        m /= 100

    return int(score)


build_hands_dict(cardsutils.deck_as_set, r"hands_prime.json", use_prime_key=True)
