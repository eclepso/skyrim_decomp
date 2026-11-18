// NiParticleSystem functions for build sse-steam-1-7-104.
//
// Labels: v2
// Task: contrib-niparticlesystem
// Code origin: bodies written for this unit from the listings of the pinned image; names and
// declarations from CommonLibSSE-NG. No community or sibling body is adapted.
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
// Drafted by v-macrev, assisted by claude-opus-5-5, starting from
// a tools/skeleton.py skeleton.
// Compared functions:
//   RVA 0xf98f50, 127 bytes: NiParticleSystem::LoadBinary
//   RVA 0xf99260, 89 bytes: NiParticleSystem::RegisterStreamables
//   RVA 0xf992c0, 193 bytes: NiParticleSystem::SaveBinary
//   RVA 0xf99390, 192 bytes: NiParticleSystem::IsEqual
//   RVA 0xf99a30, 96 bytes: NiParticleSystem::UpdateDownwardPass
//   RVA 0xf99aa0, 109 bytes: NiParticleSystem::UpdateSelectedDownwardPass
//   RVA 0xf99ba0, 68 bytes: NiParticleSystem::SetSelectiveUpdateFlags
//   RVA 0xf9a140, 67 bytes: NiParticleSystem::~NiParticleSystem
// Adapted bodies: none
// A byte match shows that this source and recipe produce the checked code; it does not verify the
// community names or that the original source looked like this.
#include "NiParticleSystem.h"

// kSelectiveUpdate, kSelectiveUpdateTransforms, kSelectiveUpdateController, kSelectiveUpdateRigid: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); NiAVObject flag bits
static const std::uint32_t kSelectiveUpdate = 1u << 1;
static const std::uint32_t kSelectiveUpdateTransforms = 1u << 2;
static const std::uint32_t kSelectiveUpdateController = 1u << 3;
static const std::uint32_t kSelectiveUpdateRigid = 1u << 4;

// StreamRead, StreamWrite: GUESS(low); one raw read or write of a value through the stream's
// function pointer, advancing the stream position by the bytes moved.
template <class T>
static inline bool StreamRead(NiBinaryStream* a_in, T* a_value, std::uint32_t a_count)
{
    std::uint32_t size = sizeof(T);
    std::uint32_t toRead = a_count * size;
    std::uint32_t bytesRead = a_in->_readFn(a_in, a_value, toRead, &size, 1);
    a_in->_absoluteCurrentPos += bytesRead;
    return bytesRead == toRead;
}

template <class T>
static inline bool StreamWrite(NiBinaryStream* a_out, const T* a_value, std::uint32_t a_count)
{
    std::uint32_t size = sizeof(T);
    std::uint32_t toWrite = a_count * size;
    std::uint32_t bytesWritten = a_out->_writeFn(a_out, a_value, toWrite, &size, 1);
    a_out->_absoluteCurrentPos += bytesWritten;
    return bytesWritten == toWrite;
}

// TestBit, SetBit: GUESS(low); reads one flag bit by its index, or sets or clears a flag mask
static inline bool TestBit(std::uint32_t a_flags, std::uint32_t a_bit)
{
    return ((a_flags >> a_bit) & 1) != 0;
}

static inline void SetBit(std::uint32_t& a_flags, std::uint32_t a_mask, bool a_set)
{
    if (a_set) {
        a_flags |= a_mask;
    } else {
        a_flags &= ~a_mask;
    }
}

// GetModifierByName: GUESS(low); the first modifier with the given name, or none.
NiPSysModifier* NiParticleSystem::GetModifierByName(const BSFixedString& a_name)
{
    for (NiTListItem<NiPointer<NiPSysModifier>>* item = modifierList.head; item;) {
        NiPointer<NiPSysModifier>& element = item->element;
        item = item->next;
        NiPSysModifier* modifier = element.get();
        if (modifier && modifier->name == a_name) {
            return modifier;
        }
    }
    return nullptr;
}

