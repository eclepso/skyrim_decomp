// Type declarations for the BGSAttackData translation unit (build sse-steam-1-7-104).
//
// Labels: v2
// Code origin: original reconstruction from binary analysis by Taylor Turner, assisted by claude-sonnet-5-5; class and member names come from CommonLibSSE-NG (MIT), and no external implementation body or layout is copied.
// Source exposure: binary-analysis (a local listing of the contributor's own copy of the pinned image).
// Community names are unverified. Only the members the compared code needs are declared.
// BGSAttackData, BGSAttackData::~BGSAttackData, event: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// NiRefObject, NiRefObject::~NiRefObject, _refCount, DeleteThis: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); inline because the target inlines it
// BSFixedString, BSFixedString::~BSFixedString: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); the destructor is called out of line
// value, unknown18: GUESS(low)
// ms_totalObjects: GUESS(low); NG reaches the counter through GetTotalObjectCount()
#pragma once

#include <intrin.h>
#include <cstdint>

class NiRefObject
{
public:
    // Inline because the target inlines it into the compared deleting destructor.
    virtual ~NiRefObject()
    {
        // hot path: the engine drops the shared object counter atomically on every destruction
        _InterlockedDecrement(&ms_totalObjects);
    }
    virtual void DeleteThis();  // 01

    static volatile long ms_totalObjects;

    std::uint32_t _refCount{ 0 };  // 08
    std::uint32_t _pad0C;          // 0C
};
static_assert(sizeof(NiRefObject) == 0x10, "NiRefObject size");

// Stand-in: a pooled string handle; its destructor is called out of line.
class BSFixedString {
public:
    ~BSFixedString();  // declared only; called out of line

    const char* value;  // 00
};

class BGSAttackData : public NiRefObject
{
public:
    BGSAttackData();
    // The destructor is implicit: it is the compared 0x44afe0 (scalar deleting destructor).

    BSFixedString event;           // 10
    std::uint8_t  unknown18[0x38]; // 18
};
static_assert(sizeof(BGSAttackData) == 0x50, "BGSAttackData size");
