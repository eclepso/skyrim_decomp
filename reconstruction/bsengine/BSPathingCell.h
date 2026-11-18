// Type declarations for the BSPathingCell translation unit (build sse-steam-1-7-104).
//
// Labels: v2
// Code origin: original reconstruction from binary analysis by Taylor Turner, assisted by claude-sonnet-5-5; class and member names come from CommonLibSSE-NG (MIT), and no external implementation body or layout is copied.
// Source exposure: binary-analysis (a local listing of the contributor's own copy of the pinned image).
// Community names are unverified. Only the members the compared code needs are declared.
// BSPathingCell, BSPathingCell::~BSPathingCell: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// unknown08: GUESS(low)
#pragma once

#include <cstdint>

class BSPathingCell {
public:
    BSPathingCell();
    virtual ~BSPathingCell() {}  // compared: 0x4e0860 (scalar deleting destructor)

    std::uint8_t unknown08[0x8];  // 08
};
static_assert(sizeof(BSPathingCell) == 0x10, "BSPathingCell size");
