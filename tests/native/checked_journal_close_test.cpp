// SPDX-License-Identifier: BSD-3-Clause
#include "checked_journal_close.h"
#include <cassert>
int main() {
    FILE *file=nullptr;assert(cruisn::close_journal(file) && !file);
    file=std::tmpfile();assert(file);
    assert(std::fputs("complete record\n",file)>=0);
    assert(cruisn::close_journal(file) && !file);
    // An actual failed write to a read-only stream sets ferror even when its
    // eventual fclose succeeds. The source file cannot be modified this way.
    file=std::fopen(__FILE__,"rb");assert(file);
    assert(std::fputs("rejected write",file)==EOF && std::ferror(file));
    assert(!cruisn::close_journal(file) && !file);
    assert(cruisn::close_journal(file));
}
