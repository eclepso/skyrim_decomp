// NiParticleSystem declarations for build sse-steam-1-7-104.
//
// Labels: v2
// Task: contrib-niparticlesystem
// Code origin: declarations written for this unit from CommonLibSSE-NG names and layouts; the
// stand-ins declare only what the compared code needs.
// Source exposure: mixed (community declarations and the contributor-owned pack;
// bases, sizes and slots are community hypotheses).
// Size agreement alone proves neither fields nor ownership.
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
// Started from a tools/skeleton.py skeleton: stand-ins carry only what the compared code needs, and
// community names are unverified.
// Base form: NiParticles over BSGeometry, local stand-ins of the community 0x168 and 0x158 sizes over a
// minimal NiObject; the NiObjectNET and NiAVObject layers are not modelled, and BSGeometry holds the
// NiAVObject members the compared code reads. NiObject declares the virtual slots up to 0x1C because
// the compared code calls slots 0x1A and 0x1C of modifiers; later slot order is not modelled.
// NiParticleSystem, NiParticleSystem::LoadBinary, NiParticleSystem::RegisterStreamables, NiParticleSystem::SaveBinary, NiParticleSystem::IsEqual, NiParticleSystem::UpdateDownwardPass, NiParticleSystem::UpdateSelectedDownwardPass, NiParticleSystem::SetSelectiveUpdateFlags, NiParticleSystem::~NiParticleSystem (implicit here), NiParticles::LoadBinary, NiParticles::RegisterStreamables, NiParticles::SaveBinary, NiParticles::IsEqual, NiParticles::~NiParticles, BSGeometry::SetSelectiveUpdateFlags, BSGeometry::UpdateDownwardPass, BSGeometry::UpdateSelectedDownwardPass: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
#pragma once

#include <cstdint>
#include <cstddef>

class NiObject;

// NiBinaryStream: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); only the members the compared code reads
class NiBinaryStream
{
public:
    // ReadFn, WriteFn: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
    using ReadFn = std::uint32_t(NiBinaryStream* a_this, void* a_buffer, std::uint32_t a_bytes, std::uint32_t* a_componentSizes, std::uint32_t a_numComponents);
    using WriteFn = std::uint32_t(NiBinaryStream* a_this, const void* a_buffer, std::uint32_t a_bytes, std::uint32_t* a_componentSizes, std::uint32_t a_numComponents);

    virtual ~NiBinaryStream();  // 00

    // _absoluteCurrentPos, _readFn, _writeFn: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
    std::uint32_t _absoluteCurrentPos;  // 08
    // pad0C: GUESS(low)
    std::uint32_t pad0C;  // 0C
    ReadFn* _readFn;  // 10
    WriteFn* _writeFn;  // 18
};
static_assert(sizeof(NiBinaryStream) == 0x20, "NiBinaryStream size");

// NiStream: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); the virtual slots up to SaveLinkID and a prefix view up to the two stream pointers
class NiStream
{
public:
    // ~NiStream, Load1, Load2, Load3, Save1, Save2, Save3, Unk_07, RegisterFixedString, RegisterSaveObject, ChangeObject, GetLinkIDFromObject, SaveLinkID: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); declared only, parameters not modelled except SaveLinkID's
    virtual ~NiStream();  // 00
    virtual void Load1();  // 01
    virtual void Load2();  // 02
    virtual void Load3();  // 03
    virtual void Save1();  // 04
    virtual void Save2();  // 05
    virtual void Save3();  // 06
    virtual void Unk_07();  // 07
    virtual void RegisterFixedString();  // 08
    virtual void RegisterSaveObject();  // 09
    virtual void ChangeObject();  // 0A
    virtual void GetLinkIDFromObject();  // 0B
    virtual void SaveLinkID(const NiObject* a_object);  // 0C

    // SkipLinkIDs: GUESS(low); the stream helper the load path calls, declared only, bound by its public name
    void SkipLinkIDs();

