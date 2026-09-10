"""Diagnostic original-only D32F mapping; not the extended-distance policy.

Preserve the current fragment shader's float normalization and D24 quantization
before mapping those stored codes into a larger domain. Clearing and saturated
original geometry remain the same sentinel. True farther geometry needs a
separate pre-clamp policy and handover validation; this helper does not supply it.
The GL diagnostics must pass on the actual driver before using this mapping.
"""

ORIGINAL = 'gl_FragDepth = float(dv) / 16777215.0;'
COMPATIBILITY = '''float legacyDepth = float(dv) / 16777215.0;
    uint quantizedDepth = uint(floor(double(legacyDepth) * 16777215.0lf + 0.5lf));
    gl_FragDepth = quantizedDepth == 16777215u ? 1.0 : float(quantizedDepth) / 67108864.0;'''


def compatibility_fragment(fragment):
    """Change only the final depth normalization; reject an unknown shader."""
    if fragment.count(ORIGINAL) != 1:
        raise ValueError('expected exactly one original Zeus depth normalization')
    return fragment.replace(ORIGINAL, COMPATIBILITY)
