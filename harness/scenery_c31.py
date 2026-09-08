"""C31 arithmetic reference for host scenery reconstruction (no CPU execution).

Uses the extended register mantissa between operations, and the 24-bit operand
precision of MPYF. A store/reload is deliberately explicit. Ordinary IEEE float
math or rounding to nearest does not reproduce the game at pixel boundaries.

Arithmetic adapted from MAME src/devices/cpu/tms320c3x/320c3x_ops.ipp,
copyright Aaron Giles, BSD-3-Clause. Status flags are outside this module's scope.

Redistribution and use in source and binary forms, with or without modification,
are permitted provided that the following conditions are met:
1. Redistributions of source code must retain the above copyright notice, this
   list of conditions and the following disclaimer.
2. Redistributions in binary form must reproduce the above copyright notice,
   this list of conditions and the following disclaimer in the documentation
   and/or other materials provided with the distribution.
3. Neither the name of the copyright holder nor the names of its contributors
   may be used to endorse or promote products derived from this software without
   specific prior written permission.
THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT,
INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE
OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED
OF THE POSSIBILITY OF SUCH DAMAGE.
"""
from dataclasses import dataclass
import math


def signed(value, bits=32):
    value &= (1 << bits) - 1
    return value - (1 << bits) if value & (1 << (bits-1)) else value


@dataclass(frozen=True, slots=True)
class F:
    mantissa: int
    exponent: int

    @classmethod
    def load(cls, word):
        return cls(signed(word << 8), signed(word >> 24, 8))

    def store(self):
        return ((self.exponent & 255) << 24) | ((self.mantissa >> 8) & 0xffffff)

    def reload(self):
        return F.load(self.store())

    def value(self):
        if self.exponent == -128:
            return 0.0
        return math.ldexp(self.mantissa ^ 0x80000000, self.exponent - 31)

    @classmethod
    def integer(cls, value):
        value = signed(value)
        if value == 0:
            return ZERO
        if value == -1:
            return cls(-0x80000000, -1)
        count = 32 - (value if value > 0 else ~value).bit_length()
        return cls(signed((value << count) ^ 0x80000000), 31-count)

    def fix(self):
        shift = 31-self.exponent
        if shift <= 0:
            return 0x7fffffff if self.mantissa >= 0 else -0x80000000
        if shift > 31:
            return self.mantissa >> 31
        return (self.mantissa >> shift) ^ (1 << (31-shift))

    def __neg__(self):
        # Exact normalization; the negative of +1 uses exponent -1.
        if self.exponent == -128:
            return ZERO
        return _normalize(-(self.mantissa ^ 0x80000000), self.exponent)

    def __add__(self, other):
        if self.exponent == -128:
            return other
        if other.exponent == -128:
            return self
        return self._sum(other, False)

    def __sub__(self, other):
        if other.exponent == -128:
            return self
        return self._sum(other, True)

    def _sum(self, other, subtract):
        exp = max(self.exponent, other.exponent)
        if self.exponent-other.exponent >= 32:
            return self
        if other.exponent-self.exponent >= 32:
            return -other if subtract else other
        m1 = (self.mantissa ^ 0x80000000) >> (exp-self.exponent)
        m2 = (other.mantissa ^ 0x80000000) >> (exp-other.exponent)
        return _normalize(m1-m2 if subtract else m1+m2, exp)

    def __mul__(self, other):
        if self.exponent == -128 or other.exponent == -128:
            return ZERO
        m1 = (self.mantissa >> 8) ^ 0x800000
        m2 = (other.mantissa >> 8) ^ 0x800000
        man = (m1*m2) >> 15
        exp = self.exponent+other.exponent
        while man >= 0x100000000 or man < -0x100000000:
            man >>= 1
            exp += 1
        return _finish(man, exp)


ZERO = F(0, -128)


def _finish(man, exp):
    if man == 0 or exp <= -128:
        return ZERO
    if exp > 127:
        return F(-0x80000000 if man < 0 else 0x7fffffff, 127)
    return F(signed(man ^ 0x80000000), exp)


def _normalize(man, exp):
    if man == 0 or exp <= -128:
        return ZERO
    while man >= 0x100000000 or man < -0x100000000:
        man >>= 1
        exp += 1
    if -0x80000000 <= man < 0x80000000:
        count = 32 - (man if man > 0 else ~man).bit_length()
        man <<= count
        exp -= count
    return _finish(man, exp)


def dot(values, row):
    """Three separate MPYF operations followed by two extended ADDF operations."""
    return (values[0]*row[0] + values[1]*row[1]) + values[2]*row[2]
