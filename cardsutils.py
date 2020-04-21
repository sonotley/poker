from primesieve import n_primes

ranks = ["2", "3", "4", "5", "6", "7", "8", "9", "A", "J", "K", "Q", "T"]
suits = ['c', 'd', 'h', 's']
deck_as_list = []
for suit in suits:
    for rank in ranks:
        deck_as_list.append(rank + suit)

deck_as_set = set(deck_as_list)

deck_dict_with_primes = dict(zip(deck_as_list, n_primes(52)))
