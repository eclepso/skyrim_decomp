// BGSTalkingActivator functions for build sse-steam-1-7-104.
//
// Labels: v2
// Task: contrib-bgstalkingactivator
// Code origin: InitializeData, Get/SetObjectVoiceType bodies written from the local listings; declarations added to the existing unit header.
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
// Evidence: findings/fifth-batch-selection.md
// Recipe: reconstruction/recipes/msvc-19.16.27054-o2.json (compile this file alone).
// Drafted by Hinkiii, assisted by claude-sonnet-5-5, starting from
// a tools/skeleton.py skeleton.
// Compared functions:
//   RVA 0x2671e0, 16 bytes: BGSTalkingActivator::InitializeData
//   RVA 0x267810, 8 bytes: BGSTalkingActivator::SetObjectVoiceType
//   RVA 0x2676a0, 8 bytes: BGSTalkingActivator::GetObjectVoiceType
// Adapted bodies: none
// A byte match shows that this source and recipe produce the checked code; it does not verify the
// community names or that the original source looked like this.
// Build: sse-steam-1-7-104; RVA 0x267530; 53 bytes
// Labels: v2
// Source exposure: mixed
// Origin: independently decoded target, anonymous sibling and public declarations.
// Drafted by gpt-6.1-terra
// Recipe: reconstruction/recipes/msvc-19.16.27054-o2.json
// Evidence: findings/ghidra-import.md
// BGSTalkingActivator::Revert: SIBLING(fo4-private@1b765c70, author-permission); adapted to target observations.
// Sibling source: fo4-private@1b765c70 src/Shared/TESForms/Objects/BGSTalkingActivator.cpp:168
// BGSTalkingActivator, TESObjectACTI: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e832f263dbef44e44cbe2936622a02f91a, MIT); declarations adapted from include/RE/T/TESObjectACTI.h, include/RE/T/TESBoundObject.h, include/RE/T/TESForm.h and public component headers.
// names: GUESS(low); names and original signatures are tentative.
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
#include "BGSTalkingActivator.h"
void BGSTalkingActivator::InitializeData() { voiceType = nullptr; TESObjectACTI::InitializeData(); }
void BGSTalkingActivator::SetObjectVoiceType(BGSVoiceType* a_voice) { voiceType = a_voice; }
BGSVoiceType* BGSTalkingActivator::GetObjectVoiceType() const { return voiceType; }
void BGSTalkingActivator::Revert(BGSLoadFormBuffer* buffer) { TESForm::Revert(buffer); if ((unsigned char)(buffer->oldChangeFlags >> 23) & 1) tempRef = nullptr; }
