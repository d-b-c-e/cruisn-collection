// license:BSD-3-Clause
#pragma once
#include <cstdint>
namespace cruisn { namespace world_host {
// Separately mapped World revisions. These are semantic bindings, not a global
// relocation: allocator, scene heads and lookup tables move independently.
struct Layout {uint32_t revision,table,pending,scene,section,stage,cursor,palette,texture,trig;};
constexpr Layout v24={24,0xb66f,0x61ec,0x61ee,0xd575,0xd5a5,0xd5a1,0x4151,0x4150,0xcc35};
constexpr Layout v25={25,0xb665,0x658d,0x658f,0xd56f,0xd59f,0xd59b,0x4121,0x4120,0xcc2f};
inline const Layout *layout(uint32_t revision){return revision==24?&v24:revision==25?&v25:nullptr;}
template<class Read> bool track_reset(Read read,uint32_t revision)
{
    // World 2.5 clears these together while leaving menu objects on its lists.
    // A pending list alone does not prove that a race's scenery is initialized.
    return revision==25 && read(v25.section)==0 && read(0xd586)==0;
}
template<class Read> bool scene_matches(Read read,uint32_t revision)
{
    const auto *profile=layout(revision);if(!profile)return false;
    return read(0x69)==(0x08280000|profile->scene) &&
        read(revision==24?0x7b55:0x7b47)==(0x08280000|profile->pending) &&
        read(revision==24?0x7b5c:0x7b4e)==0x1ae03000 &&
        (read(revision==24?0xd58c:0xd586)==11 || track_reset(read,revision));
}
} }
