// NiGeometry declarations for build sse-steam-1-7-104.
//
// Labels: v2
// Task: contrib-nigeometry
// Code origin: Community declarations and local analysis. Stand-ins describe only the observed fields and calls.
// Source exposure: mixed (community names and pinned-image analysis).
// Adapted bodies: NiBinaryStream::write and NiBinaryStream::binary_write, from CharmedBaryon/CommonLibSSE-NG
// at b93280e (MIT), include/RE/N/NiBinaryStream.h and src/RE/N/NiBinaryStream.cpp.
// The writer is inlined in this view and assumes a configured output callback.
// The MIT notice below covers only the material adapted from CharmedBaryon/CommonLibSSE-NG@b93280e (MIT).
// It does not cover any sibling-derived material; this header declares none.
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
// NiGeometry, NiUpdateData, NiBinaryStream, NiStream: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// NiGeometry::RegisterStreamables, NiGeometry::SaveBinary, NiGeometry::PostLinkObject, NiGeometry::SetSelectiveUpdateFlags, NiGeometry::UpdateDownwardPass, NiGeometry::UpdateSelectedDownwardPass, NiGeometry::Unk_36, NiGeometry::Unk_37, NiGeometry::Unk_3A: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// GeometryStreamView, GeometryControllerView, GeometryRefView, GeometryCollisionView, GeometryPropertyView: STANDIN GUESS(low)
// m_spPropertyState, m_spEffectState, m_spModelData, m_spSkinInstance, unk130: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// flags, time: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// NiBinaryStream::write, NiBinaryStream::binary_write: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// Value, elementsToWrite, count, elementByteCount, total, payloadBytes, sizes, written: GUESS(low)
// unk01 through unk19, unk1B through unk29: GUESS(low); slots unused by this unit
// unk00, unk0C, unk10, refCount, WriteBytes, streamStorage, bytesWritten, output, RefreshSkin, ClearState, UpdateState: GUESS(low)
// Destroy, RegisterObjectStreamables, baseStorage, HasVertexEffect, nextController, propertyControllers, WriteObjectLink: GUESS(low)
// streamRef, updateData, a_mode, a_update, a_transforms, rigidResult, a_skin, a_object: GUESS(low)
#pragma once

#include <cstdint>
#include <cstddef>
class NiStream;

class NiUpdateData
{
public:
    float time;
    std::uint32_t flags;
};
static_assert(sizeof(NiUpdateData) == 8, "NiUpdateData represented size");

class GeometryRefView
{
public:
    virtual ~GeometryRefView();
    virtual void Destroy();
    virtual void unk02();
    virtual void unk03();
    virtual void unk04();
    virtual void unk05();
    virtual void unk06();
    virtual void unk07();
    virtual void unk08();
    virtual void unk09();
    virtual void unk0A();
    virtual void unk0B();
    virtual void unk0C();
    virtual void unk0D();
    virtual void unk0E();
    virtual void unk0F();
    virtual void unk10();
    virtual void unk11();
    virtual void unk12();
    virtual void unk13();
    virtual void unk14();
    virtual void unk15();
    virtual void unk16();
    virtual void unk17();
    virtual void unk18();
    virtual void unk19();
    virtual bool RegisterObjectStreamables(NiStream& streamRef);

    long refCount;
};

// GeometryObjectView: STANDIN GUESS(low); common slots before controller and collision dispatch
class GeometryObjectView : public GeometryRefView
{
public:
    virtual void unk1B();
    virtual void unk1C();
    virtual void unk1D();
    virtual void unk1E();
    virtual void unk1F();
    virtual void unk20();
    virtual void unk21();
    virtual void unk22();
    virtual void unk23();
    virtual void unk24();
};

// Next pointer placement and the predicate slot are observed independently on this build.
class GeometryControllerView : public GeometryObjectView
{
public:
    virtual void unk25();
    virtual void unk26();
    virtual void unk27();
    virtual void unk28();
    virtual void unk29();
    virtual bool HasVertexEffect() const;

    std::uint8_t unk10[0x30];
    GeometryControllerView* nextController;
};

class GeometryCollisionView : public GeometryObjectView
{
public:
    virtual void unk25();
    virtual void UpdateState(NiUpdateData& updateData);
    virtual void ClearState();
};

struct GeometryPropertyView : GeometryRefView
{
    std::uint8_t unk10[8];
    void* propertyControllers;
};

class NiBinaryStream
{
public:
    std::uint32_t binary_write(const void* payloadBytes, std::uint32_t total,
                               std::uint32_t* sizes, std::uint32_t count = 1)
    {
        const std::uint32_t written = WriteBytes(this, payloadBytes, total, sizes, count);
        bytesWritten += written;
        return written;
    }

    template <class Value>
    bool write(const Value* elementsToWrite, std::uint32_t count)
    {
        std::uint32_t elementByteCount = sizeof(Value);
        std::uint32_t total = count * elementByteCount;
        return binary_write(elementsToWrite, total, &elementByteCount) == total;
    }

    virtual ~NiBinaryStream();
    virtual void unk01();
    virtual void unk02();

    // This callback is stored in the stream object rather than called through its vtable.
    std::uint32_t bytesWritten;
    std::uint32_t unk0C;
    void* unk10;
    std::uint32_t (*WriteBytes)(NiBinaryStream*, const void*, std::uint32_t, std::uint32_t*, std::uint32_t);
};
static_assert(sizeof(NiBinaryStream) == 0x20, "NiBinaryStream represented size");

class GeometryStreamView
{
public:
    virtual ~GeometryStreamView();
    virtual void unk01();
    virtual void unk02();
    virtual void unk03();
    virtual void unk04();
    virtual void unk05();
    virtual void unk06();
    virtual void unk07();
    virtual void unk08();
    virtual void unk09();
    virtual void unk0A();
    virtual void unk0B();
    virtual void WriteObjectLink(const GeometryRefView* a_object);

    std::uint8_t streamStorage[0x298];
    NiBinaryStream* output;
};

class NiGeometry
{
public:
    bool RegisterStreamables(NiStream& streamRef);
    void SaveBinary(NiStream& streamRef);
    void UpdateDownwardPass(NiUpdateData& updateData, std::uint32_t a_mode);
    void UpdateSelectedDownwardPass(NiUpdateData& updateData, std::uint32_t a_mode);
    // The original return type is unknown. This stand-in represents the observed register result.
    std::uint32_t Unk_36();
    void Unk_37(GeometryRefView* a_skin);
    void* Unk_3A();
    void PostLinkObject(NiStream& streamRef);
    void SetSelectiveUpdateFlags(bool& a_update, bool a_transforms, bool& rigidResult);

    void RefreshSkin(NiUpdateData& updateData);

    std::uint8_t baseStorage[0x110];
    GeometryPropertyView* m_spPropertyState;
    GeometryPropertyView* m_spEffectState;
    GeometryRefView* m_spSkinInstance;
    GeometryRefView* m_spModelData;
    std::uint64_t unk130;
};
static_assert(sizeof(NiGeometry) == 0x138, "NiGeometry represented size");
