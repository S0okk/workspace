import time
from threading import Thread

def clock(delay):
    time.sleep(delay)


threads = [Thread(target=clock, args=(1,)) for i in range(10**6)]

if __name__ == "__main__":
    start = time.time()
    print(f"Time start: {time.strftime('%X')}")
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    
    print(f'Time end: {time.strftime('%X')}')
    print(f' ======= Total time: {time.time() - start:0.2f} ======= ')