import queue
import threading


class TaskInThread:
    def __init__(
        self,
        window,
        computation,
        args=(),
        kwargs=None,
        callback=None,
        errback=None,
        polling=500,
        timeout=10000,
    ) -> None:
        if kwargs is None:
            kwargs = {}

        future_result = queue.Queue()

        worker = threading.Thread(
            target=self._compute_result, args=(computation, args, kwargs, future_result)
        )
        worker.daemon = True
        worker.start()

        self._timeout = timeout

        if callback is not None or errback is not None:
            self._after_completion(window, future_result, callback, errback, polling)

    def _compute_result(self, computation, args, kwargs, future_result):
        try:
            _result = computation(*args, **kwargs)
        except Exception as e:  # disable=broad-except
            _result = e

        future_result.put(_result)

    def _after_completion(self, window, future_result, callback, errback, polling):
        def check():
            result = None
            try:
                result = future_result.get(block=False)
            except queue.Empty:
                pass

            if result is None and self._timeout > 0:
                self._timeout -= polling
                window.after(polling, check)
            elif result is None and self._timeout <= 0:
                if errback is not None:
                    errback("Операция не была завершена за отведенное время")
            else:
                if isinstance(result, Exception):
                    if errback is not None:
                        errback(result)
                    else:
                        if callback is not None:
                            callback(result)

        window.after(0, check)
