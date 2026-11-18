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
#pragma once
class Component { public: virtual ~Component(); };
class TESForm : public Component { public: void* files; unsigned formFlags, id; unsigned short inGameFlags; unsigned char type, pad; unsigned pad2; void Revert(void*); };
struct ShortPoint { short x,y,z; };
class TESBoundObject : public TESForm { public: ShortPoint min, max; unsigned pad; };
class TESBoundAnimObject : public TESBoundObject {};
class TESFullName : public Component { public: const char* name; };
class TESModel : public Component { public: const char* model; void* textures; unsigned* addons; unsigned short numTextures, numAddons; unsigned pad; };
class TESModelTextureSwap : public TESModel { public: void* alternateTextures; unsigned count, pad; };
class TESMagicTargetForm {};
class BGSDestructibleObjectForm : public Component { public: void* data; };
class BGSOpenCloseForm { public: virtual ~BGSOpenCloseForm(); };
class BGSKeywordForm : public Component { public: void** keywords; unsigned count; };
class TESObjectACTI : public TESBoundAnimObject, public TESFullName, public TESModelTextureSwap, public TESMagicTargetForm, public BGSDestructibleObjectForm, public BGSOpenCloseForm, public BGSKeywordForm { public: void* soundLoop; void* soundActivate; void* waterForm; unsigned short flags, padc2; unsigned padc4; void ClearData(); virtual void InitializeData(); };
template<class T> struct Array { T* data; unsigned capacity, allocatorPad, size, sizePad; void Deallocate(); void Clear() { if (data) Deallocate(); size = 0; } };
class BGSLoadGameBuffer { public: virtual ~BGSLoadGameBuffer(); void* buffer; unsigned long long unknown10; unsigned unknown18, unknown1c, unknown20, bufferPosition; }; struct BGSLoadFormData { unsigned formID, size, uncompressedSize, pad; TESForm* form; unsigned changeFlags, oldChangeFlags, flags; unsigned char pad22, version; }; class BGSLoadFormBuffer : public BGSLoadGameBuffer, public BGSLoadFormData {};
// BGSTalkingActivator::GetObjectVoiceType: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e832f263dbef44e44cbe2936622a02f91a, MIT); signature as declared on TESBoundObject
// BGSTalkingActivator::InitializeData, TESObjectACTI::InitializeData: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e832f263dbef44e44cbe2936622a02f91a, MIT); target 0x279750 for the base call
// BGSTalkingActivator::SetObjectVoiceType: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e832f263dbef44e44cbe2936622a02f91a, MIT); signature as declared on TESBoundObject
// voiceType: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e832f263dbef44e44cbe2936622a02f91a, MIT); member read at offset 0xD0 in this unit's stand-in layout
class BGSVoiceType;
class BGSTalkingActivator : public TESObjectACTI { public: void InitializeData() override; virtual void SetObjectVoiceType(BGSVoiceType*); virtual BGSVoiceType* GetObjectVoiceType() const; void* tempRef; BGSVoiceType* voiceType; void Revert(BGSLoadFormBuffer*); };
