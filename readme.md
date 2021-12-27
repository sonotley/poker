# Toy poker hand evaluator

This is some code I wrote based on a [Stack Overflow question](https://stackoverflow.com/questions/59435354/how-can-i-speed-up-my-python-poker-hand-vs-hand-equity-calculator) (much of the code in `build_json.py` is the work of the OP, rioZg).

It is not optimised for useability or nice code, but it is pretty optimised for speed. 
I use it as a toy project to implement in new languages I am learning and to test the speed of different
machines, OSes., Python versions, etc.

Given two hands in Texas Hold'Em (only two players currently supported, it would be insanely slow with more) 
and optionally the community cards it calculates the win probability for each hand by calculating every possible outcome.

## How to use

First run `build_json.py` to create a json file that contains the value of every possible hand. You only need to do this once.
This has a dependency on the `primesieve` package.

Now run `main_prime.py` and enter the cards as prompted. You can edit the values of `PARALLELISM` and `NUM_PARALLELS`
in the code to change the method of parallel processing between threads and processes and the number of them.

In standard CPython on Linux it is usually fastest to select `PARALLELISM = "PROCESS"` and set `NUM_PARALLELS`
equal to the number of cores you have. However, on other platforms (or very high core-counts) the overhead to start a 
process is so high that a lower value is better. `NUM_PARALLELS = 0` disables parallelism entirely.
