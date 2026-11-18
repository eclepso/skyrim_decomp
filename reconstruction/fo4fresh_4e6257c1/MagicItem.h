// MagicItem, build sse-steam-1-7-104.
// Labels: v2
// Source exposure: mixed (target listing, anonymous sibling and unverified names).
// Origin: SIBLING(fo4-private@1b765c70, author-permission)
// Sibling source: fo4-private@1b765c70 src/Shared/Magic/MagicItem.cpp:50 (MagicItem::GetFixedCastDuration)
// Sibling source: fo4-private@1b765c70 src/Shared/Magic/MagicItem.cpp:56 (MagicItem::GetRange)
// Evidence: findings/ghidra-import.md
// Recipe: reconstruction/recipes/msvc-19.16.27054-o2.json
// Drafted by gpt-6.1-terra.
// MagicItem, GetFixedCastDuration, GetRange: GUESS(low)
// GetChargeTime, IsPoison, IsAutoCalc, HasEffect: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e832f263dbef44e44cbe2936622a02f91a, MIT); names only, the bodies are written from the target listing
// GetType: GUESS(low); virtual slot 0x53 (byte offset 0x298), returns the spell type compared in IsPoison
// GetData: GUESS(low); virtual slot 0x6C (byte offset 0x360), returns the record whose byte at 0x4 IsAutoCalc tests
// Unk_NN: GUESS(low); placeholders that only keep GetType and GetData at the vtable offsets the image encodes
// Effect, EffectSetting, Data and the member layout: STANDIN GUESS(low); only the offsets the compared code reads
#pragma once
#include <cstdint>

struct EffectSetting {
    std::uint8_t pad00[0xC0];  // 00
    std::int32_t unkC0;        // C0
};

struct Effect {
    std::uint8_t   pad00[0x10];  // 00
    EffectSetting* baseEffect;   // 10
};

struct EffectArray {
    Effect**      data;       // 00
    std::uint32_t capacity;   // 08
    std::uint32_t allocPad;   // 0C
    std::uint32_t size;       // 10
    std::uint32_t sizePad;    // 14
};

struct MagicItemData {
    std::uint8_t pad00[4];  // 00
    std::uint8_t unk04;     // 04
};

class MagicItem
{
public:
    virtual ~MagicItem();
    virtual void Unk_01();
    virtual void Unk_02();
    virtual void Unk_03();
    virtual void Unk_04();
    virtual void Unk_05();
    virtual void Unk_06();
    virtual void Unk_07();
    virtual void Unk_08();
    virtual void Unk_09();
    virtual void Unk_0A();
    virtual void Unk_0B();
    virtual void Unk_0C();
    virtual void Unk_0D();
    virtual void Unk_0E();
    virtual void Unk_0F();
    virtual void Unk_10();
    virtual void Unk_11();
    virtual void Unk_12();
    virtual void Unk_13();
    virtual void Unk_14();
    virtual void Unk_15();
    virtual void Unk_16();
    virtual void Unk_17();
    virtual void Unk_18();
    virtual void Unk_19();
    virtual void Unk_1A();
    virtual void Unk_1B();
    virtual void Unk_1C();
    virtual void Unk_1D();
    virtual void Unk_1E();
    virtual void Unk_1F();
    virtual void Unk_20();
    virtual void Unk_21();
    virtual void Unk_22();
    virtual void Unk_23();
    virtual void Unk_24();
    virtual void Unk_25();
    virtual void Unk_26();
    virtual void Unk_27();
    virtual void Unk_28();
    virtual void Unk_29();
    virtual void Unk_2A();
    virtual void Unk_2B();
    virtual void Unk_2C();
    virtual void Unk_2D();
    virtual void Unk_2E();
    virtual void Unk_2F();
    virtual void Unk_30();
    virtual void Unk_31();
    virtual void Unk_32();
    virtual void Unk_33();
    virtual void Unk_34();
    virtual void Unk_35();
    virtual void Unk_36();
    virtual void Unk_37();
    virtual void Unk_38();
    virtual void Unk_39();
    virtual void Unk_3A();
    virtual void Unk_3B();
    virtual void Unk_3C();
    virtual void Unk_3D();
    virtual void Unk_3E();
    virtual void Unk_3F();
    virtual void Unk_40();
    virtual void Unk_41();
    virtual void Unk_42();
    virtual void Unk_43();
    virtual void Unk_44();
    virtual void Unk_45();
    virtual void Unk_46();
    virtual void Unk_47();
    virtual void Unk_48();
    virtual void Unk_49();
    virtual void Unk_4A();
    virtual void Unk_4B();
    virtual void Unk_4C();
    virtual void Unk_4D();
    virtual void Unk_4E();
    virtual void Unk_4F();
    virtual void Unk_50();
    virtual void Unk_51();
    virtual void Unk_52();
    virtual std::int32_t GetType() const;  // 53
    virtual void Unk_54();
    virtual void Unk_55();
    virtual void Unk_56();
    virtual void Unk_57();
    virtual void Unk_58();
    virtual void Unk_59();
    virtual void Unk_5A();
    virtual void Unk_5B();
    virtual void Unk_5C();
    virtual void Unk_5D();
    virtual void Unk_5E();
    virtual void Unk_5F();
    virtual void Unk_60();
    virtual void Unk_61();
    virtual void Unk_62();
    virtual void Unk_63();
    virtual void Unk_64();
    virtual void Unk_65();
    virtual void Unk_66();
    virtual void Unk_67();
    virtual void Unk_68();
    virtual void Unk_69();
    virtual void Unk_6A();
    virtual void Unk_6B();
    virtual MagicItemData* GetData() const;  // 6C
    virtual float GetChargeTime() const;
    virtual bool IsPoison() const;
    virtual bool IsAutoCalc() const;
    virtual bool HasEffect(std::int32_t a_value) const;

    float GetFixedCastDuration() const;
    float GetRange() const;

    std::uint8_t pad08[0x50];  // 08
    EffectArray  effects;      // 58
};
