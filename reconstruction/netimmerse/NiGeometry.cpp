// NiGeometry functions for build sse-steam-1-7-104.
//
// Labels: v2
// Task: contrib-nigeometry
// Code origin: Reconstruction by v-macrev with Codex assistance from pinned-image analysis,
// with the reserved-field write structure in SaveBinary adapted from the cited sibling.
// Source exposure: mixed (community declarations, sibling context, and local analysis of the pinned image).
// NiGeometry::SaveBinary, NiGeometry::RegisterStreamables, NiGeometry::SetSelectiveUpdateFlags: SIBLING(momusdigital/fnv_decomp@91e1b6e8, no-licence); SaveBinary adapts the reserved-field write structure, the other two were consulted for context
// The MIT notice below covers only the material adapted from CharmedBaryon/CommonLibSSE-NG@b93280e (MIT).
// It does not cover the sibling-derived material labelled above, which carries no licence grant.
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
// Recipe: reconstruction/recipes/msvc-19.16.27054-o2-root-includes.json (compile this file alone).
// Drafted by v-macrev, assisted by gpt-6.2-sol, starting from
// a tools/skeleton.py skeleton.
// Compared functions:
//   RVA 0xf0b140, 3 bytes: NiGeometry::Unk_36
//   RVA 0xf0ad10, 140 bytes: NiGeometry::RegisterStreamables
//   RVA 0xf0adb0, 256 bytes: NiGeometry::SaveBinary
//   RVA 0xf0b010, 49 bytes: NiGeometry::UpdateDownwardPass
//   RVA 0xf0b050, 56 bytes: NiGeometry::UpdateSelectedDownwardPass
//   RVA 0xf0b150, 138 bytes: NiGeometry::Unk_37
//   RVA 0xf0b7f0, 90 bytes: NiGeometry::Unk_3A
//   RVA 0xf0b9c0, 78 bytes: NiGeometry::PostLinkObject
//   RVA 0xf0ba20, 75 bytes: NiGeometry::SetSelectiveUpdateFlags
// CI hash: 0xf0ad10 ?RegisterStreamables@NiGeometry@@QEAA_NAEAVNiStream@@@Z
// CI hash: 0xf0adb0 ?SaveBinary@NiGeometry@@QEAAXAEAVNiStream@@@Z
// CI hash: 0xf0b010 ?UpdateDownwardPass@NiGeometry@@QEAAXAEAVNiUpdateData@@I@Z
// CI hash: 0xf0b050 ?UpdateSelectedDownwardPass@NiGeometry@@QEAAXAEAVNiUpdateData@@I@Z
// CI hash: 0xf0b140 ?Unk_36@NiGeometry@@QEAAIXZ
// CI hash: 0xf0b150 ?Unk_37@NiGeometry@@QEAAXPEAVGeometryRefView@@@Z
// CI hash: 0xf0b7f0 ?Unk_3A@NiGeometry@@QEAAPEAXXZ
// CI hash: 0xf0b9c0 ?PostLinkObject@NiGeometry@@QEAAXAEAVNiStream@@@Z
// CI hash: 0xf0ba20 ?SetSelectiveUpdateFlags@NiGeometry@@QEAAXAEA_N_N0@Z
// Sibling source: momusdigital/fnv_decomp@91e1b6e8 src/gamebryo2.2/corelibs/nimain/nigeometry.cpp:446 (SetSelectiveUpdateFlags).
// Sibling source: momusdigital/fnv_decomp@91e1b6e8 src/gamebryo2.2/corelibs/nimain/nigeometry.cpp:640 (RegisterStreamables).
// Sibling source: momusdigital/fnv_decomp@91e1b6e8 src/gamebryo2.2/corelibs/nimain/nigeometry.cpp:1025 (SaveBinary).
// Adapted bodies: SaveBinary uses the cited sibling's reserved-field write structure and the
// adapted CommonLibSSE-NG write helpers documented in NiGeometry.h. The link and write sequence
// was checked in the pinned image. The other cited sibling functions were consulted for context.
// A byte match shows that this source and recipe produce the checked code; it does not verify the
// community names or that the original source looked like this.
#include <intrin.h>
#include "NiGeometry.h"

namespace
{
// LayoutMember, a_object, offset, Field, Owner: GUESS(low); observed fields inside opaque base storage
template <class Field, class Owner>
Field& LayoutMember(Owner* a_object, std::size_t offset)
{
    return *reinterpret_cast<Field*>(reinterpret_cast<unsigned char*>(a_object) + offset);
}

// IsBitSet, a_flags, a_bit, flagsWord, controllers, collision, streamRef, stream, firstReservedWord, secondReservedWord, reservedByte, oldSkin, update, mode, effect, property: GUESS(low)
bool IsBitSet(std::uint32_t a_flags, unsigned a_bit)
{
    return ((a_flags >> a_bit) & 1) != 0;
}
}

