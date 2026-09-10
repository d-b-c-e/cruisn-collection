"""Diagnostic Zeus D32F policies; no production extended-distance acceptance.

Preserve the current fragment shader's float normalization and D24 quantization
before mapping those stored codes into a larger domain. Clearing and saturated
original geometry remain the same sentinel. True farther geometry needs a
separate pre-clamp policy and handover validation; this helper does not supply it.
The GL diagnostics must pass on the actual driver before using this mapping.
The separate wider policy requires an explicit source-command tag for range
initialization. It is standalone until its native producer/consumer is integrated.
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


ORIGINAL_DEPTH = '''    dv = clamp(dv, 0, 0xffffff);
    gl_FragDepth = float(dv) / 16777215.0;'''
WIDE_DEPTH = '''    bool clearDepth = (flags & 32u) != 0u || ((flags & 256u) != 0u && dv >= 16777215 && (flags & 1024u) == 0u);
    int boundedDepth = clamp(dv, 0, 67108860);
    if ((flags & 1024u) != 0u) {
        float legacyDepth = float(clamp(dv, 0, 16777215)) / 16777215.0;
        uint quantizedDepth = uint(floor(double(legacyDepth) * 16777215.0lf + 0.5lf));
        gl_FragDepth = float(quantizedDepth) / 16777216.0;
    } else if (clearDepth) gl_FragDepth = 1.0;
    else if (boundedDepth <= 16777215) {
        float legacyDepth = float(boundedDepth) / 16777215.0;
        uint quantizedDepth = uint(floor(double(legacyDepth) * 16777215.0lf + 0.5lf));
        gl_FragDepth = float(quantizedDepth) / 67108864.0;
    } else gl_FragDepth = float(boundedDepth) / 67108864.0;'''


def wide_fragment(fragment):
    """Private wide geometry plus explicitly tagged (bit1024) range clears.

    Only original fast-clear command type3 may carry the new tag. Direct depth
    writes preserve actual-depth meaning. Future geometry packets reject clears
    and out-of-range depths; their guard must not rely on shader saturation.
    Original/future handover and complete game ordering still require live proof.
    """
    if fragment.count(ORIGINAL_DEPTH) != 1:
        raise ValueError('expected exactly one original Zeus depth calculation')
    return fragment.replace(ORIGINAL_DEPTH, WIDE_DEPTH)
