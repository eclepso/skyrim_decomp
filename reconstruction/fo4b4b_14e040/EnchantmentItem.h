// Build: sse-steam-1-7-104; RVA 0x14e040; 11 bytes; RVA 0x14e260; 12 bytes
// Labels: v2
// Source exposure: mixed
// Origin: independently decoded target, anonymous sibling and public declarations.
// Drafted by gpt-6.1-terra
// Recipe: reconstruction/recipes/msvc-19.16.27054-o2.json
// Evidence: findings/ghidra-import.md
// EnchantmentItem::SetCastingType, EnchantmentItem::InitFromChunk: SIBLING(fo4-private@1b765c70, author-permission); adapted to target observations.
// Sibling source: fo4-private@1b765c70 src/Shared/Magic/EnchantmentItem.cpp:74
// Sibling source: fo4-private@1b765c70 src/Shared/Magic/EnchantmentItem.cpp:99
// EnchantmentItem, MagicItem: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e832f263dbef44e44cbe2936622a02f91a, MIT); declarations adapted from include/RE/E/EnchantmentItem.h, include/RE/M/MagicItem.h, include/RE/T/TESBoundObject.h, include/RE/T/TESForm.h, include/RE/T/TESFullName.h and include/RE/B/BGSKeywordForm.h.
// names: GUESS(low); names and original signatures are tentative.
// EnchantmentItem::GetCastingType, EnchantmentItem::GetDelivery, EnchantmentItem::GetSpellType, EnchantmentItem::GetData2: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e832f263dbef44e44cbe2936622a02f91a, MIT); signatures adapted (enum returns shown as int)
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
class Component { public: virtual ~Component(); };
class TESForm : public Component { public: void* files; unsigned flags, id; unsigned short inGameFlags; unsigned char type, pad; unsigned pad2; };
struct ShortPoint { short x,y,z; };
class TESBoundObject : public TESForm { public: ShortPoint min, max; unsigned pad; };
class TESFullName : public Component { public: const char* name; };
class BGSKeywordForm : public Component { public: void** keywords; unsigned count; };
template<class T> struct Array { T* data; unsigned capacity, allocatorPad, size, sizePad; };
class MagicItem : public TESBoundObject, public TESFullName, public BGSKeywordForm { public: Array<void*> effects; int hostileCount; unsigned pad; void* avEffectSetting; unsigned preloadCount, pad2; void* preloadedItem; void SetCastingType(int); };
class TESFile;
class EnchantmentItem : public MagicItem { public:
 struct Data { int costOverride; unsigned flags; int castingType, chargeOverride, delivery, spellType; float chargeTime; unsigned pad; EnchantmentItem* baseEnchantment; void* wornRestrictions; void InitFromChunk(TESFile*); } data;
 void SetCastingType(int); void InitFromChunk(TESFile*);
 virtual int GetCastingType() const; virtual int GetDelivery() const; virtual int GetSpellType() const; virtual Data* GetData2();
};
