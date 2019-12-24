import multiprocessing as mp


def get_print(q):
    while not q.empty():
        a = q.get(timeout=1)
        print(a)


if __name__ == '__main__':
    q = mp.Queue()

    for i in range(100):
        q.put(i)

    p = mp.Process(target=get_print, args=(q,))
    p.start()
    p.join()
    print("Joined")
