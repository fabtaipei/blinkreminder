"""
Every word this app shows, in every language it speaks.

Data only -- no logic, nothing to import, nothing that can fail. The machinery
that uses it (T, set_language, detect_language) lives in blink_reminder.py.
The split is so that adding a language, or handing one to a translator, means
touching this file and nothing else.

To add a language:

  1. Add (label, code) to LANGUAGES. The label is written in its OWN
     language: someone who cannot read the interface they are looking at
     still has to be able to find the way out of it.
  2. Add an entry to STRINGS keyed by the same code, copying the zh-Hant
     block and translating the values. Keys are the ENGLISH strings and must
     match the source character for character.
  3. If the language needs fonts the Latin stacks do not have (CJK, Thai,
     Devanagari), add them to LANGUAGE_FONTS. Cyrillic, Greek and every
     Latin-script language are already covered by Segoe UI Variable.
  4. Run test_i18n.py. It checks that every key exists, that nothing is
     orphaned, and that no string is too wide for the control it goes in.

Right-to-left languages -- Arabic, Hebrew, Persian, Urdu -- are NOT supported
and should not be added. The settings panel places every widget at a
hard-coded x from the left edge; mirroring it is a layout rewrite, not a
translation.
"""

# --------------------------------------------------------------------------
# Language
#
# One table per language, keyed by the ENGLISH string. The English text stays
# in the source as the key, which buys two things: reading a widget still
# tells you what it says, and a string nobody has translated yet falls back
# to English rather than showing the user a bare identifier like
# "settings.save". There is no gettext, no .po file and no build step -- the
# app is one file, and this is one dict.
#
# Only what a user reads is in here. Log lines are deliberately NOT
# translated: they are for whoever is debugging, and a log written in two
# languages is a log you cannot grep. DISPLAY_NAME is not translated either.
# It is the product's name, it is what the Store reserved, and a name that
# changes by locale is a name nobody can search for.
# --------------------------------------------------------------------------

# (label, code). Each label is written in its OWN language, which is the one
# convention every language picker follows: someone who cannot read the UI
# they are looking at still has to be able to find the way out of it.
LANGUAGES = [("English", "en"), ("繁體中文", "zh-Hant")]

# Families to try AHEAD of the Latin stacks, per language. Segoe UI Variable
# carries no CJK at all, and Tk's own font fallback on Windows is not
# dependable enough to gamble a whole interface on -- an unresolved glyph is a
# tofu box, drawn silently, with no error raised anywhere.
# Microsoft JhengHei UI is Windows' own Traditional Chinese interface font and
# ships with every install, Chinese or not. The rest are a ladder down from it,
# ending at two fonts drawn for other languages: YaHei sets the same characters
# in mainland typographic conventions and Yu Gothic in Japanese ones, which is
# a compromise on how the text LOOKS and never on whether it can be read at all.
LANGUAGE_FONTS = {
    "zh-Hant": ("Microsoft JhengHei UI", "Microsoft JhengHei", "PMingLiU",
                "MingLiU", "Microsoft YaHei UI", "Yu Gothic UI"),
}

