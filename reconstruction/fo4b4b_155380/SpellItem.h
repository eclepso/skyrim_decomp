// Build: sse-steam-1-7-104; RVA 0x155380; 26 bytes; RVA 0x1553a0; 26 bytes; RVA 0x1553c0; 26 bytes
// Labels: v2
// Source exposure: mixed
// Origin: independently decoded target, anonymous sibling and public declarations.
// Drafted by gpt-6.1-terra
// Recipe: reconstruction/recipes/msvc-19.16.27054-o2.json
// Evidence: findings/ghidra-import.md
// SpellItem::IgnoreLOS, SpellItem::GetNoAbsorb, SpellItem::GetNoDualCastModifications: SIBLING(fo4-private@1b765c70, author-permission); adapted to target observations.
// Sibling source: fo4-private@1b765c70 src/Shared/Magic/SpellItem.cpp:214
// Sibling source: fo4-private@1b765c70 src/Shared/Magic/SpellItem.cpp:220
// Sibling source: fo4-private@1b765c70 src/Shared/Magic/SpellItem.cpp:226
// SpellItem, MagicItem: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e832f263dbef44e44cbe2936622a02f91a, MIT); declarations adapted from include/RE/S/SpellItem.h, include/RE/M/MagicItem.h, include/RE/T/TESBoundObject.h, include/RE/T/TESForm.h, include/RE/T/TESFullName.h and include/RE/B/BGSKeywordForm.h, include/RE/B/BGSEquipType.h, include/RE/B/BGSMenuDisplayObject.h and include/RE/T/TESDescription.h.
// names: GUESS(low); names and original signatures are tentative.
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
// SpellItem::GetDelivery, GetFixedCastDuration, IgnoresResistance, GetData2: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e832f263dbef44e44cbe2936622a02f91a, MIT); names only, the bodies are written from the target listing
// SpellItemData, unk08, data: STANDIN GUESS(low); the record at 0xC0 and only the members the compared code reads
// GetData2: virtual slot unknown, declared after the known slots
#pragma once
#include <cstdint>
class TESFile; class BGSSaveFormBuffer; class BGSLoadFormBuffer; class TESObjectREFR; class BSFixedString; struct FORM; struct FORM_GROUP; class TESBoundObject; class TESWaterForm; class NiAVObject; class BGSVoiceType; class BSString; class Actor;
using FormID = std::uint32_t; enum class FormType : unsigned char; enum class ActorValue : int;
namespace MagicSystem { enum class SpellType : int; enum class CastingType : int; enum class Delivery : int; }
class Component { public: virtual ~Component(); virtual void InitializeDataComponent(); virtual void ClearDataComponent(); virtual void CopyComponent(Component*); };
class TESForm : public Component { public:
virtual void                               InitializeData();
virtual void                               ClearData();
virtual bool                               Load(TESFile* a_mod);
virtual bool                               LoadPartial(TESFile* a_mod);
virtual bool                               LoadEdit(TESFile* a_mod);
virtual TESForm*                           CreateDuplicateForm(bool a_createEditorID, void* a_arg2);
virtual bool                               AddChange(std::uint32_t a_changeFlags);
virtual void                               RemoveChange(std::uint32_t a_changeFlags);
virtual bool                               FindInFileFast(TESFile* a_mod);
virtual bool                               CheckSaveGame(BGSSaveFormBuffer* a_buf);
virtual void                               SaveGame(BGSSaveFormBuffer* a_buf);
virtual void                               LoadGame(BGSLoadFormBuffer* a_buf);
virtual void                               InitLoadGame(BGSLoadFormBuffer* a_buf);
virtual void                               FinishLoadGame(BGSLoadFormBuffer* a_buf);
virtual void                               Revert(BGSLoadFormBuffer* a_buf);
virtual void                               InitItemImpl();
virtual TESFile*             GetDescriptionOwnerFile() const;
virtual FormType             GetSavedFormType() const;
virtual void                               GetFormDetailedString(char* a_buf, std::uint32_t a_bufLen);
virtual bool                 GetKnown() const;
virtual bool                 GetRandomAnim() const;
virtual bool                 GetPlayable() const;
virtual bool                 IsHeadingMarker() const;
virtual bool                 GetDangerous() const;
virtual bool                 QHasCurrents() const;
virtual bool                 GetObstacle() const;
virtual bool                 QIsLODLandObject() const;
virtual bool                 GetOnLocalMap() const;
virtual bool                 GetMustUpdate() const;
virtual void                               SetOnLocalMap(bool a_set);
virtual bool                 GetIgnoredBySandbox() const;
virtual void                               SetDelete(bool a_set);
virtual void                               SetAltered(bool a_set);
virtual void                               SaveObjectBound();
virtual void                               LoadObjectBound(TESFile* a_mod);
virtual bool                 IsBoundObject() const;
virtual bool                 IsObject() const;
virtual bool                 IsMagicItem() const;
virtual bool                 IsWater() const;
virtual TESObjectREFR*                     AsReference1();
virtual const TESObjectREFR* AsReference2() const;
virtual std::uint32_t        GetRefCount() const;
virtual const char*          GetTextForParsedSubTag(const BSFixedString& a_tag) const;
virtual void                               Copy(TESForm* a_srcForm);
virtual bool                               BelongsInGroup(FORM* a_form, bool a_allowParentGroups, bool a_currentOnly);
virtual void                               CreateGroupData(FORM* a_form, FORM_GROUP* a_group);
virtual const char*          GetFormEditorID() const;
virtual bool                               SetFormEditorID(const char* a_str);
virtual bool                               IsParentForm();
virtual bool                               IsParentFormTree();
virtual bool                               IsFormTypeChild(FormType a_type);
virtual bool                               Activate(TESObjectREFR* a_targetRef, TESObjectREFR* a_activatorRef, std::uint8_t a_arg3, TESBoundObject* a_object, std::int32_t a_targetCount);
virtual void                               SetFormID(FormID a_id, bool a_updateFile);
virtual const char*          GetObjectTypeName() const;
virtual bool                 QAvailableInGame() const;
};
class TESObject : public TESForm { public:
virtual void                        Unk_3B(void);
virtual bool                        IsBoundAnimObject();
virtual TESWaterForm* GetWaterType() const;
virtual bool          IsAutoCalc() const;
virtual void                        SetAutoCalc(bool a_autoCalc);
virtual NiAVObject*                 Clone3D(TESObjectREFR* a_ref, bool a_arg3);
virtual void                        UnClone3D(TESObjectREFR* a_ref);
virtual bool                        IsMarker();
virtual bool                        IsOcclusionMarker();
virtual bool                        ReplaceModel();
virtual std::uint32_t               IncRef();
virtual std::uint32_t               DecRef();
virtual NiAVObject*                 LoadGraphics(TESObjectREFR* a_ref);
};
class TESBoundObject : public TESObject { public:
virtual void                        SetObjectVoiceType(BGSVoiceType* a_voiceType);
virtual BGSVoiceType* GetObjectVoiceType() const;
virtual NiAVObject*                 Clone3D(TESObjectREFR* a_ref);
virtual bool                        ReplaceModel(const char* a_str);
virtual bool                        GetActivateText(TESObjectREFR* a_activator, BSString& a_dst);
virtual bool                        CalculateDoFavor(Actor* a_activator, bool a_arg2, TESObjectREFR* a_toActivate, float a_arg3);
virtual void                        HandleRemoveItemFromContainer(TESObjectREFR* a_container);
virtual void                        OnRemove3D(NiAVObject* a_obj3D);
virtual void                        OnCheckModels();
virtual void                        OnCopyReference();
virtual void                        OnFinishScale();
};
class MagicItem : public TESBoundObject { public: struct Data { int costOverride; unsigned flags; }; struct SkillUsageData;
virtual MagicSystem::SpellType   GetSpellType() const = 0;
virtual void                                   SetCastingType(MagicSystem::CastingType a_type);
virtual MagicSystem::CastingType GetCastingType() const = 0;
virtual void                                   SetDelivery(MagicSystem::Delivery a_delivery);
virtual MagicSystem::Delivery    GetDelivery() const = 0;
virtual bool                     IsValidDelivery(MagicSystem::Delivery a_delivery);
virtual float                    GetFixedCastDuration() const;
virtual float                    GetRange() const;
virtual bool                     IgnoresResistance() const;
virtual bool                     IgnoreLOS() const;
virtual bool                     IsFood() const;
virtual bool                     GetNoAbsorb() const;
virtual bool                     GetNoDualCastModifications() const;
virtual bool                                   GetSkillUsageData(SkillUsageData& a_data) const;
virtual bool                     IsPoison() const;
virtual bool                     IsMedicine() const;
virtual void                                   AdjustCost(float& a_cost, Actor* a_actor) const;
virtual float                    GetChargeTime() const;
virtual std::uint32_t            GetMaxEffectCount() const;
virtual ActorValue               GetAssociatedSkill() const;
virtual bool                     IsTwoHanded() const;
virtual std::uint32_t            GetChunkID() = 0;
virtual void                                   CopyMagicItemData(MagicItem* a_src) = 0;
virtual void                                   LoadMagicItemChunk(TESFile* a_mod, std::uint32_t a_chunkID);
virtual void                                   LoadChunkDataPostProcess(TESFile* a_mod);
virtual const Data*              GetData1() const = 0;
};
struct SpellItemData {
    std::int32_t costOverride;  // 00
    std::uint32_t flags;        // 04
    std::int32_t spellType;     // 08
    float chargeTime;           // 0C
    std::int32_t castingType;   // 10
    std::int32_t delivery;      // 14
    float castDuration;         // 18
};
class SpellItem : public MagicItem { public:
    bool IgnoreLOS() const override; bool GetNoAbsorb() const override; bool GetNoDualCastModifications() const override;
    MagicSystem::Delivery GetDelivery() const override;
    float GetFixedCastDuration() const override;
    bool IgnoresResistance() const override;
    virtual SpellItemData* GetData2();
    std::uint8_t unk08[0xB8];  // 08
    SpellItemData data;        // C0
};
