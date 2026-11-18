// NiSkinInstance declarations for build sse-steam-1-7-104.
//
// Labels: v2
// Task: contrib-niskininstance
// Code origin: Local analysis and CommonLibSSE-NG type declarations. The stream write helpers are adapted from
// CharmedBaryon/CommonLibSSE-NG at b93280e, include/RE/N/NiBinaryStream.h and
// src/RE/N/NiBinaryStream.cpp (MIT).
// Source exposure: mixed (community declarations and the contributor-owned pack;
// bases, sizes and slots are community hypotheses).
// Sizes and slots are community hypotheses: verify C1-C5 locally before drafting.
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
// NiSkinInstance, NiSkinInstance::~NiSkinInstance, NiSkinInstance::LoadBinary, NiSkinInstance::RegisterStreamables, NiSkinInstance::SaveBinary, NiSkinInstance::IsEqual, NiSkinInstance::Unk_25, NiSkinInstance::GetRTTI, NiSkinInstance::CreateClone, NiSkinInstance::LinkObject, NiSkinInstance::PostLinkObject: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// NiSkinData, NiBinaryStream, NiStream: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// NiBinaryStream::write, NiBinaryStream::binary_write, NiStream::SaveLinkID, oStr: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// skinData, skinPartition, rootParent, bones, boneWorldTransforms, frameID, numMatrices, numRegisters, allocatedSize, boneMatrices, prevBoneMatrices, skinToWorldWorldToSkinMatrix, lock: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// SkinInstanceLock: STANDIN GUESS(low); opaque platform lock storage initialized by the platform API
// Value, unk10, unk0C, streamStorage, unknownWords, outputCursor, writeCallback, elementByteCount, elementsToWrite, payloadBytes, widths, emittedBytes, length, widthCount, total, streamRef, comparedObject, cloneContext, linkTarget: GUESS(low)
// LoadLinkID, SkipLinkIDs: GUESS(low); stream operations identified by their use in the load path
// unk01 through unk0B: GUESS(low); virtual slots outside this unit
// NiSkinInstance::Ctor: OBSERVED; placement construction entry
#pragma once

#include <cstdint>
#include "NiObject.h"

class NiSkinData : public NiObject
{
public:
    std::uint8_t unk10[0x48];
    std::uint32_t bones;
};

class NiBinaryStream
{
public:
    virtual ~NiBinaryStream();

    std::uint32_t binary_write(const void* payloadBytes, std::uint32_t length,
                               std::uint32_t* widths, std::uint32_t widthCount = 1)
    {
        const std::uint32_t emittedBytes = writeCallback(this, payloadBytes, length, widths, widthCount);
        outputCursor += emittedBytes;
        return emittedBytes;
    }

    template <class Value>
    bool write(const Value* elementsToWrite, std::uint32_t widthCount)
    {
        std::uint32_t elementByteCount = sizeof(Value);
        std::uint32_t total = widthCount * elementByteCount;
        return binary_write(elementsToWrite, total, &elementByteCount) == total;
    }

    std::uint32_t outputCursor;
    std::uint32_t unk0C;
    void* unk10;
    std::uint32_t (*writeCallback)(NiBinaryStream*, const void*, std::uint32_t, std::uint32_t*, std::uint32_t);
};

class NiStream
{
public:
    virtual ~NiStream();
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
    virtual void SaveLinkID(const NiObject* linkTarget);

    void LoadLinkID();
    void SkipLinkIDs();

    std::uint8_t streamStorage[0x298];
    NiBinaryStream* oStr;
};

struct SkinInstanceLock
{
    SkinInstanceLock() noexcept;
    std::uint64_t unknownWords[5];
};
static_assert(sizeof(SkinInstanceLock) == 0x28, "SkinInstanceLock storage size");

// NiPointer, get: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// pointee: GUESS(low)
template <class Value>
class NiPointer
{
public:
    NiPointer() noexcept : pointee(nullptr) {}
    ~NiPointer() noexcept;

    Value* get() const noexcept
    {
        return pointee;
    }

private:
    Value* pointee;
};

class NiSkinInstance : public NiObject
{
public:
    NiSkinInstance();
    ~NiSkinInstance() override;
    const NiRTTI* GetRTTI() const override;
    NiObject* CreateClone(NiCloningProcess& cloneContext) override;
    void LoadBinary(NiStream& streamRef) override;
    void LinkObject(NiStream& streamRef) override;
    bool RegisterStreamables(NiStream& streamRef) override;
    void SaveBinary(NiStream& streamRef) override;
    bool IsEqual(NiObject* comparedObject) override;
    void PostLinkObject(NiStream& streamRef) override;
    virtual void Unk_25();
    NiSkinInstance* Ctor();

    NiPointer<NiSkinData> skinData;
    NiPointer<NiObject> skinPartition;
    NiObject* rootParent;
    NiObject** bones;
    const void** boneWorldTransforms;
    std::uint32_t frameID{ UINT32_MAX };
    std::uint32_t numMatrices;
    std::uint32_t numRegisters;
    std::uint32_t allocatedSize;
    void* boneMatrices;
    void* prevBoneMatrices;
    void* skinToWorldWorldToSkinMatrix;
    SkinInstanceLock lock;
};
static_assert(sizeof(NiSkinInstance) == 0x88, "NiSkinInstance size");