// RVA 0xf98f50, 127 bytes.
void NiParticleSystem::LoadBinary(NiStream& a_stream)
{
    NiParticles::LoadBinary(a_stream);
    std::uint8_t worldspace;
    StreamRead(a_stream.iStr, &worldspace, 1);
    isWorldspace = worldspace != 0;
    if (worldspace) {
        world.NiTransformHelper();
    }
    a_stream.SkipLinkIDs();
}

// RVA 0xf99260, 89 bytes.
bool NiParticleSystem::RegisterStreamables(NiStream& a_stream)
{
    if (!NiParticles::RegisterStreamables(a_stream)) {
        return false;
    }
    for (NiTListItem<NiPointer<NiPSysModifier>>* item = modifierList.head; item;) {
        NiPointer<NiPSysModifier>& element = item->element;
        item = item->next;
        element.get()->RegisterStreamables(a_stream);
    }
    return true;
}

// RVA 0xf992c0, 193 bytes.
void NiParticleSystem::SaveBinary(NiStream& a_stream)
{
    NiParticles::SaveBinary(a_stream);
    std::uint8_t worldspace = isWorldspace;
    StreamWrite(a_stream.oStr, &worldspace, 1);
    std::uint32_t count = modifierList.allocator.size;
    StreamWrite(a_stream.oStr, &count, 1);
    for (NiTListItem<NiPointer<NiPSysModifier>>* item = modifierList.head; item;) {
        NiPointer<NiPSysModifier>& element = item->element;
        item = item->next;
        a_stream.SaveLinkID(element.get());
    }
}

// RVA 0xf99390, 192 bytes.
bool NiParticleSystem::IsEqual(NiObject* a_object)
{
    if (!NiParticles::IsEqual(a_object)) {
        return false;
    }
    NiParticleSystem* other = static_cast<NiParticleSystem*>(a_object);
    if (isWorldspace != other->isWorldspace) {
        return false;
    }
    if (dynamicBounds != other->dynamicBounds) {
        return false;
    }
    for (NiTListItem<NiPointer<NiPSysModifier>>* item = modifierList.head; item;) {
        NiPointer<NiPSysModifier>& element = item->element;
        item = item->next;
        NiPSysModifier* modifier = element.get();
        if (!modifier->IsEqual(other->GetModifierByName(modifier->name))) {
            return false;
        }
    }
    return true;
}

// RVA 0xf99a30, 96 bytes.
void NiParticleSystem::UpdateDownwardPass(NiUpdateData& a_data, std::uint32_t a_arg2)
{
    if (TestBit(a_data.flags, 1)) {
        a_data.flags |= 1u << 8;
        return;
    }
    UpdateSystemForPass(a_data);
    BSGeometry::UpdateDownwardPass(a_data, a_arg2);
}

// RVA 0xf99aa0, 109 bytes.
void NiParticleSystem::UpdateSelectedDownwardPass(NiUpdateData& a_data, std::uint32_t a_arg2)
{
    if (TestBit(a_data.flags, 1)) {
        a_data.flags |= 1u << 8;
        return;
    }
    if (TestBit(this->flags, 2)) {
        UpdateSystemForPass(a_data);
    }
    BSGeometry::UpdateSelectedDownwardPass(a_data, a_arg2);
}

// RVA 0xf99ba0, 68 bytes.
void NiParticleSystem::SetSelectiveUpdateFlags(bool& a_selectiveUpdate, bool a_selectiveUpdateTransforms, bool& a_rigid)
{
    a_selectiveUpdate = true;
    a_rigid = false;
    SetBit(flags, kSelectiveUpdate, a_selectiveUpdate);
    SetBit(flags, kSelectiveUpdateTransforms, true);
    SetBit(flags, kSelectiveUpdateController, true);
    SetBit(flags, kSelectiveUpdateRigid, a_rigid);
}

// Not compared: defined so that the compiler emits the vftable and, beside it, the scalar deleting
// destructor compared at RVA 0xf9a140 (67 bytes), which runs the implicit destructor.
NiParticleSystem::NiParticleSystem()
{
}
