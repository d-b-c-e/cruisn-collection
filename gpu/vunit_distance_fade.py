"""V-Unit distance-fade variants for saved scenes and gated native diagnostics.

The RGBA variant resolves each command's palette before ordered blending.
The indexed/mirror variants preserve late palette resolution and are linked by
the explicit native World experiment. They are not launcher defaults. Callers
must preserve palette updates, original buffers and material/layer ownership.

Additional bindings: palette R32UI at uniform ``colors``; SSBO4 float per quad
(-1 = fade, +1 = opaque), SSBO5 vec4 positive camera depths per quad. Both reset
with each draw, matching original primitive IDs. Uniforms fadePlane/fadeWidth
are positive camera units. Original UVs, transparency discards and far masks
are retained. Roads/other protected layers are selected opaque by the caller.
"""
import math


def validate_parameters(plane, width):
    if (isinstance(plane, bool) or isinstance(width, bool) or
            not isinstance(plane, (int, float)) or not isinstance(width, (int, float)) or
            not math.isfinite(plane) or not math.isfinite(width) or
            not 0 < width < plane <= 1000000):
        raise ValueError('distance fade requires finite 0 < width < plane <= 1000000')
    return float(plane), float(width)


TAIL = r"""
layout(std430,binding=5) readonly buffer DepthValues { vec4 cameraZ[]; };
uniform float fadePlane;
uniform float fadeWidth;
bool bary(vec2 p, vec2 a, vec2 b, vec2 c, out vec3 weights) {
 vec2 u=b-a,v=c-a,w=p-a;float det=u.x*v.y-u.y*v.x;
 if(abs(det)<0.00001) { weights=vec3(0);return false; }
 float y=(w.x*v.y-w.y*v.x)/det,z=(u.x*w.y-u.y*w.x)/det;
 weights=vec3(1-y-z,y,z);return true;
}
void main() {
 original_pixel();
 uint pen=outIndex&32767u;
 uint palette_word=texelFetch(colors,ivec2(pen&255u,pen>>8),0).r;
 uvec3 rgb=uvec3((palette_word>>10)&31u,(palette_word>>5)&31u,palette_word&31u);
 int id=gl_PrimitiveID/2;float alpha=1;
 if(opacity[id]<0) {
  vec2 p=vec2(gl_FragCoord.x/float(uScale),uCanvas.y-gl_FragCoord.y/float(uScale));
  vec4 z=cameraZ[id];vec3 weights;vec3 used=z.xyz;
  bool valid=bary(p,v0,v1,v2,weights);
  if(!valid || any(lessThan(weights,vec3(-0.00001)))) { valid=bary(p,v0,v2,v3,weights);used=z.xzw; }
  float depth=max(max(z.x,z.y),max(z.z,z.w));
  if(valid) { weights=max(weights,vec3(0));weights/=dot(weights,vec3(1));depth=1.0/dot(weights,1.0/used); }
  float t=clamp((fadePlane-depth)/fadeWidth,0.0,1.0);alpha=t*t*(3-2*t);
 }
 outColor=vec4(vec3((rgb<<3)|(rgb>>2))/255.0,alpha);
}
"""


def fragment_shader(original):
    output = 'layout(location = 0) out uint outIndex;'
    entry = 'void main() {'
    if original.count(output) != 1 or original.count(entry) != 1:
        raise ValueError('unsupported V-Unit material shader layout')
    replacement = ("uint outIndex;\nlayout(location=0) out vec4 outColor;\n"
                   "uniform usampler2D colors;\n"
                   "layout(std430,binding=4) readonly buffer Opacity { float opacity[]; };")
    return original.replace(output, replacement).replace(entry, 'void original_pixel() {') + TAIL


def indexed_fragment_shader(original):
    """Preserve late palette resolution; write the visible owner's opacity to MRT2.

    This alternative requires an original-only index mirror. Final blending uses
    the visible extended index and original index, both resolved with the current
    palette. It is a distance-weighted composite, not ordered alpha accumulation
    through every overlapping host surface. Compare those policies before use.
    """
    shader = fragment_shader(original)
    shader = shader.replace('uint outIndex;\nlayout(location=0) out vec4 outColor;',
                            'layout(location=0) out uint outIndex;\n'
                            'layout(location=2) out float outFadeAlpha;')
    shader = shader.replace('uniform usampler2D colors;\n', '')
    first = shader.index(' uint pen=outIndex&32767u;', shader.index('void main()'))
    last = shader.index(' int id=gl_PrimitiveID/2;', first)
    shader = shader[:first] + shader[last:]
    shader = shader.replace(' outColor=vec4(vec3((rgb<<3)|(rgb>>2))/255.0,alpha);',
                            ' outFadeAlpha=alpha;')
    return shader


