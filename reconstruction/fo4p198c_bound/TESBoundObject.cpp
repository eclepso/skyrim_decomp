// TESBoundObject functions for build sse-steam-1-7-104.
//
// Labels: v2
// Task: contrib-tesboundobject
// Code origin: GetObjectVoiceType body written from the local listing (returns null); declarations adapted from the existing unit header.
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
// Evidence: findings/p92-unit-supply-selection.md
// Recipe: reconstruction/recipes/msvc-19.16.27054-o2.json (compile this file alone).
// Drafted by Hinkiii, assisted by claude-sonnet-5-5, starting from
// a tools/skeleton.py skeleton.
// Compared functions:
//   RVA 0x1467c0, 3 bytes: TESBoundObject::GetObjectVoiceType
// Adapted bodies: none
// A byte match shows that this source and recipe produce the checked code; it does not verify the
// community names or that the original source looked like this.
// Build: sse-steam-1-7-104
// Labels: v2
// Source exposure: mixed (local target analysis, public declarations and permitted sibling).
// Origin: reconstructed from target and sibling hints.
// Drafted by gpt-6.1-terra
// Recipe: reconstruction/recipes/msvc-19.16.27054-o2.json
// Evidence: findings/ghidra-import.md
// names: GUESS(low); signatures and type names are hypotheses.
// TESBoundObject::Clone3D: SIBLING(fo4-private@1b765c70, author-permission); adapted virtual forwarding.
// TESBoundObject::ReplaceModel: SIBLING(fo4-private@1b765c70, author-permission); adapted virtual forwarding.
// Sibling source: fo4-private@1b765c70 src/Shared/TESForms/Objects/TESObject.cpp:92
// Sibling source: fo4-private@1b765c70 src/Shared/TESForms/Objects/TESObject.cpp:105
// TESObject and TESBoundObject: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); adapted declarations.
// RVA 0x277e00, 13 bytes; RVA 0x278e00, 47 bytes.
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
#include "TESBoundObject.h"
NiAVObject* TESBoundObject::Clone3D(TESObjectREFR* ref) { return Clone3D(ref, false); }
bool TESBoundObject::ReplaceModel() { return ReplaceModel(TESModel::GetModel(this)); }
BGSVoiceType* TESBoundObject::GetObjectVoiceType() const { return nullptr; }
