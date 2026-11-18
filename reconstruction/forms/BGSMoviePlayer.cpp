// BGSMoviePlayer functions for build sse-steam-1-7-104.
//
// Labels: v2
// Task: contrib-bgsmovieplayer
// Code origin: Bodies for Unk_07, Unk_09, Unk_0B and Unk_0C written from the local listings; declarations added to the existing unit header.
// Source exposure: mixed (names and declarations from community headers; the listing of the pinned
// image).
// MIT License
//
// Copyright (c) 2018 Ryan-rsm-McKenzie
//
// Permission is hereby granted, free of charge, to any person obtaining a copy
// of this software and associated documentation files (the "Software"), to deal
// in the Software without restriction, including without limitation the rights
// to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
// copies of the Software, and to permit persons to whom the Software is
// furnished to do so, subject to the following conditions:
//
// The above copyright notice and this permission notice shall be included in all
// copies or substantial portions of the Software.
//
// THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
// IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
// FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
// AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
// LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
// OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
// SOFTWARE.
// Evidence: findings/queue-refill-held-selection.md
// Recipe: reconstruction/recipes/msvc-19.16.27054-o2.json (compile this file alone).
// Drafted by Hinkiii, assisted by claude-sonnet-5-5, starting from
// a tools/skeleton.py skeleton.
// Compared functions:
//   RVA 0x644910, 7 bytes: BGSMoviePlayer::Unk_09
//   RVA 0x644930, 8 bytes: BGSMoviePlayer::Unk_0B
//   RVA 0x6448d0, 12 bytes: BGSMoviePlayer::Unk_07
//   RVA 0x644940, 17 bytes: BGSMoviePlayer::Unk_0C
//   RVA 0x645120, 3 bytes: BGSMoviePlayer::Unk_06
//   RVA 0x645130, 3 bytes: BGSMoviePlayer::Unk_05
//   RVA 0x644920, 7 bytes: BGSMoviePlayer::Unk_0A
// Adapted bodies: none
// A byte match shows that this source and recipe produce the checked code; it does not verify the
// community names or that the original source looked like this.
#include "BGSMoviePlayer.h"
std::uint32_t BGSMoviePlayer::Unk_09() { return g_moviePlayerValue09; }
std::uint8_t BGSMoviePlayer::Unk_0B() { return g_moviePlayerFlag0B; }
void BGSMoviePlayer::Unk_07() { InitMoviePlayerObject(&g_moviePlayerObject); }
std::uint32_t BGSMoviePlayer::Unk_0C()
{
    Main* main = Main::singleton;
    if (main) {
        return main->unk28;
    }
    return 0;
}

// RVA 0x645120, 3 bytes
void BGSMoviePlayer::Unk_06()
{
}

// RVA 0x645130, 3 bytes
void BGSMoviePlayer::Unk_05()
{
}

// RVA 0x644920, 7 bytes
std::uint32_t BGSMoviePlayer::Unk_0A()
{
    return g_bgsMoviePlayerUnk;
}
