"""Opt-in V-Unit RGBA distance-fade shader for saved-scene diagnostics.

NOT used by the launcher or native renderer. Resolve each command's palette
before blending, at its original position. The caller must preserve palette
update order and both native material and layer provenance before live use.

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
