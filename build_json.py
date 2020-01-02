import itertools
import time
import json

ranks = ['2','3','4','5','6','7','8','9','T','J','Q','K','A']
names ="Deuces Threes Fours Fives Sixes Sevens Eights Nines Tens Jacks Queens Kings Aces"
cardnames = names.split()
suitsall = "hearts spades diamonds clubs"
suitnames = suitsall.split()
suits = ['h','s','d','c']
cards = set()

# Create all cards from suits and ranks
for suit in suits:
    for rank in ranks:
        cards.add(rank + suit)


# Function dict_hand_rank ranks every board and returns a tuple (board) (value)
def hand_rank_dict(hand):

    suits = []
    ranks_alphabetical = []
    ranks_numerical = []
    ranks_histogram = []
    kickers = []
    kickers_text = []

    isFlush = False
    isStraight = False
    isStraightFlush = False
    handrankValue = 0

    straightHeight = -1
    straightName = "No straight"
    handName = "none yet"

    for card in hand:
        suits.append(card[1])
        ranks_alphabetical.append(card[0])

    # create ranks_histogram where from A 2 ... J Q K A every card has the corresponding number of occurencies, A double counted

    ranks_histogram.append(str(ranks_alphabetical.count('A')))

    for rank in ranks:
        ranks_histogram.append(str(ranks_alphabetical.count(rank)))

    joined_histogram = ''.join(ranks_histogram)

    # create ranks numerical instead of T, J, Q, K A

    for card in hand:
        ranks_numerical.append(ranks.index(card[0])+2)

    # create kickers

    kickers = sorted([x for x in ranks_numerical if ranks_numerical.count(x) <2], reverse = True)

    # check if a hand is a straight

    if '11111' in joined_histogram:
        isStraight = True
        straightHeight = joined_histogram.find('11111') + 5
        straightName = cardnames[straightHeight - 2]
        handName = "Straight"
        handrankValue = (4,) + (straightHeight,)

    # check if a hand is a flush

    if all(x == suits[0] for x in suits):
        isFlush = True
        handName = "Flush " + cardnames[kickers[0] - 2] + " " + cardnames[kickers[1] - 2] \
              + " " + cardnames[kickers[2] - 2] +  " " + cardnames[kickers[3] - 2] + " " + cardnames[kickers[4] - 2]
        handrankValue = (5,) + tuple(kickers)

    # check if a hand is a straight and a flush

    if isFlush & isStraight:
        isStraightFlush = True
        handName = "Straight Flush"
        handrankValue = (8,) + (straightHeight,)

    # check if a hand is four of a kind
    if '4' in  joined_histogram:
        fourofakindcard = (joined_histogram[1:].find('4') + 2)
        handName = "Four of a Kind " + cardnames[fourofakindcard -2] + " " + cardnames[kickers[0] - 2] + " kicker"
        handrankValue = (7,) + ((joined_histogram[1:].find('4') + 2),) + tuple(kickers)

    # check if a hand is a full house
    if ('3' in joined_histogram) & ('2' in joined_histogram):
        handName = "Full house"
        handrankValue = (6,) + ((joined_histogram[1:].find('3') + 2),) + ((joined_histogram[1:].find('2') + 2),) + tuple(kickers)


    # check if a hand is three of a kind
    if ('3' in joined_histogram) & (len(kickers) == 2):
        threeofakindcard = (joined_histogram[1:].find('3') + 2)
        handName = "Three of a Kind " + cardnames[threeofakindcard -2] + " " + cardnames[kickers[0] - 2] + \
            " " + cardnames[kickers[1] - 2]
        handrankValue = (3,) + ((joined_histogram[1:].find('3') + 2),) + tuple(kickers)

    # check if a hand is two pairs
    if ('2' in joined_histogram) & (len(kickers) == 1):
        lowerpair = (joined_histogram[1:].find('2') + 2)
        higherpair = (joined_histogram[lowerpair:].find('2') + 1 + lowerpair)
        handName = "Two pair " + cardnames[higherpair -2] + " and " + cardnames[lowerpair - 2] + " " + \
            cardnames[kickers[0] - 2] + " kicker"
        handrankValue = (2,) + (higherpair, lowerpair) + tuple(kickers)

    # check if a hand is one pair
    if ('2' in joined_histogram) & (len(kickers) == 3):
        lowerpair = (joined_histogram[1:].find('2') + 2)
        handName = "One pair " + cardnames[lowerpair - 2] + " kickers " + cardnames[kickers[0] - 2] \
            + " " + cardnames[kickers[1] - 2] +  " " + cardnames[kickers[2] - 2]
        handrankValue = (1,) + (lowerpair,) + tuple(kickers)


    # evaluate high card hand
    if (len(ranks_numerical) == len(set(ranks_numerical))) & (isStraight == False) & (isFlush == False):
        handName = "High card " + cardnames[kickers[0] - 2] + " " + cardnames[kickers[1] - 2] \
            + " " + cardnames[kickers[2] - 2] +  " " + cardnames[kickers[3] - 2] + " " + cardnames[kickers[4] - 2]
        handrankValue = (0,) + tuple(kickers)

    return {''.join(sorted(hand)): rank_integer(handrankValue)}


def build_hands_dict(deck, path):

    ranked_hands_dict = {}
    t0 = time.time()
    for five_card_hand in itertools.combinations(deck, 5):
        ranked_hands_dict.update(hand_rank_dict(five_card_hand))
    t1 = time.time()
    total = t1-t0
    print(total)
    with open(path,'w') as f:
        json.dump(ranked_hands_dict, f)


def rank_integer(rank_tuple):
    m = 100 ** 5
    score = 0
    for x in rank_tuple:
        score += x * m
        m /= 100

    return int(score)


build_hands_dict(cards, r'hands.json')