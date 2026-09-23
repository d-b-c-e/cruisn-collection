"""Opt-in record of Windows monitor topology while an isolated replay runs.

This is diagnostic evidence, not a capture oracle: short transitions between
polls can be missed. Completed-frame dimensions remain independently checked.
"""
import threading
import time

from display_target import monitors


def topology(value):
    """Ignore enumeration order, but retain each device's size and primary flag."""
    return tuple(sorted((row['device'], bool(row['primary']),
                         tuple(row['size'])) for row in value))


class DisplayWatch:
    def __init__(self, poll=monitors, interval=0.5, clock=time.monotonic, expected=None):
        if interval <= 0:
            raise ValueError('display watch interval must be positive')
        self.poll, self.interval, self.clock = poll, interval, clock
        self._stop = threading.Event()
        self._thread = None
        self._started = None
        self._previous = None
        self._expected = topology(expected) if expected is not None else None
        self._samples = []
        self._error = None

    def sample(self):
        try:
            current = topology(self.poll())
            if not current:
                raise ValueError('no monitors enumerated')
        except (OSError, ValueError, AttributeError, TypeError, KeyError) as exc:
            self._error = f'{type(exc).__name__}: {exc}'
            self._stop.set()
            return
        if current != self._previous:
            self._samples.append({
                'elapsed_ms': round((self.clock() - self._started) * 1000, 3),
                'monitors': [dict(device=device, primary=primary, size=list(size))
                             for device, primary, size in current],
            })
            self._previous = current

    def start(self):
        if self._started is not None:
            raise ValueError('display watch already started')
        self._started = self.clock()
        self.sample()
        if self._error:
            raise ValueError('display watch initial enumeration failed: ' + self._error)
        self._thread = threading.Thread(target=self._loop, name='display-topology-watch', daemon=True)
        self._thread.start()

    def _loop(self):
        while not self._stop.wait(self.interval):
            self.sample()

    def close(self):
        if self._started is None:
            raise ValueError('display watch was not started')
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=2)
            if self._thread.is_alive():
                self._error = 'display enumeration did not stop within two seconds'
        initial_matches = (self._expected is None or bool(self._samples) and
                           topology(self._samples[0]['monitors']) == self._expected)
        return {
            'passed': self._error is None and initial_matches and len(self._samples) == 1,
            'initial_matches_preflight': initial_matches,
            'changes': max(0, len(self._samples) - 1),
            'samples': self._samples,
            'error': self._error,
            'interval_ms': round(self.interval * 1000, 3),
            'scope': 'Polled monitor topology during emulator execution; transitions between polls may be missed.',
        }
