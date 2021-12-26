ranks = ["2", "3", "4", "5", "6", "7", "8", "9", "T", "J", "Q", "K", "A"]
suits = ['h', 's', 'd', 'c']
ranks_map = {"2": 2, "3": 3, "4": 4, "5": 5, "6": 6, "7": 7, "8": 8, "9": 9, "A": 14, "J": 11, "K": 13, "Q": 12,
             "T": 10}
deck_as_list = []
for suit in suits:
    for rank in ranks:
        deck_as_list.append(rank + suit)

deck_as_set = set(deck_as_list)

fifty_two_primes = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47, 53, 59, 61, 67, 71, 73, 79, 83, 89, 97, 101, 103, 107, 109, 113, 127, 131, 137, 139, 149, 151, 157, 163, 167, 173, 179, 181, 191, 193, 197, 199, 211, 223, 227, 229, 233, 239]

deck_dict_with_primes = dict(zip(deck_as_list, fifty_two_primes))
