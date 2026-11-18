// BGSReverbParameters functions for build sse-steam-1-7-104.
//
// Labels: v2
// Task: contrib-bgsreverbparameters
// Code origin: Bodies for the DoGet accessors and InitializeData written from the local listings; declarations added to the existing unit header.
// Source exposure: mixed (names and declarations from community headers; the listing of the pinned
// image).
// Evidence: findings/queue-small-2-selection.md
// Recipe: reconstruction/recipes/msvc-19.16.27054-o2.json (compile this file alone).
// Drafted by Hinkiii, assisted by claude-sonnet-5-5, starting from
// a tools/skeleton.py skeleton.
// Compared functions:
//   RVA 0x328e60, 8 bytes: BGSReverbParameters::DoGetRoomLevel
//   RVA 0x328e70, 8 bytes: BGSReverbParameters::DoGetRoomHFLevel
//   RVA 0x328ec0, 8 bytes: BGSReverbParameters::DoGetReflectionLevel
//   RVA 0x328ef0, 8 bytes: BGSReverbParameters::DoGetReverbLevel
//   RVA 0x328f20, 12 bytes: BGSReverbParameters::DoGetDiffusion
//   RVA 0x328f40, 12 bytes: BGSReverbParameters::DoGetDensity
//   RVA 0x328f60, 12 bytes: BGSReverbParameters::DoGetHFReference
//   RVA 0x328e80, 20 bytes: BGSReverbParameters::DoGetDecayTime
//   RVA 0x328ea0, 20 bytes: BGSReverbParameters::DoGetDecayHFRatio
//   RVA 0x328ed0, 20 bytes: BGSReverbParameters::DoGetReflectionDelay
//   RVA 0x328bf0, 22 bytes: BGSReverbParameters::InitializeData
// Adapted bodies: none
// A byte match shows that this source and recipe produce the checked code; it does not verify the
// community names or that the original source looked like this.
#include "BGSReverbParameters.h"
int BGSReverbParameters::DoGetRoomLevel() const { return data.roomFilter * 100; }
int BGSReverbParameters::DoGetRoomHFLevel() const { return data.roomHFFilter * 100; }
int BGSReverbParameters::DoGetReflectionLevel() const { return data.reflections * 100; }
int BGSReverbParameters::DoGetReverbLevel() const { return data.reverb * 100; }
float BGSReverbParameters::DoGetDiffusion() const { return static_cast<float>(data.diffusionPct); }
float BGSReverbParameters::DoGetDensity() const { return static_cast<float>(data.densityPct); }
float BGSReverbParameters::DoGetHFReference() const { return static_cast<float>(data.hfReference); }
float BGSReverbParameters::DoGetDecayTime() const { return static_cast<float>(data.decayTime) * kDecayTimeScale; }
float BGSReverbParameters::DoGetDecayHFRatio() const { return static_cast<float>(data.decayHFRatio) * 0.01f; }
float BGSReverbParameters::DoGetReflectionDelay() const { return static_cast<float>(data.reflectionDelay) * kReflectionDelayScale; }
void BGSReverbParameters::InitializeData()
{
    data.decayTime = 1250;
    data.hfReference = 800;
    data.roomFilter = 100;
    data.roomHFFilter = 100;
    data.reflections = 0;
    data.reverb = 0;
    data.decayHFRatio = 100;
    data.reflectionDelay = 0;
    data.reverbDelay = 0;
    data.diffusionPct = 100;
}
