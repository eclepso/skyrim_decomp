// TESObjectACTI declarations for build sse-steam-1-7-104.
// Code origin: declarations written by hand from the local listings and the community headers; the bodies are in the matching .cpp.
// Labels: v2
// Task: p177fb-ec14f6c6
// Source exposure: mixed (names and declarations from community headers; the listing of the pinned image).
// TESObjectACTI, TESObjectACTI::InitializeData: GUESS(low)
// TESObjectACTI fields: STANDIN GUESS(low)
// Supporting types: STANDIN GUESS(low)
// GetWaterType, GetIgnoredBySandbox, IsWater: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e832f263dbef44e44cbe2936622a02f91a, MIT); signatures as declared there
// TESWaterForm: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e832f263dbef44e44cbe2936622a02f91a, MIT)
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

class TESWaterForm;
class TESObjectACTI {
public: virtual TESWaterForm* GetWaterType() const; virtual bool GetIgnoredBySandbox() const; virtual bool IsWater() const; void InitializeData();
private: std::uint8_t pad[0xa0]; void* soundLoop; void* soundActivate; TESWaterForm* waterForm; std::uint16_t flags;
};
