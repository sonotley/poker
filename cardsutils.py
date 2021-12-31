from __future__ import annotations

ranks: list[str] = ["2", "3", "4", "5", "6", "7", "8", "9", "T", "J", "Q", "K", "A"]
suits: list[str] = ["h", "s", "d", "c"]
ranks_map: dict[str, int] = {
    "2": 2,
    "3": 3,
    "4": 4,
    "5": 5,
    "6": 6,
    "7": 7,
    "8": 8,
    "9": 9,
    "A": 14,
    "J": 11,
    "K": 13,
    "Q": 12,
    "T": 10,
}
deck_as_list: list[str] = []
for suit in suits:
    for rank in ranks:
        deck_as_list.append(rank + suit)

deck_as_set: set[str] = set(deck_as_list)

fifty_two_primes: list[int] = [
    2,
    3,
    5,
    7,
    11,
    13,
    17,
    19,
    23,
    29,
    31,
    37,
    41,
    43,
    47,
    53,
    59,
    61,
    67,
    71,
    73,
    79,
    83,
    89,
    97,
    101,
    103,
    107,
    109,
    113,
    127,
    131,
    137,
    139,
    149,
    151,
    157,
    163,
    167,
    173,
    179,
    181,
    191,
    193,
    197,
    199,
    211,
    223,
    227,
    229,
    233,
    239,
]

deck_dict_with_primes: dict[str, int] = dict(zip(deck_as_list, fifty_two_primes))


def grouped(iterable, n):
    "s -> (s0,s1,s2,...sn-1), (sn,sn+1,sn+2,...s2n-1), (s2n,s2n+1,s2n+2,...s3n-1), ..."
    return zip(*[iter(iterable)]*n)


def extract_cards_from_string(card_string: str) -> set[int]:
    result = set()
    for x in grouped(card_string, 2):
        card = x[0].upper() + x[1].lower()
        try:
            result.add(deck_dict_with_primes[card])
        except KeyError:
            raise ValueError(f"Failed to interpret {card} as a valid card")

    if len(card_string) != 2 * len(result):
        raise ValueError(f"String '{card_string}' looks like {len(card_string)//2} cards but didn't parse - is there a duplicate?")
    return result