    // unk008: GUESS(low); members not used here
    std::uint8_t unk008[0x290];  // 008
    // iStr, oStr: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
    NiBinaryStream* iStr;  // 298
    NiBinaryStream* oStr;  // 2A0
};

// BSFixedString: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); compared by its data pointer
class BSFixedString
{
public:
    // _data: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
    const char* _data;  // 0

    bool operator==(const BSFixedString& a_rhs) const { return _data == a_rhs._data; }
};

// NiObject: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); the virtual slots up to IsEqual
class NiObject
{
public:
    virtual ~NiObject();  // 00
    // Unk_01..Unk_17: GUESS(low); slot placeholders, not used here
    virtual void Unk_01();
    virtual void Unk_02();
    virtual void Unk_03();
    virtual void Unk_04();
    virtual void Unk_05();
    virtual void Unk_06();
    virtual void Unk_07();
    virtual void Unk_08();
    virtual void Unk_09();
    virtual void Unk_0A();
    virtual void Unk_0B();
    virtual void Unk_0C();
    virtual void Unk_0D();
    virtual void Unk_0E();
    virtual void Unk_0F();
    virtual void Unk_10();
    virtual void Unk_11();
    virtual void Unk_12();
    virtual void Unk_13();
    virtual void Unk_14();
    virtual void Unk_15();
    virtual void Unk_16();
    virtual void Unk_17();
    // LoadBinary, LinkObject, RegisterStreamables, SaveBinary, IsEqual: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
    virtual void LoadBinary(NiStream& a_stream);  // 18
    virtual void LinkObject(NiStream& a_stream);  // 19
    virtual bool RegisterStreamables(NiStream& a_stream);  // 1A
    virtual void SaveBinary(NiStream& a_stream);  // 1B
    virtual bool IsEqual(NiObject* a_object);  // 1C

    // unk08: GUESS(low); the reference count, not used here
    std::uint32_t unk08;  // 08
    std::uint32_t pad0C;  // 0C
};
static_assert(sizeof(NiObject) == 0x10, "NiObject size");

// NiPSysModifier: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); only the name the compared code reads
class NiPSysModifier : public NiObject
{
public:
    // name: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
    BSFixedString name;  // 10
};

// NiPointer: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); the raw pointer only
template <class T>
class NiPointer
{
public:
    // _ptr: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
    T* _ptr;  // 0

    T* get() const { return _ptr; }
};

// NiTListItem: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
template <class T>
class NiTListItem
{
public:
    // next, prev, element: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
    NiTListItem* next;  // 00
    NiTListItem* prev;  // 08
    T element;  // 10
};

// NiTPointerList: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); not a template here: the NiTPointerList<NiPointer<NiPSysModifier>> instance, with the NiTListBase members
class NiTPointerList
{
public:
    // NiTPointerList::~NiTPointerList: GUESS(low); the list destructor the compared destructor calls, declared only, bound by address
    ~NiTPointerList();

    // AntiBloatAllocator, size: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
    struct AntiBloatAllocator
    {
        std::uint32_t size;  // 0
    };

    // head, tail, allocator: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
    NiTListItem<NiPointer<NiPSysModifier>>* head;  // 00
    NiTListItem<NiPointer<NiPSysModifier>>* tail;  // 08
    AntiBloatAllocator allocator;  // 10
};
static_assert(sizeof(NiTPointerList) == 0x18, "NiTPointerList size");

// NiTransform: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); opaque storage of the community size
class NiTransform
{
public:
    // NiTransformHelper: GUESS(low); the member function the load path calls on the world transform, declared only, bound by address
    void NiTransformHelper();

    // unk00: GUESS(low); rotate, translate and scale, not modelled
    std::uint8_t unk00[0x34];  // 00
};
static_assert(sizeof(NiTransform) == 0x34, "NiTransform size");

// NiUpdateData: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
class NiUpdateData
{
public:
    // time, flags: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); flags is a plain word here
    float time;  // 0
    std::uint32_t flags;  // 4
};
static_assert(sizeof(NiUpdateData) == 0x8, "NiUpdateData size");

