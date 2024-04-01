import queue
import threading


# disable=dangerous-default-value
def run_in_thread(window, computation, args=(), kwargs={}, callback=None, errback=None, polling=500):
    future_result = queue.Queue()

    worker = threading.Thread(target=_compute_result, args=(computation, args, kwargs, future_result))
    worker.daemon = True
    worker.start()

    if callback is not None or errback is not None:
        _after_completion(window, future_result, callback, errback, polling)


def _compute_result(computation, args, kwargs, future_result):
    try:
        _result = computation(*args, **kwargs)
    except BaseException as e:  # disable=broad-except
        _result = e

    future_result.put(_result)


def _after_completion(window, future_result, callback, errback, polling):
    def check():
        try:
            result = future_result.get(block=False)
        except Exception:  # disable=broad-except
            window.after(polling, check)
        else:
            if isinstance(result, Exception):
                if errback is not None:
                    errback(result)
            else:
                if callback is not None:
                    callback(result)

    window.after(0, check)
