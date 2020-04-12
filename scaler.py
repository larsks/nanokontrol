#!/usr/bin/python

class Scaler:
    def __init__(self, min_in, max_in, min_out, max_out):
        self._min_in = min_in
        self._max_in = max_in
        self._min_out = min_out
        self._max_out = max_out

        self.update()

    def update(self):
        self.scale_factor = (
            (self._max_out - self._min_out) /
            (self._max_in - self._min_in)
        )

    @property
    def min_in(self):
        return self._min_in

    @min_in.setter
    def min_in(self, val):
        self._min_in = val
        self.update()

    @property
    def max_in(self):
        return self._max_in

    @max_in.setter
    def max_in(self, val):
        self._max_in = val
        self.update()

    @property
    def min_out(self):
        return self._min_out

    @min_out.setter
    def min_out(self, val):
        self._min_out = val
        self.update()

    @property
    def max_out(self):
        return self._max_out

    @max_out.setter
    def max_out(self, val):
        self._max_out = val
        self.update()

    def scale(self, val):
        if (val < self._min_in) or (val > self._max_in):
            raise ValueError(val)

        return ((val - self._min_in) * self.scale_factor) + self._min_out