# Traditional Chinese, in Taiwan's vocabulary: 螢幕 rather than 屏幕, 設定
# rather than 設置. Both readings are understood either side of the strait,
# but picking one and holding to it is what stops the panel reading as
# machine output.
STRINGS = {
    "zh-Hant": {
        # -- the tray menu -----------------------------------------------
        "Blink now": "立即眨眼",
        "Resume reminders": "恢復提醒",
        "Snooze 30 minutes": "暫停 30 分鐘",
        "Settings": "設定",
        "Buy me a coffee": "請我喝杯咖啡",
        "Quit": "結束",

        # -- how often a reminder fires, as a person would say it ---------
        # No plural forms to get wrong here, which is the one way Chinese is
        # kinder to a translator than English.
        "every second": "每秒",
        "every %d seconds": "每 %d 秒",
        "every minute": "每分鐘",
        "every %d minutes": "每 %d 分鐘",

        # -- the startup notice ------------------------------------------
        "%s is running": "%s 正在執行",
        "It stays in the background and will nudge you to blink\n%s.":
            "它會留在背景執行，%s提醒你眨眼。",
        "Right-click the tray icon, by the clock, for settings.":
            "在時鐘旁的圖示上按右鍵即可開啟設定。",
        "Got it": "知道了",

        # -- launched a second time --------------------------------------
        "%s is already running.\n\nLook for its icon in the system tray, "
        "next to the clock -- you may need to click the ^ arrow to see it. "
        "Right-click the icon for Settings.":
            "%s 已經在執行中。\n\n請在時鐘旁的系統匣裡找它的圖示"
            "— 你可能要先按 ^ 箭頭才看得到。在圖示上按右鍵即可開啟設定。",

        # -- the settings panel, and the strip along its bottom ----------
        "A gentle nudge on every screen.": "在每個螢幕上輕輕提醒你。",
        "Start with Windows": "開機時啟動",
        "Startup: managed by Windows": "啟動：由 Windows 管理",
        "Startup: turned off in Task Manager": "啟動：已在工作管理員關閉",
        "Preview blink": "預覽眨眼",
        "Preview break": "預覽休息",
        "Cancel": "取消",
        "Save": "儲存",
        "Save the changes you made?": "要儲存你剛才的變更嗎？",

        # -- the blink card ----------------------------------------------
        # "Blink" is both this card's title and the word the overlay shows
        # by default. One translation serves both, which is why they share
        # a key rather than each having one.
        "Blink": "眨眼",
        "Remind me every": "提醒間隔",
        "seconds": "秒",
        "minutes": "分",

        # -- the break card ----------------------------------------------
        "Break": "休息",
        "Look at trees!": "看看綠樹！",
        "Remind me to look away": "提醒我看向遠方",
        "min": "分",

        # -- the five rows both cards share ------------------------------
        "A dot": "圓點",
        "A word": "文字",
        "Dim screen": "螢幕變暗",
        "Strength": "強度",
        "Colour": "顏色",
        "Change...": "變更…",
        "Play a sound": "播放音效",
        # The leading spaces make room for the arrow image beside the text.
        # An ideographic space is the CJK-width equivalent of the two the
        # English label uses.
        "  Advanced settings": "　進階設定",

        # -- the two advanced windows ------------------------------------
        "Advanced settings - Blink": "進階設定 — 眨眼",
        "Blink timing and sound": "眨眼的時間與音效",
        "Blink look": "眨眼的外觀",
        "Advanced settings - Break": "進階設定 — 休息",
        "Break timing and sound": "休息的時間與音效",
        "Break look": "休息的外觀",
        "Flash style": "閃動方式",
        "Gentle": "輕柔",
        "Standard": "標準",
        "Sharp": "明顯",
        "Custom": "自訂",
        "Hold (s)": "停留（秒）",
        "Fade (s)": "淡化（秒）",
        "Pulses": "次數",
        # Not a bare 間隔: the blink card already says 提醒間隔 for how often
        # the reminder fires, and these two mean very different things.
        "Gap between pulses": "每次之間的間隔",
        "Sound": "音效",
        "Ding": "叮",
        "Chord": "和弦",
        "Chime": "鈴聲",
        "Notify": "通知",
        "Volume": "音量",
        "Test": "試聽",
        "Dot size": "圓點大小",
        "Word to show": "顯示文字",
        "Word size": "文字大小",
        "Position": "位置",
        "Centre": "中央",
        "Top left": "左上",
        "Top right": "右上",
        "Bottom left": "左下",
        "Bottom right": "右下",
        "Edge margin": "邊界距離",
        "Show on every monitor": "在每個螢幕上顯示",
        "Done": "完成",

        # -- the other word the overlay can show -------------------------
        "Look into the distance": "看向遠方",
    },
}