def mirror_fragment_shader(source):
    """Duplicate ordinary index/mask writes to MRT3/4 in a single traversal.

    Auxiliary draws MUST disable attachments3/4 (or bind an extended-only FBO).
    CPU index writes use the same wrapper. Opacity is one unless the input shader
    already computes it. No page clearing or source classification is inferred.
    """
    if (source.count('void main() {') != 1 or 'outIndex;' not in source or
            'outMask;' not in source or 'outOriginalIndex' in source):
        raise ValueError('unsupported indexed shader for original mirror')
    has_alpha = 'layout(location=2) out float outFadeAlpha;' in source
    declarations = '' if has_alpha else 'layout(location=2) out float outFadeAlpha;\n'
    declarations += ('layout(location=3) out uint outOriginalIndex;\n'
                     'layout(location=4) out uint outOriginalMask;\n')
    body = 'void main() {\n mirror_source();\n'
    if not has_alpha:
        body += ' outFadeAlpha=1.0;\n'
    body += ' outOriginalIndex=outIndex;\n outOriginalMask=outMask;\n}\n'
    return source.replace('void main() {', 'void mirror_source() {') + declarations + body


def palette_shader(original):
    """Resolve both index views late, retaining separate seam/dither ownership.

    The caller maintains original-only indices/masks plus extended indices/masks
    and visible-owner opacity. Both views use the presentation-time palette.
    Native CRT processing follows the blend. This does not implement page,
    palette, CPU-write or command lifetimes in the native renderer.
    """
    import re
    begin = original.index('bool covered(ivec2 p, bool foreground) {')
    end = original.index('ivec2 src_px(vec2 tuv) {', begin)
    helpers = original[begin:end]
    names = ('covered', 'fill_layer', 'fill_px', 'fetch_raw', 'fetch_at')
    mapping = {name: 'original_' + name for name in names}
    mapping.update(idxTex='originalIdxTex', maskTex='originalMaskTex', uHostLayers='0')
    base = re.sub(r'\b(' + '|'.join(mapping) + r')\b', lambda m: mapping[m[0]], helpers)
    entry = 'vec3 fetch_at(ivec2 p) {'
    if helpers.count(entry) != 1:
        raise ValueError('unsupported V-Unit filtered palette resolve layout')
    enhanced = helpers.replace(entry, 'vec3 enhanced_fetch_at(ivec2 p) {')
    declarations = """uniform int uDistanceFade;
uniform usampler2D originalIdxTex;
uniform usampler2D originalMaskTex;
uniform sampler2D fadeAlphaTex;
"""
    blend = """
float owner_alpha(ivec2 p) {
    return clamp(texelFetch(fadeAlphaTex, fill_px(p), 0).r, 0.0, 1.0);
}
float surface_alpha(ivec2 p) {
    return clamp(texelFetch(fadeAlphaTex, p, 0).r, 0.0, 1.0);
}
vec3 fetch_at(ivec2 p) {
    vec3 extended = enhanced_fetch_at(p);
    if (uDistanceFade == 0) return extended;
    ivec2 sz = textureSize(idxTex, 0);
    p = clamp(p, ivec2(0), sz - 1);
    float alpha = owner_alpha(p);
    ivec2 b = (p / 2) * 2;
    if (b.x + 1 < sz.x && b.y + 1 < sz.y) {
        bool a = (texelFetch(maskTex, b, 0).r & 3u) == 3u;
        bool c = (texelFetch(maskTex, b + ivec2(1, 0), 0).r & 3u) == 3u;
        bool d = (texelFetch(maskTex, b + ivec2(0, 1), 0).r & 3u) == 3u;
        bool e = (texelFetch(maskTex, b + ivec2(1, 1), 0).r & 3u) == 3u;
        // The game's qualified dither pair is resolved as one smoked surface.
        // Use its written pixels' opacity for all four filtered pixels; the
        // untouched background's opaque tag must not reintroduce checkerboards.
        if (a == e && c == d && a != c) {
            alpha = a ? 0.5 * (surface_alpha(b) + surface_alpha(b + ivec2(1, 1)))
                      : 0.5 * (surface_alpha(b + ivec2(1, 0)) + surface_alpha(b + ivec2(0, 1)));
        }
    }
    return mix(original_fetch_at(p), extended, alpha);
}
"""
    return original[:begin] + declarations + base + enhanced + blend + original[end:]
