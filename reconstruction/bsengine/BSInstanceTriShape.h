// Type declarations for the BSInstanceTriShape translation unit (build sse-steam-1-7-104).
//
// Labels: v2
// Code origin: original reconstruction from binary analysis by Taylor Turner, assisted by claude-sonnet-5-5; class and member names come from CommonLibSSE-NG (MIT), and no external implementation body or layout is copied.
// Source exposure: binary-analysis (a local listing of the contributor's own copy of the pinned image).
// Community names are unverified. Only the members the compared code needs are declared.
// BSInstanceTriShape, BSInstanceTriShape::~BSInstanceTriShape: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// unknown08: GUESS(low)
#pragma once

#include <cstdint>

class BSInstanceTriShape {
public:
    BSInstanceTriShape();
    virtual ~BSInstanceTriShape();  // compared: 0xfe4240 (scalar deleting destructor)

    std::uint8_t unknown08[0x158];  // 08
};
static_assert(sizeof(BSInstanceTriShape) == 0x160, "BSInstanceTriShape size");
