from original import hand_v_hand, build_hands_dict
import time

build_hands_dict(r'hands.p')

tic=time.time()

print(hand_v_hand())

toc=time.time()

print(toc-tic)