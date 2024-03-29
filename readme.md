# Toy poker hand evaluator

This is some code I wrote based on a [Stack Overflow question](https://stackoverflow.com/questions/59435354/how-can-i-speed-up-my-python-poker-hand-vs-hand-equity-calculator) (much of the code in `build_json.py` is the work of the OP, rioZg).

It is not optimised for useability or nice code, but it is pretty optimised for speed. 
I use it as a toy project to implement in new languages I am learning and to test the speed of different
machines, OSes., Python versions, etc.

Given one or two hands in Texas Hold'Em (only two players currently supported) 
and some, none or all of the community cards it calculates the win probability for each hand by 
calculating every possible outcome.

## How to use

First run `build_json.py` to create a json file that contains the value of every possible hand. You only need to do this once.

Now run `main.py`, use `--help` to see the full arguments, but the recommended way to run is to first select parallelism options:

    main.py --num-parallels 8

then continue interactively. This maximises the speed of each run by setting up worker processes etc in advance.

Technically you can omit both `hand2` and `board` but you'll be waiting a very long time for an answer. 
You can also supply partial definitions of either parameter, i.e. 0-2 cards for `hand2` and 0-5 for `board`.

Running with `--hand1` starts in non-interactive mode, whereby the program will evaluate this hand then exit.

When running interactively, it is usually fastest to set `num-parallels` equal to the number of cores you have. 

However in non-interactive mode, the overhead to start a process is so high that a lower value is sometimes better. 
`num-parallels = 0` disables parallelism entirely.

The `--thread-parallelism` switch changes the programme to use threads instead of processes - 
this is useless unless you are using a GIL-free interpreter
