// TESFurniture declarations for build sse-steam-1-7-104 (standalone unit for the functions compared in the matching .cpp).
// Labels: v2
// Code origin: declarations extended by hand from the local listings; names follow the community headers.
// Source exposure: mixed
// Recipe: reconstruction/recipes/msvc-19.16.27054-o2.json
// Evidence: findings/ghidra-import.md
// TESFurniture, TESObjectACTI: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e832f263dbef44e44cbe2936622a02f91a, MIT); declarations adapted from include/RE/T/TESObjectACTI.h, include/RE/T/TESBoundObject.h, include/RE/T/TESForm.h and public component headers.
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
// TESFurniture::InitializeData, TESFurniture::Clone3D: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e832f263dbef44e44cbe2936622a02f91a, MIT); names only, the bodies are written from the target listing
// g_furnitureCloneFlag: GUESS(low); global byte at address 0x20b6130 that gates the extra step in Clone3D
// TESFurniture::Unk26f900: GUESS(low); address 0x26f900, called with the cloned node when the flag is set
// dwordE4, qwordE8, unkE0: GUESS(low); members the compared InitializeData clears
#pragma once
class Component { public: virtual ~Component(); };
class TESForm : public Component { public: void* files; unsigned formFlags, id; unsigned short inGameFlags; unsigned char type, pad; unsigned pad2; void Revert(void*); };
struct ShortPoint { short x,y,z; };
class NiAVObject; class TESObjectREFR;
class TESBoundObject : public TESForm { public: virtual NiAVObject* Clone3D(TESObjectREFR* a_ref); ShortPoint min, max; unsigned pad; };
class TESBoundAnimObject : public TESBoundObject {};
class TESFullName : public Component { public: const char* name; };
class TESModel : public Component { public: const char* model; void* textures; unsigned* addons; unsigned short numTextures, numAddons; unsigned pad; };
class TESModelTextureSwap : public TESModel { public: void* alternateTextures; unsigned count, pad; };
class TESMagicTargetForm {};
class BGSDestructibleObjectForm : public Component { public: void* data; };
class BGSOpenCloseForm { public: virtual ~BGSOpenCloseForm(); };
class BGSKeywordForm : public Component { public: void** keywords; unsigned count; };
class TESObjectACTI : public TESBoundAnimObject, public TESFullName, public TESModelTextureSwap, public TESMagicTargetForm, public BGSDestructibleObjectForm, public BGSOpenCloseForm, public BGSKeywordForm { public: void* soundLoop; void* soundActivate; void* waterForm; unsigned short flags, padc2; unsigned padc4; void ClearData(); virtual void InitializeData(); };
template<class T> struct Array { T* data; unsigned capacity, allocatorPad, size, sizePad; void Deallocate(); void Clear() { if (data) { Deallocate(); size = 0; } } };
class TESFurniture : public TESObjectACTI { public: struct EntryPointData; Array<EntryPointData> entryPointDataArray; unsigned unkE0, dwordE4; void* qwordE8; void ClearData(); void InitializeData() override; NiAVObject* Clone3D(TESObjectREFR* a_ref) override; void Unk26f900(NiAVObject* a_node); };
extern bool g_furnitureCloneFlag;