// BaseRegisterStreamables, BaseSaveBinary, BaseUpdateDownwardPass, BaseUpdateSelectedDownwardPass, BasePostLinkObject, BaseSetSelectiveUpdateFlags, self, a_mode, a_update, a_transforms, rigidResult: GUESS(low); stand-ins for direct calls to base implementations
bool BaseRegisterStreamables(NiGeometry* self, NiStream& streamRef);
void BaseSaveBinary(NiGeometry* self, NiStream& streamRef);
void BaseUpdateDownwardPass(NiGeometry* self, NiUpdateData& updateData, std::uint32_t a_mode);
void BaseUpdateSelectedDownwardPass(NiGeometry* self, NiUpdateData& updateData, std::uint32_t a_mode);
void BasePostLinkObject(NiGeometry* self, NiStream& streamRef);
void BaseSetSelectiveUpdateFlags(NiGeometry* self, bool& a_update, bool a_transforms, bool& rigidResult);

// QuerySkin, a_skin, a_mode: GUESS(low); out-of-line skin query
void* QuerySkin(GeometryRefView* a_skin, std::uint32_t a_mode);

bool NiGeometry::RegisterStreamables(NiStream& streamRef)
{
    if (!BaseRegisterStreamables(this, streamRef)) {
        return false;
    }
    m_spSkinInstance->RegisterObjectStreamables(streamRef);
    if (m_spModelData) {
        m_spModelData->RegisterObjectStreamables(streamRef);
    }
    if (m_spEffectState) {
        m_spEffectState->RegisterObjectStreamables(streamRef);
    }
    if (m_spPropertyState) {
        m_spPropertyState->RegisterObjectStreamables(streamRef);
    }
    return true;
}

void NiGeometry::SaveBinary(NiStream& streamRef)
{
    BaseSaveBinary(this, streamRef);
    auto& stream = reinterpret_cast<GeometryStreamView&>(streamRef);
    stream.WriteObjectLink(m_spSkinInstance);
    stream.WriteObjectLink(m_spModelData);

    // The format keeps two reserved words and a reserved byte between these link records.
    const std::uint32_t firstReservedWord = 0;
    stream.output->write(&firstReservedWord, 1);
    {
        const std::uint32_t secondReservedWord = 0;
        stream.output->write(&secondReservedWord, 1);
    }
    const std::uint8_t reservedByte = 0;
    stream.output->write(&reservedByte, 1);

    stream.WriteObjectLink(m_spEffectState);
    stream.WriteObjectLink(m_spPropertyState);
}

void NiGeometry::UpdateDownwardPass(NiUpdateData& updateData, std::uint32_t a_mode)
{
    BaseUpdateDownwardPass(this, updateData, a_mode);
    if (updateData.flags & 1) {
        RefreshSkin(updateData);
    }
}

void NiGeometry::UpdateSelectedDownwardPass(NiUpdateData& updateData, std::uint32_t a_mode)
{
    BaseUpdateSelectedDownwardPass(this, updateData, a_mode);
    if (IsBitSet(LayoutMember<std::uint32_t>(this, 0xF4), 3)) {
        RefreshSkin(updateData);
    }
}

std::uint32_t NiGeometry::Unk_36()
{
    return 0;
}

void NiGeometry::Unk_37(GeometryRefView* a_skin)
{
    if (!a_skin) {
        return;
    }
    if (auto* collision = LayoutMember<GeometryCollisionView*>(this, 0x40)) {
        collision->ClearState();
        NiUpdateData update{ 0.0f, 0 };
        LayoutMember<GeometryCollisionView*>(this, 0x40)->UpdateState(update);
    }
    auto* oldSkin = m_spSkinInstance;
    if (oldSkin != a_skin) {
        // The reference count can be shared by other threads, so changes must be atomic.
        _InterlockedIncrement(&a_skin->refCount);
        m_spSkinInstance = a_skin;
        // Delete the former object only if this reference was the last one.
        if (oldSkin && _InterlockedExchangeAdd(&oldSkin->refCount, -1) == 1) {
            oldSkin->Destroy();
        }
    }
}

void* NiGeometry::Unk_3A()
{
    std::uint32_t mode = 0x4000;
    for (auto* controllers = LayoutMember<GeometryControllerView*>(this, 0x18);
         controllers;
         controllers = controllers->nextController) {
        if (controllers->HasVertexEffect()) {
            mode = 0;
            break;
        }
    }
    return QuerySkin(m_spSkinInstance, mode);
}

void NiGeometry::PostLinkObject(NiStream& streamRef)
{
    BasePostLinkObject(this, streamRef);
    if (auto* effect = m_spEffectState) {
        if (effect->propertyControllers) {
            LayoutMember<std::uint32_t>(this, 0xF4) |= 0x40000;
        }
    }
    if (auto* property = m_spPropertyState) {
        if (property->propertyControllers) {
            LayoutMember<std::uint32_t>(this, 0xF4) |= 0x40000;
        }
    }
}

void NiGeometry::SetSelectiveUpdateFlags(bool& a_update, bool a_transforms, bool& rigidResult)
{
    BaseSetSelectiveUpdateFlags(this, a_update, a_transforms, rigidResult);
    if (m_spModelData) {
        auto& flagsWord = LayoutMember<std::uint32_t>(this, 0xF4);
        flagsWord |= 4;
        a_update = true;
        flagsWord |= 2;
        rigidResult = false;
    }
}