// BSGeometry: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); the community 0x158 size, with the NiAVObject members the compared code reads
class BSGeometry : public NiObject
{
public:
    // SetSelectiveUpdateFlags, UpdateDownwardPass, UpdateSelectedDownwardPass: declared only; the compared passes tail-call the last two, bound by address
    virtual void SetSelectiveUpdateFlags(bool& a_selectiveUpdate, bool a_selectiveUpdateTransforms, bool& a_rigid);
    virtual void UpdateDownwardPass(NiUpdateData& a_data, std::uint32_t a_arg2);
    virtual void UpdateSelectedDownwardPass(NiUpdateData& a_data, std::uint32_t a_arg2);

    // unk010: GUESS(low); NiObjectNET and NiAVObject members, not used here
    std::uint8_t unk010[0x6C];  // 010
    // world, flags: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); NiAVObject members
    NiTransform world;  // 07C
    // unk0B0: GUESS(low); members not used here
    std::uint8_t unk0B0[0x44];  // 0B0
    std::uint32_t flags;  // 0F4
    // unk0F8: GUESS(low); NiAVObject and BSGeometry members, not used here
    std::uint8_t unk0F8[0x60];  // 0F8
};
static_assert(sizeof(BSGeometry) == 0x158, "BSGeometry size");

// NiParticles: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); the community 0x168 size
class NiParticles : public BSGeometry
{
public:
    // Declared only; the emission constructor of NiParticleSystem calls it.
    NiParticles();
    // NiParticles::~NiParticles: declared only; the compared destructor calls it, bound by address
    ~NiParticles() override;
    // LoadBinary, RegisterStreamables, SaveBinary, IsEqual: declared only; the compared overrides call them directly, bound by address
    void LoadBinary(NiStream& a_stream) override;
    bool RegisterStreamables(NiStream& a_stream) override;
    void SaveBinary(NiStream& a_stream) override;
    bool IsEqual(NiObject* a_object) override;

    // unk158: GUESS(low); NiParticles members, not used here
    std::uint8_t unk158[0x10];  // 158
};
static_assert(sizeof(NiParticles) == 0x168, "NiParticles size");

class NiParticleSystem : public NiParticles
{
public:
    // Defined empty only to emit the vftable, not compared. The destructor is implicit; its scalar
    // deleting destructor is compared: 0xf9a140
    NiParticleSystem();
    void LoadBinary(NiStream& a_stream) override;  // compared: 0xf98f50
    bool RegisterStreamables(NiStream& a_stream) override;  // compared: 0xf99260
    void SaveBinary(NiStream& a_stream) override;  // compared: 0xf992c0
    bool IsEqual(NiObject* a_object) override;  // compared: 0xf99390
    void SetSelectiveUpdateFlags(bool& a_selectiveUpdate, bool a_selectiveUpdateTransforms, bool& a_rigid) override;  // compared: 0xf99ba0
    void UpdateDownwardPass(NiUpdateData& a_data, std::uint32_t a_arg2) override;  // compared: 0xf99a30
    void UpdateSelectedDownwardPass(NiUpdateData& a_data, std::uint32_t a_arg2) override;  // compared: 0xf99aa0

    // UpdateSystemForPass: GUESS(low); the helper both update passes call, declared only, bound by address
    void UpdateSystemForPass(NiUpdateData& a_data);
    // GetModifierByName: GUESS(low); the lookup IsEqual makes in the other system
    NiPSysModifier* GetModifierByName(const BSFixedString& a_name);

    // modifierList, unk180, unk184, unk188, lastUpdate, resetSystem, dynamicBounds, isWorldspace: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
    NiTPointerList modifierList;  // 168
    float unk180;  // 180
    float unk184;  // 184
    float unk188;  // 188
    float lastUpdate;  // 18C
    bool resetSystem;  // 190
    bool dynamicBounds;  // 191
    bool isWorldspace;  // 192
    // pad193, pad194: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
    std::uint8_t pad193;  // 193
    std::uint32_t pad194;  // 194
};
static_assert(sizeof(NiParticleSystem) == 0x198, "NiParticleSystem size");
