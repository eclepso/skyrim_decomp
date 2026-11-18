// NiSkinInstance functions for build sse-steam-1-7-104.
//
// Labels: v2
// Task: contrib-niskininstance
// Code origin: Reconstruction by v-macrev with Codex assistance from pinned-image analysis,
// informed by the cited sibling serialization and comparison shapes.
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
// Recipe: reconstruction/recipes/msvc-19.16.27054-o2-root-includes.json (compile this file alone).
// Drafted by v-macrev, assisted by gpt-6.2-sol, starting from
// a tools/skeleton.py skeleton.
// Compared functions:
//   RVA 0xef6f50, 52 bytes: NiSkinInstance::~NiSkinInstance
//   RVA 0xf096a0, 51 bytes: NiSkinInstance::LoadBinary
//   RVA 0xf09820, 167 bytes: NiSkinInstance::RegisterStreamables
//   RVA 0xf098d0, 186 bytes: NiSkinInstance::SaveBinary
//   RVA 0xf09990, 112 bytes: NiSkinInstance::IsEqual
//   RVA 0xf09ca0, 9 bytes: NiSkinInstance::Unk_25
//   RVA 0xf0a690, 91 bytes: NiSkinInstance::Ctor
// CI hash: 0xef6f50 ??_GNiSkinInstance@@UEAAPEAXI@Z
// CI hash: 0xf096a0 ?LoadBinary@NiSkinInstance@@UEAAXAEAVNiStream@@@Z
// CI hash: 0xf09820 ?RegisterStreamables@NiSkinInstance@@UEAA_NAEAVNiStream@@@Z
// CI hash: 0xf098d0 ?SaveBinary@NiSkinInstance@@UEAAXAEAVNiStream@@@Z
// CI hash: 0xf09990 ?IsEqual@NiSkinInstance@@UEAA_NPEAVNiObject@@@Z
// CI hash: 0xf09ca0 ?Unk_25@NiSkinInstance@@UEAAXXZ
// CI hash: 0xf0a690 ?Ctor@NiSkinInstance@@QEAAPEAV1@XZ
// Sibling source: momusdigital/fnv_decomp@91e1b6e8 src/gamebryo2.2/corelibs/nimain/niskininstance.cpp:8
// Sibling source: momusdigital/fnv_decomp@91e1b6e8 src/gamebryo2.2/corelibs/nimain/niskininstance.cpp:32
// Sibling source: momusdigital/fnv_decomp@91e1b6e8 src/gamebryo2.2/corelibs/nimain/niskininstance.cpp:58
// Sibling source: momusdigital/fnv_decomp@91e1b6e8 src/gamebryo2.2/corelibs/nimain/niskininstance.cpp:187
// Adapted bodies: SaveBinary, RegisterStreamables and IsEqual use the cited sibling control
// flow with layout, call sites and argument order checked against the pinned image.
// LoadBinary was reconstructed from the pinned image. The stream writer is credited in the header.
// A byte match covers the checked code and does not verify the community names.
#include "NiSkinInstance.h"

#include <cstddef>
#include <new>

// InitializeCriticalSection: OBSERVED; named Windows import for the instance lock
// lockStorage, UpdatePartition, partition: GUESS(low)
extern "C" __declspec(dllimport) void InitializeCriticalSection(SkinInstanceLock* lockStorage) noexcept;
void UpdatePartition(NiObject* partition);

SkinInstanceLock::SkinInstanceLock() noexcept
{
    InitializeCriticalSection(this);
}

// The complete destructor is external. Its declaration lets the compiler emit the deleting
// destructor beside the constructor's virtual table.
NiSkinInstance::NiSkinInstance() :
    rootParent(nullptr),
    bones(nullptr),
    boneWorldTransforms(nullptr),
    numMatrices(0),
    numRegisters(0),
    allocatedSize(0),
    boneMatrices(nullptr),
    prevBoneMatrices(nullptr),
    skinToWorldWorldToSkinMatrix(nullptr)
{
}

NiSkinInstance* NiSkinInstance::Ctor()
{
    return new (this) NiSkinInstance;
}

void NiSkinInstance::LoadBinary(NiStream& streamRef)
{
    NiObject::LoadBinary(streamRef);
    streamRef.LoadLinkID();
    streamRef.LoadLinkID();
    streamRef.LoadLinkID();
    streamRef.SkipLinkIDs();
}

// boneCount, index, other: GUESS(low)
bool NiSkinInstance::RegisterStreamables(NiStream& streamRef)
{
    if (!NiObject::RegisterStreamables(streamRef)) {
        return false;
    }
    skinData.get()->RegisterStreamables(streamRef);
    if (skinPartition.get()) {
        skinPartition.get()->RegisterStreamables(streamRef);
    }
    rootParent->RegisterStreamables(streamRef);

    const std::uint32_t boneCount = skinData.get()->bones;
    for (std::uint32_t index = 0; index < boneCount; ++index) {
        bones[index]->RegisterStreamables(streamRef);
    }
    return true;
}

void NiSkinInstance::SaveBinary(NiStream& streamRef)
{
    NiObject::SaveBinary(streamRef);
    streamRef.SaveLinkID(skinData.get());
    streamRef.SaveLinkID(skinPartition.get());
    streamRef.SaveLinkID(rootParent);
    std::uint32_t boneCount = skinData.get()->bones;
    streamRef.oStr->write(&boneCount, 1);
    for (std::uint32_t index = 0; index < boneCount; ++index) {
        streamRef.SaveLinkID(bones[index]);
    }
}

bool NiSkinInstance::IsEqual(NiObject* comparedObject)
{
    if (!NiObject::IsEqual(comparedObject)) {
        return false;
    }
    auto* other = static_cast<NiSkinInstance*>(comparedObject);
    if (!skinData.get()->IsEqual(other->skinData.get())) {
        return false;
    }
    if (skinPartition.get() && !skinPartition.get()->IsEqual(other->skinPartition.get())) {
        return false;
    }
    if (!skinPartition.get() && other->skinPartition.get()) {
        return false;
    }
    return true;
}

void NiSkinInstance::Unk_25()
{
    UpdatePartition(skinPartition.get());
}
