// SPDX-License-Identifier: BSD-3-Clause
// Bounded LOCAL model/context batch. No game operands are distributed.
#include "zeus_model_bounds.h"
#include <fstream>
#include <iostream>
#include <stdexcept>

int main(int argc, char **argv)
{
    try
    {
        if (argc != 3) return 2;
        std::ifstream input(argv[1], std::ios::binary | std::ios::ate);
        if (!input || input.tellg() < 8 || input.tellg() > 128*1024*1024)
            throw std::runtime_error("bounds input size");
        input.seekg(0);
        auto read = [&](void *p, size_t bytes) {
            if (!input.read(static_cast<char *>(p), bytes))
                throw std::runtime_error("bounds input truncated");
        };
        auto word = [&]() { uint32_t w; read(&w, 4); return w; };
        if (word() != 0x3142535a) throw std::runtime_error("bounds input magic");
        const uint32_t count = word();
        if (!count || count > 65536) throw std::runtime_error("bounds case budget");
        std::vector<uint32_t> decisions;
        uint32_t rejected = 0;
        for (uint32_t i = 0; i < count; ++i)
        {
            const uint32_t n = word(), size = word();
            if (n > 2*(0xc800+1)) throw std::runtime_error("bounds model budget");
            cruisn::zeus_model::Context context;
            float margin;
            read(context.regs.data(), 128*4);
            read(context.matrix.data(), 9*4);
            read(context.translation.data(), 3*4);
            read(&margin, 4);
            std::vector<uint32_t> words(n); read(words.data(), n*4);
            cruisn::zeus_bounds::Bounds bounds;
            if (!cruisn::zeus_bounds::prepare(words, size, bounds))
                throw std::runtime_error("bounds model rejected");
            const bool outside = cruisn::zeus_bounds::outside(bounds, context, margin);
            decisions.push_back(outside); rejected += outside;
        }
        if (input.peek() != std::char_traits<char>::eof())
            throw std::runtime_error("bounds input trailing bytes");
        std::ofstream output(argv[2], std::ios::binary);
        if (!output.write(reinterpret_cast<const char *>(decisions.data()), decisions.size()*4))
            throw std::runtime_error("bounds output write");
        output.close();
        if (!output) throw std::runtime_error("bounds output close");
        std::cout << "{\"passed\":true,\"cases\":" << count << ",\"rejected\":" << rejected << "}\n";
        return 0;
    }
    catch (const std::exception &error)
    {
        std::cerr << error.what() << '\n';
        return 1;
    }
}
