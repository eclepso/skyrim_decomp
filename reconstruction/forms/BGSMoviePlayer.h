// BGSMoviePlayer declarations for build sse-steam-1-7-104.
//
// Labels: v2
// Task: p92-s-bgsmovieplayer
// Code origin: declarations generated from a tools/skeleton.py skeleton and extended by hand from the local listings; globals and helper callees are named guesses.
// Source exposure: mixed (names and declarations from community headers; base classes, sizes and
// the compared functions from the pinned image).
// Started from a tools/skeleton.py skeleton: stand-ins carry only what the compared code needs, and
// community names are unverified.
// Base form: local stand-ins (no ancestor has a shared header).
// BGSMoviePlayer: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT) EXE_RTTI
// MoviePlayer: STANDIN EXE_RTTI
// BGSMoviePlayer::Unk_06, BGSMoviePlayer::Unk_05, BGSMoviePlayer::Unk_0A, BGSMoviePlayer::Unk_07, BGSMoviePlayer::Unk_09, BGSMoviePlayer::Unk_0B, BGSMoviePlayer::Unk_0C: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// MoviePlayer::~MoviePlayer, unknown08, unknown58: GUESS(low)
// The MIT notice below covers only the names and declarations taken from
// CharmedBaryon/CommonLibSSE-NG@b93280e832f263dbef44e44cbe2936622a02f91a; the other code in this file
// is covered by the repository licence and the provenance labels above.
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
#pragma once

#include <cstdint>
#include <cstddef>

class MoviePlayer
{
public:
    virtual ~MoviePlayer() = default;
    std::uint8_t unknown08[0x50];  // 08
};
static_assert(sizeof(MoviePlayer) == 0x58, "MoviePlayer size");

// g_moviePlayerValue09: GUESS(low); the dword at address 0x33363c4 that Unk_09 returns.
// g_moviePlayerFlag0B: GUESS(low); the byte at address 0x3336400 that Unk_0B returns.
// g_moviePlayerObject: GUESS(low); the object at address 0x3331f40 passed to the callee in Unk_07.
// InitMoviePlayerObject: GUESS(low); address 0x1009cf0, called by Unk_07 with the global object.
// Main::singleton: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); global at address 0x3230530
// unk28: GUESS(low); member of Main read by Unk_0C.
// g_bgsMoviePlayerUnk: GUESS(low); the dword at address 0x33363c8 that Unk_0A returns.
extern std::uint32_t g_bgsMoviePlayerUnk;
extern std::uint32_t g_moviePlayerValue09;
extern std::uint8_t g_moviePlayerFlag0B;
extern char g_moviePlayerObject;
void InitMoviePlayerObject(void* a_object);
class Main {
public:
    static Main* singleton;
    std::uint8_t unknown00[0x28];  // 00
    std::uint32_t unk28;           // 28
};

class BGSMoviePlayer : public MoviePlayer
{
public:
    virtual void Unk_06();  // compared: 0x645120
    virtual void Unk_05();  // compared: 0x645130
    virtual std::uint32_t Unk_0A();  // compared: 0x644920
    virtual void Unk_07();  // compared: 0x6448d0
    virtual std::uint32_t Unk_09();  // compared: 0x644910
    virtual std::uint8_t Unk_0B();  // compared: 0x644930
    virtual std::uint32_t Unk_0C();  // compared: 0x644940

    // TODO members: replace part of the padding with the members the bodies read,
    // keeping every offset and the size check true.
    std::uint8_t unknown58[0x68];  // 58
};
static_assert(sizeof(BGSMoviePlayer) == 0xC0, "BGSMoviePlayer size");
