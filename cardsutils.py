from primesieve import n_primes

ranks = ["2", "3", "4", "5", "6", "7", "8", "9", "T", "J", "Q", "K", "A"]
suits = ['h', 's', 'd', 'c']
ranks_map = {"2": 2, "3": 3, "4": 4, "5": 5, "6": 6, "7": 7, "8": 8, "9": 9, "A": 14, "J": 11, "K": 13, "Q": 12,
             "T": 10}
deck_as_list = []
for suit in suits:
    for rank in ranks:
        deck_as_list.append(rank + suit)

deck_as_set = set(deck_as_list)

deck_dict_with_primes = dict(zip(deck_as_list, n_primes(52)))
