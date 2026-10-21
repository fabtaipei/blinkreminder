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
# Roman-script names first, A to Z, then everything else. Sorting the whole
# list by codepoint would put Arabic, Chinese and Hindi in an order no
# reader of any of them recognises, and scatter the Latin names among them;
# this way most of the list is scannable by anyone, and the rest is grouped
# rather than interleaved. Within the second block the order is by English
# language name, which is at least deterministic -- there is no collation
# that means anything across seven different writing systems.
LANGUAGES = [
    ("Bahasa Indonesia", "id"),
    ("Čeština", "cs"),
    ("Dansk", "da"),
    ("Deutsch", "de"),
    ("English", "en"),
    ("Español", "es"),
    ("Français", "fr"),
    ("Italiano", "it"),
    ("Magyar", "hu"),
    ("Nederlands", "nl"),
    ("Norsk", "nb"),
    ("Polski", "pl"),
    ("Português", "pt"),
    ("Română", "ro"),
    ("Suomi", "fi"),
    ("Svenska", "sv"),
    ("Tiếng Việt", "vi"),
    ("Türkçe", "tr"),
    ("Ελληνικά", "el"),       # Greek
    ("Українська", "uk"),     # Ukrainian
    ("Русский", "ru"),        # Russian
    ("العربية", "ar"),        # Arabic
    ("বাংলা", "bn"),           # Bengali
    ("简体中文", "zh-Hans"),    # Chinese, Simplified
    ("繁體中文", "zh-Hant"),    # Chinese, Traditional
    ("हिन्दी", "hi"),           # Hindi
    ("日本語", "ja"),          # Japanese
    ("한국어", "ko"),           # Korean
    ("ไทย", "th"),            # Thai
    ("اردو", "ur"),           # Urdu
]

# Families to try AHEAD of the Latin stacks, per language. Segoe UI Variable
# carries no CJK at all, and Tk's own font fallback on Windows is not
# dependable enough to gamble a whole interface on -- an unresolved glyph is a
# tofu box, drawn silently, with no error raised anywhere.
# Microsoft JhengHei UI is Windows' own Traditional Chinese interface font and
# ships with every install, Chinese or not. The rest are a ladder down from it,
# ending at two fonts drawn for other languages: YaHei sets the same characters
# in mainland typographic conventions and Yu Gothic in Japanese ones, which is
# a compromise on how the text LOOKS and never on whether it can be read at all.
# Languages written right to left. Tk shapes and reverses their text
# correctly on its own, but a LABEL is a left-to-right widget, so Tk lays
# its text out with a left-to-right base paragraph direction -- and that
# misplaces any Latin run inside. Measured: "التشغيل مع Windows" renders
# with Windows at the FRONT, which is simply the wrong sentence. T() wraps
# these languages in U+202B ... U+202C to state the base direction, which
# puts it back where it belongs.
RTL_LANGUAGES = frozenset(("ar", "ur"))

LANGUAGE_FONTS = {
    "zh-Hant": ("Microsoft JhengHei UI", "Microsoft JhengHei", "PMingLiU",
                "MingLiU", "Microsoft YaHei UI", "Yu Gothic UI"),
    # YaHei is Windows' own Simplified Chinese interface font, and the ladder
    # below it runs the other way from Traditional's: JhengHei sets the same
    # characters in Taiwanese conventions, which is a compromise on how the
    # text looks and never on whether it can be read.
    "zh-Hans": ("Microsoft YaHei UI", "Microsoft YaHei", "SimSun", "NSimSun",
                "Microsoft JhengHei UI", "Yu Gothic UI"),
    "ja": ("Yu Gothic UI", "Meiryo UI", "MS UI Gothic",
           "Microsoft JhengHei UI"),
    "ko": ("Malgun Gothic", "Gulim", "Dotum", "Microsoft JhengHei UI"),
    # Nirmala UI is Windows' own face for the Indic scripts and covers both
    # Devanagari and Bengali. Tk shapes them correctly through Windows --
    # conjuncts form and vowel marks reorder, measured at 0.49 and 0.64 of
    # the width of the same characters laid out singly.
    "hi": ("Nirmala UI", "Mangal"),
    "bn": ("Nirmala UI", "Vrinda", "Shonar Bangla"),
    # Arabic and Urdu also shape and run right to left correctly. Segoe UI
    # carries Arabic; Urdu Typesetting is the nastaliq face Windows ships
    # for Urdu, but it is calligraphic and sets far too tall for a 32px row,
    # so the naskh in Segoe UI is the better fit for an interface.
    "ar": ("Segoe UI", "Tahoma", "Arial"),
    "ur": ("Segoe UI", "Tahoma", "Arial"),
    # Leelawadee UI is Windows' Thai interface font. Thai stacks vowel and
    # tone marks above and below the consonant line, so it needs a face
    # designed for it -- a Latin font that merely has the codepoints sets
    # them at the wrong heights and they collide.
    "th": ("Leelawadee UI", "Leelawadee", "Tahoma"),
    # Nothing needed for French, Spanish, German, Italian, Portuguese,
    # Polish, Turkish, Vietnamese, Indonesian or Russian: Segoe UI Variable
    # covers Latin with every diacritic those languages use, and Cyrillic
    # and Greek besides.
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

        # -- the startup notice ------------------------------------------
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

        # The ask cards, the tray's review item, and the break's countdown switch.
        "Like the app?": "喜歡這個程式嗎？",
        "If this independent app works well for you, would you consider a small donation? Thank you!": "如果這個獨立開發的程式對你有用，願意小額捐款支持嗎？謝謝！",
        "Finding it useful?": "覺得好用嗎？",
        "A short review helps others with tired eyes find it. Thank you!": "一則簡短的評論，能幫助其他眼睛疲勞的人找到它。謝謝！",
        "Don’t ask again": "不再詢問",
        "Rate this app": "為這個程式評分",
        "Show countdown": "顯示倒數計時",

        # The welcome card, the taught reminder and the strength question.
        "Show me": "示範一次",
        "Close…\nsqueeze…\nopen": "閉上……\n輕輕閉緊……\n睜開",
        "How it works": "使用說明",
        "Too weak or intrusive?": "太弱或太干擾？",
        "You can change these:": "你可以調整這些：",
        "How this app works?": "這個程式如何運作",
        "Too weak or too intrusive? Change strength, size, duration and sound in Settings.": "太弱或太干擾？可在「設定」中調整強度、大小、時長和音效。",
        "A cue appears periodically, to remind you to blink fully: close, squeeze gently, open.": "提示會定期出現，提醒你完整地眨眼：閉上、輕輕閉緊、再睜開。",
        "Size": "大小",
        "Duration": "時長",
    },

    # Simplified Chinese, in mainland vocabulary: 屏幕 rather than 螢幕,
    # 设置 rather than 設定. Not a character-by-character conversion of the
    # Traditional table -- the two differ in word choice, not only in script.
    "zh-Hans": {
        "Blink now": "立即眨眼",
        "Resume reminders": "恢复提醒",
        "Snooze 30 minutes": "暂停 30 分钟",
        "Settings": "设置",
        "Buy me a coffee": "请我喝杯咖啡",
        "Quit": "退出",

        "Got it": "知道了",

        "%s is already running.\n\nLook for its icon in the system tray, "
        "next to the clock -- you may need to click the ^ arrow to see it. "
        "Right-click the icon for Settings.":
            "%s 已经在运行。\n\n请在时钟旁的通知区域找它的图标"
            "— 你可能要先点 ^ 箭头才能看到。在图标上点右键即可打开设置。",

        "A gentle nudge on every screen.": "在每个屏幕上轻轻提醒你。",
        "Start with Windows": "开机时启动",
        "Startup: managed by Windows": "启动：由 Windows 管理",
        "Startup: turned off in Task Manager": "启动：已在任务管理器关闭",
        "Preview blink": "预览眨眼",
        "Preview break": "预览休息",
        "Cancel": "取消",
        "Save": "保存",
        "Save the changes you made?": "要保存刚才的更改吗？",

        "Blink": "眨眼",
        "Remind me every": "提醒间隔",
        "seconds": "秒",
        "minutes": "分",

        "Break": "休息",
        "Look at trees!": "看看绿树！",
        "Remind me to look away": "提醒我看向远方",
        "min": "分",

        "A dot": "圆点",
        "A word": "文字",
        "Dim screen": "屏幕变暗",
        "Strength": "强度",
        "Colour": "颜色",
        "Change...": "更改…",
        "Play a sound": "播放声音",
        "  Advanced settings": "　高级设置",

        "Advanced settings - Blink": "高级设置 — 眨眼",
        "Blink timing and sound": "眨眼的时间与声音",
        "Blink look": "眨眼的外观",
        "Advanced settings - Break": "高级设置 — 休息",
        "Break timing and sound": "休息的时间与声音",
        "Break look": "休息的外观",
        "Flash style": "闪动方式",
        "Gentle": "轻柔",
        "Standard": "标准",
        "Sharp": "明显",
        "Custom": "自定义",
        "Hold (s)": "停留（秒）",
        "Fade (s)": "淡化（秒）",
        "Pulses": "次数",
        "Gap between pulses": "每次之间的间隔",
        "Sound": "声音",
        "Ding": "叮",
        "Chord": "和弦",
        "Chime": "铃声",
        "Notify": "通知",
        "Volume": "音量",
        "Test": "试听",
        "Dot size": "圆点大小",
        "Word to show": "显示文字",
        "Word size": "文字大小",
        "Position": "位置",
        "Centre": "中间",
        "Top left": "左上",
        "Top right": "右上",
        "Bottom left": "左下",
        "Bottom right": "右下",
        "Edge margin": "边距",
        "Show on every monitor": "在每个屏幕上显示",
        "Done": "完成",

        "Look into the distance": "看向远方",

        # The ask cards, the tray's review item, and the break's countdown switch.
        "Like the app?": "喜欢这个应用吗？",
        "If this independent app works well for you, would you consider a small donation? Thank you!": "如果这个独立开发的应用对你有用，愿意小额捐款支持吗？谢谢！",
        "Finding it useful?": "觉得好用吗？",
        "A short review helps others with tired eyes find it. Thank you!": "一条简短的评价，能帮助其他眼睛疲劳的人找到它。谢谢！",
        "Don’t ask again": "不再询问",
        "Rate this app": "为这个应用评分",
        "Show countdown": "显示倒计时",

        # The welcome card, the taught reminder and the strength question.
        "Show me": "演示一下",
        "Close…\nsqueeze…\nopen": "闭上……\n轻轻闭紧……\n睁开",
        "How it works": "使用说明",
        "Too weak or intrusive?": "太弱或太打扰？",
        "You can change these:": "你可以调整这些：",
        "How this app works?": "这个程序如何运作",
        "Too weak or too intrusive? Change strength, size, duration and sound in Settings.": "太弱或太打扰？可在“设置”中调整强度、大小、时长和声音。",
        "A cue appears periodically, to remind you to blink fully: close, squeeze gently, open.": "提示会定期出现，提醒你完整地眨眼：闭上、轻轻闭紧、再睁开。",
        "Size": "大小",
        "Duration": "时长",
    },

    # French. Several strings are shorter than the obvious rendering on
    # purpose: "Démarrage : désactivé (Gestionnaire)" rather than naming the
    # Gestionnaire des tâches in full, because the control it sits in is 328
    # logical pixels wide and the full phrase is half as long again.
    "fr": {
        "Blink now": "Cligner maintenant",
        "Resume reminders": "Reprendre les rappels",
        "Snooze 30 minutes": "Pause de 30 minutes",
        "Settings": "Paramètres",
        "Buy me a coffee": "Offrez-moi un café",
        "Quit": "Quitter",

        # Not "est en cours d'exécution": with the product name in front of
        # it that is 464 pixels in a 440-pixel window.
        "Got it": "Compris",

        "%s is already running.\n\nLook for its icon in the system tray, "
        "next to the clock -- you may need to click the ^ arrow to see it. "
        "Right-click the icon for Settings.":
            "%s est déjà en cours d'exécution.\n\nCherchez son icône dans "
            "la zone de notification, près de l'horloge — vous devrez "
            "peut-être cliquer sur la flèche ^ pour la voir. Clic droit sur "
            "l'icône pour les paramètres.",

        "A gentle nudge on every screen.": "Un rappel discret sur chaque écran.",
        "Start with Windows": "Démarrer avec Windows",
        "Startup: managed by Windows": "Démarrage : géré par Windows",
        "Startup: turned off in Task Manager":
            "Démarrage : désactivé (Gestionnaire)",
        "Preview blink": "Aperçu clignement",
        "Preview break": "Aperçu pause",
        "Cancel": "Annuler",
        "Save": "Enregistrer",
        "Save the changes you made?": "Enregistrer les modifications ?",

        "Blink": "Clignement",
        "Remind me every": "Me rappeler toutes les",
        "seconds": "secondes",
        "minutes": "minutes",

        "Break": "Pause",
        "Look at trees!": "Regardez les arbres !",
        "Remind me to look away": "Me rappeler de regarder au loin",
        "min": "min",

        "A dot": "Un point",
        "A word": "Un mot",
        "Dim screen": "Assombrir",
        "Strength": "Intensité",
        "Colour": "Couleur",
        "Change...": "Modifier…",
        "Play a sound": "Jouer un son",
        "  Advanced settings": "  Paramètres avancés",

        "Advanced settings - Blink": "Paramètres avancés — Clignement",
        "Blink timing and sound": "Clignement : durée et son",
        "Blink look": "Apparence du clignement",
        "Advanced settings - Break": "Paramètres avancés — Pause",
        "Break timing and sound": "Pause : durée et son",
        "Break look": "Apparence de la pause",
        "Flash style": "Style du flash",
        "Gentle": "Doux",
        "Standard": "Standard",
        "Sharp": "Net",
        "Custom": "Perso",
        "Hold (s)": "Maintien (s)",
        "Fade (s)": "Fondu (s)",
        "Pulses": "Impulsions",
        "Gap between pulses": "Écart entre impulsions",
        "Sound": "Son",
        "Ding": "Ding",
        "Chord": "Accord",
        "Chime": "Carillon",
        "Notify": "Notif.",
        "Volume": "Volume",
        "Test": "Tester",
        "Dot size": "Taille du point",
        "Word to show": "Mot à afficher",
        "Word size": "Taille du mot",
        "Position": "Position",
        "Centre": "Centre",
        "Top left": "En haut à gauche",
        "Top right": "En haut à droite",
        "Bottom left": "En bas à gauche",
        "Bottom right": "En bas à droite",
        "Edge margin": "Marge du bord",
        "Show on every monitor": "Afficher sur chaque écran",
        "Done": "Terminé",

        "Look into the distance": "Regardez au loin",

        # The ask cards, the tray's review item, and the break's countdown switch.
        "Like the app?": "Vous aimez l'application ?",
        "If this independent app works well for you, would you consider a small donation? Thank you!": "Si cette application indépendante vous convient, envisageriez-vous un petit don ? Merci !",
        "Finding it useful?": "Vous la trouvez utile ?",
        "A short review helps others with tired eyes find it. Thank you!": "Un court avis aide d'autres personnes aux yeux fatigués à la trouver. Merci !",
        "Don’t ask again": "Ne plus demander",
        "Rate this app": "Évaluer l'application",
        "Show countdown": "Afficher le compte à rebours",

        # The welcome card, the taught reminder and the strength question.
        "Show me": "Montrez-moi",
        "Close…\nsqueeze…\nopen": "Fermez…\nserrez…\nouvrez",
        "How it works": "Mode d'emploi",
        "Too weak or intrusive?": "Trop faible ou trop gênant ?",
        "You can change these:": "Vous pouvez modifier :",
        "How this app works?": "Comment fonctionne cette appli ?",
        "Too weak or too intrusive? Change strength, size, duration and sound in Settings.": "Trop faible ou trop gênant ? Modifiez l'intensité, la taille, la durée et le son dans les Paramètres.",
        "A cue appears periodically, to remind you to blink fully: close, squeeze gently, open.": "Un signal apparaît régulièrement pour vous rappeler de cligner complètement des yeux : fermez, serrez doucement, ouvrez.",
        "Size": "Taille",
        "Duration": "Durée",
    },

    # Spanish. "Palabra" rather than "Una palabra" for the style picker:
    # three segments share 268 pixels and the article does not survive it.
    "es": {
        "Blink now": "Parpadear ahora",
        "Resume reminders": "Reanudar recordatorios",
        "Snooze 30 minutes": "Posponer 30 minutos",
        "Settings": "Configuración",
        "Buy me a coffee": "Invítame a un café",
        "Quit": "Salir",

        "Got it": "Entendido",

        "%s is already running.\n\nLook for its icon in the system tray, "
        "next to the clock -- you may need to click the ^ arrow to see it. "
        "Right-click the icon for Settings.":
            "%s ya está en ejecución.\n\nBusca su icono en el área de "
            "notificación, junto al reloj — puede que tengas que hacer clic "
            "en la flecha ^ para verlo. Clic derecho en el icono para la "
            "configuración.",

        "A gentle nudge on every screen.": "Un aviso discreto en cada pantalla.",
        "Start with Windows": "Iniciar con Windows",
        "Startup: managed by Windows": "Inicio: gestionado por Windows",
        "Startup: turned off in Task Manager":
            "Inicio: desactivado (Administrador)",
        "Preview blink": "Probar parpadeo",
        "Preview break": "Probar descanso",
        "Cancel": "Cancelar",
        "Save": "Guardar",
        "Save the changes you made?": "¿Guardar los cambios?",

        "Blink": "Parpadeo",
        "Remind me every": "Recordarme cada",
        "seconds": "segundos",
        "minutes": "minutos",

        "Break": "Descanso",
        "Look at trees!": "¡Mira los árboles!",
        "Remind me to look away": "Recordarme mirar a lo lejos",
        "min": "min",

        "A dot": "Un punto",
        "A word": "Palabra",
        "Dim screen": "Atenuar",
        "Strength": "Intensidad",
        "Colour": "Color",
        "Change...": "Cambiar…",
        "Play a sound": "Reproducir sonido",
        "  Advanced settings": "  Configuración avanzada",

        "Advanced settings - Blink": "Configuración avanzada — Parpadeo",
        "Blink timing and sound": "Parpadeo: tiempo y sonido",
        "Blink look": "Aspecto del parpadeo",
        "Advanced settings - Break": "Configuración avanzada — Descanso",
        "Break timing and sound": "Descanso: tiempo y sonido",
        "Break look": "Aspecto del descanso",
        "Flash style": "Estilo del destello",
        "Gentle": "Suave",
        "Standard": "Estándar",
        "Sharp": "Marcado",
        "Custom": "Personal",
        "Hold (s)": "Espera (s)",
        "Fade (s)": "Fundido (s)",
        "Pulses": "Pulsos",
        "Gap between pulses": "Intervalo entre pulsos",
        "Sound": "Sonido",
        "Ding": "Ding",
        "Chord": "Acorde",
        "Chime": "Campana",
        "Notify": "Aviso",
        "Volume": "Volumen",
        "Test": "Probar",
        "Dot size": "Tamaño del punto",
        "Word to show": "Palabra a mostrar",
        "Word size": "Tamaño del texto",
        "Position": "Posición",
        "Centre": "Centro",
        "Top left": "Arriba izquierda",
        "Top right": "Arriba derecha",
        "Bottom left": "Abajo izquierda",
        "Bottom right": "Abajo derecha",
        "Edge margin": "Margen del borde",
        "Show on every monitor": "Mostrar en cada pantalla",
        "Done": "Listo",

        "Look into the distance": "Mira a lo lejos",

        # The ask cards, the tray's review item, and the break's countdown switch.
        "Like the app?": "¿Te gusta la app?",
        "If this independent app works well for you, would you consider a small donation? Thank you!": "Si esta app independiente te funciona bien, ¿te plantearías hacer un pequeño donativo? ¡Gracias!",
        "Finding it useful?": "¿Te resulta útil?",
        "A short review helps others with tired eyes find it. Thank you!": "Una reseña breve ayuda a otras personas con los ojos cansados a encontrarla. ¡Gracias!",
        "Don’t ask again": "No volver a preguntar",
        "Rate this app": "Valorar esta app",
        "Show countdown": "Mostrar cuenta atrás",

        # The welcome card, the taught reminder and the strength question.
        "Show me": "Muéstramelo",
        "Close…\nsqueeze…\nopen": "Cierra…\naprieta…\nabre",
        "How it works": "Cómo funciona",
        "Too weak or intrusive?": "¿Demasiado débil o molesto?",
        "You can change these:": "Puedes cambiar esto:",
        "How this app works?": "¿Cómo funciona esta app?",
        "Too weak or too intrusive? Change strength, size, duration and sound in Settings.": "¿Demasiado débil o molesto? Cambia la intensidad, el tamaño, la duración y el sonido en Configuración.",
        "A cue appears periodically, to remind you to blink fully: close, squeeze gently, open.": "Aparece una señal periódicamente para recordarte parpadear por completo: cierra, aprieta suavemente y abre.",
        "Size": "Tamaño",
        "Duration": "Duración",
    },

    # German, the longest language measured here at about 117% of English --
    # which is why "Autostart: im Task-Manager aus" is clipped short and the
    # gap row reads "Abstand der Impulse" rather than "zwischen den".
    "de": {
        "Blink now": "Jetzt blinzeln",
        "Resume reminders": "Erinnerungen fortsetzen",
        "Snooze 30 minutes": "30 Minuten pausieren",
        "Settings": "Einstellungen",
        "Buy me a coffee": "Kaffee spendieren",
        "Quit": "Beenden",

        "Got it": "Verstanden",

        "%s is already running.\n\nLook for its icon in the system tray, "
        "next to the clock -- you may need to click the ^ arrow to see it. "
        "Right-click the icon for Settings.":
            "%s läuft bereits.\n\nSuchen Sie das Symbol im Infobereich neben "
            "der Uhr — eventuell müssen Sie zuerst auf den Pfeil ^ klicken. "
            "Ein Rechtsklick darauf öffnet die Einstellungen.",

        "A gentle nudge on every screen.":
            "Ein sanfter Hinweis auf jedem Bildschirm.",
        "Start with Windows": "Mit Windows starten",
        "Startup: managed by Windows": "Autostart: von Windows verwaltet",
        "Startup: turned off in Task Manager": "Autostart: im Task-Manager aus",
        "Preview blink": "Blinzeln testen",
        "Preview break": "Pause testen",
        "Cancel": "Abbrechen",
        "Save": "Speichern",
        "Save the changes you made?": "Änderungen speichern?",

        "Blink": "Blinzeln",
        "Remind me every": "Erinnern alle",
        "seconds": "Sekunden",
        "minutes": "Minuten",

        "Break": "Pause",
        "Look at trees!": "Schau auf Bäume!",
        "Remind me to look away": "An Wegschauen erinnern",
        "min": "Min",

        "A dot": "Punkt",
        "A word": "Wort",
        "Dim screen": "Abdunkeln",
        "Strength": "Stärke",
        "Colour": "Farbe",
        "Change...": "Ändern…",
        "Play a sound": "Ton abspielen",
        "  Advanced settings": "  Erweiterte Einstellungen",

        "Advanced settings - Blink": "Erweiterte Einstellungen — Blinzeln",
        "Blink timing and sound": "Blinzeln: Timing und Ton",
        "Blink look": "Aussehen des Blinzelns",
        "Advanced settings - Break": "Erweiterte Einstellungen — Pause",
        "Break timing and sound": "Pause: Timing und Ton",
        "Break look": "Aussehen der Pause",
        "Flash style": "Blitzstil",
        "Gentle": "Sanft",
        "Standard": "Standard",
        "Sharp": "Deutlich",
        "Custom": "Eigene",
        "Hold (s)": "Halten (s)",
        "Fade (s)": "Blende (s)",
        "Pulses": "Impulse",
        "Gap between pulses": "Abstand der Impulse",
        "Sound": "Ton",
        "Ding": "Ding",
        "Chord": "Akkord",
        "Chime": "Glocke",
        "Notify": "Hinweis",
        "Volume": "Lautstärke",
        "Test": "Test",
        "Dot size": "Punktgröße",
        "Word to show": "Wort anzeigen",
        "Word size": "Schriftgröße",
        "Position": "Position",
        "Centre": "Mitte",
        "Top left": "Oben links",
        "Top right": "Oben rechts",
        "Bottom left": "Unten links",
        "Bottom right": "Unten rechts",
        "Edge margin": "Randabstand",
        "Show on every monitor": "Auf allen Bildschirmen",
        "Done": "Fertig",

        "Look into the distance": "In die Ferne schauen",

        # The ask cards, the tray's review item, and the break's countdown switch.
        "Like the app?": "Gefällt Ihnen die App?",
        "If this independent app works well for you, would you consider a small donation? Thank you!": "Wenn diese unabhängige App gut für Sie funktioniert, würden Sie eine kleine Spende in Betracht ziehen? Danke!",
        "Finding it useful?": "Finden Sie die App nützlich?",
        "A short review helps others with tired eyes find it. Thank you!": "Eine kurze Bewertung hilft anderen mit müden Augen, sie zu finden. Danke!",
        "Don’t ask again": "Nicht mehr fragen",
        "Rate this app": "App bewerten",
        "Show countdown": "Countdown anzeigen",

        # The welcome card, the taught reminder and the strength question.
        "Show me": "Zeigen",
        "Close…\nsqueeze…\nopen": "Schließen…\nkneifen…\nöffnen",
        "How it works": "So funktioniert es",
        "Too weak or intrusive?": "Zu schwach oder zu störend?",
        "You can change these:": "Sie können Folgendes ändern:",
        "How this app works?": "So funktioniert die App",
        "Too weak or too intrusive? Change strength, size, duration and sound in Settings.": "Zu schwach oder zu störend? Stärke, Größe, Dauer und Ton unter Einstellungen ändern.",
        "A cue appears periodically, to remind you to blink fully: close, squeeze gently, open.": "Ein Hinweis erscheint regelmäßig und erinnert Sie daran, vollständig zu blinzeln: schließen, sanft zusammenkneifen, öffnen.",
        "Size": "Größe",
        "Duration": "Dauer",
    },

    # Italian. The blink card is "Palpebre" rather than "Battito", which on
    # its own reads as a heartbeat; and the style picker says "Oscura", since
    # "Schermo scuro" is half again wider than its 79-pixel segment.
    "it": {
        "Blink now": "Batti le palpebre",
        "Resume reminders": "Riprendi i promemoria",
        "Snooze 30 minutes": "Posticipa di 30 minuti",
        "Settings": "Impostazioni",
        "Buy me a coffee": "Offrimi un caffè",
        "Quit": "Esci",

        "Got it": "Ho capito",

        "%s is already running.\n\nLook for its icon in the system tray, "
        "next to the clock -- you may need to click the ^ arrow to see it. "
        "Right-click the icon for Settings.":
            "%s è già in esecuzione.\n\nCerca la sua icona nell'area di "
            "notifica, vicino all'orologio — potrebbe servire un clic sulla "
            "freccia ^ per vederla. Clic destro sull'icona per le "
            "impostazioni.",

        "A gentle nudge on every screen.":
            "Un promemoria discreto su ogni schermo.",
        "Start with Windows": "Avvia con Windows",
        "Startup: managed by Windows": "Avvio: gestito da Windows",
        "Startup: turned off in Task Manager": "Avvio: disattivato (Gestione)",
        "Preview blink": "Prova palpebre",
        "Preview break": "Prova pausa",
        "Cancel": "Annulla",
        "Save": "Salva",
        "Save the changes you made?": "Salvare le modifiche?",

        "Blink": "Palpebre",
        "Remind me every": "Ricordamelo ogni",
        "seconds": "secondi",
        "minutes": "minuti",

        "Break": "Pausa",
        "Look at trees!": "Guarda gli alberi!",
        "Remind me to look away": "Ricordami di guardare lontano",
        "min": "min",

        "A dot": "Un punto",
        "A word": "Parola",
        "Dim screen": "Oscura",
        "Strength": "Intensità",
        "Colour": "Colore",
        "Change...": "Cambia…",
        "Play a sound": "Riproduci un suono",
        "  Advanced settings": "  Impostazioni avanzate",

        "Advanced settings - Blink": "Impostazioni avanzate — Palpebre",
        "Blink timing and sound": "Palpebre: tempi e suono",
        "Blink look": "Aspetto delle palpebre",
        "Advanced settings - Break": "Impostazioni avanzate — Pausa",
        "Break timing and sound": "Pausa: tempi e suono",
        "Break look": "Aspetto della pausa",
        "Flash style": "Stile del lampo",
        "Gentle": "Delicato",
        "Standard": "Standard",
        "Sharp": "Netto",
        "Custom": "Person.",
        "Hold (s)": "Durata (s)",
        "Fade (s)": "Sfuma (s)",
        "Pulses": "Impulsi",
        "Gap between pulses": "Intervallo tra impulsi",
        "Sound": "Suono",
        "Ding": "Ding",
        "Chord": "Accordo",
        "Chime": "Campana",
        "Notify": "Avviso",
        "Volume": "Volume",
        "Test": "Prova",
        "Dot size": "Dimensione punto",
        "Word to show": "Parola da mostrare",
        "Word size": "Dimensione testo",
        "Position": "Posizione",
        "Centre": "Centro",
        "Top left": "In alto a sinistra",
        "Top right": "In alto a destra",
        "Bottom left": "In basso a sinistra",
        "Bottom right": "In basso a destra",
        "Edge margin": "Margine dal bordo",
        "Show on every monitor": "Mostra su ogni schermo",
        "Done": "Fatto",

        "Look into the distance": "Guarda lontano",

        # The ask cards, the tray's review item, and the break's countdown switch.
        "Like the app?": "Ti piace l'app?",
        "If this independent app works well for you, would you consider a small donation? Thank you!": "Se questa app indipendente funziona bene per te, prenderesti in considerazione una piccola donazione? Grazie!",
        "Finding it useful?": "Ti è utile?",
        "A short review helps others with tired eyes find it. Thank you!": "Una breve recensione aiuta altre persone con gli occhi stanchi a trovarla. Grazie!",
        "Don’t ask again": "Non chiedere più",
        "Rate this app": "Valuta l'app",
        "Show countdown": "Mostra il conto alla rovescia",

        # The welcome card, the taught reminder and the strength question.
        "Show me": "Mostrami",
        "Close…\nsqueeze…\nopen": "Chiudi…\nstringi…\napri",
        "How it works": "Come funziona",
        "Too weak or intrusive?": "Troppo debole o invadente?",
        "You can change these:": "Puoi modificare:",
        "How this app works?": "Come funziona questa app",
        "Too weak or too intrusive? Change strength, size, duration and sound in Settings.": "Troppo debole o invadente? Cambia intensità, dimensione, durata e suono nelle Impostazioni.",
        "A cue appears periodically, to remind you to blink fully: close, squeeze gently, open.": "Un segnale appare periodicamente per ricordarti di sbattere le palpebre fino in fondo: chiudi, stringi delicatamente, apri.",
        "Size": "Dimensione",
        "Duration": "Durata",
    },

    # Portuguese, written for Brazil, which is where almost all the Store's
    # Portuguese-speaking customers are. "Tela" rather than "ecrã", "você"
    # rather than "tu".
    "pt": {
        "Blink now": "Piscar agora",
        "Resume reminders": "Retomar lembretes",
        "Snooze 30 minutes": "Adiar por 30 minutos",
        "Settings": "Configurações",
        "Buy me a coffee": "Me pague um café",
        "Quit": "Sair",

        "Got it": "Entendi",

        "%s is already running.\n\nLook for its icon in the system tray, "
        "next to the clock -- you may need to click the ^ arrow to see it. "
        "Right-click the icon for Settings.":
            "%s já está em execução.\n\nProcure o ícone na área de "
            "notificação, ao lado do relógio — talvez seja preciso clicar na "
            "seta ^ para vê-lo. Clique com o botão direito para abrir as "
            "configurações.",

        "A gentle nudge on every screen.": "Um lembrete discreto em cada tela.",
        "Start with Windows": "Iniciar com o Windows",
        "Startup: managed by Windows": "Inicialização: pelo Windows",
        "Startup: turned off in Task Manager":
            "Inicialização: desativada (Gerenciador)",
        "Preview blink": "Testar piscada",
        "Preview break": "Testar pausa",
        "Cancel": "Cancelar",
        "Save": "Salvar",
        "Save the changes you made?": "Salvar as alterações?",

        "Blink": "Piscada",
        "Remind me every": "Lembrar a cada",
        "seconds": "segundos",
        "minutes": "minutos",

        "Break": "Pausa",
        "Look at trees!": "Olhe as árvores!",
        "Remind me to look away": "Lembrar de olhar para longe",
        "min": "min",

        "A dot": "Um ponto",
        "A word": "Palavra",
        "Dim screen": "Escurecer",
        # "Intensidade" is 77px and the label has 74 before the slider.
        "Strength": "Força",
        "Colour": "Cor",
        "Change...": "Alterar…",
        "Play a sound": "Tocar um som",
        "  Advanced settings": "  Configurações avançadas",

        "Advanced settings - Blink": "Configurações avançadas — Piscada",
        "Blink timing and sound": "Piscada: tempo e som",
        "Blink look": "Aparência da piscada",
        "Advanced settings - Break": "Configurações avançadas — Pausa",
        "Break timing and sound": "Pausa: tempo e som",
        "Break look": "Aparência da pausa",
        "Flash style": "Estilo do brilho",
        "Gentle": "Suave",
        "Standard": "Padrão",
        "Sharp": "Marcado",
        "Custom": "Person.",
        "Hold (s)": "Duração (s)",
        "Fade (s)": "Fusão (s)",
        "Pulses": "Pulsos",
        "Gap between pulses": "Intervalo entre pulsos",
        "Sound": "Som",
        "Ding": "Ding",
        "Chord": "Acorde",
        "Chime": "Sino",
        "Notify": "Aviso",
        "Volume": "Volume",
        "Test": "Testar",
        "Dot size": "Tamanho do ponto",
        "Word to show": "Palavra a exibir",
        "Word size": "Tamanho do texto",
        "Position": "Posição",
        "Centre": "Centro",
        "Top left": "Acima à esquerda",
        "Top right": "Acima à direita",
        "Bottom left": "Abaixo à esquerda",
        "Bottom right": "Abaixo à direita",
        "Edge margin": "Margem da borda",
        "Show on every monitor": "Mostrar em todas as telas",
        "Done": "Concluir",

        "Look into the distance": "Olhe para longe",

        # The ask cards, the tray's review item, and the break's countdown switch.
        "Like the app?": "Gostou do app?",
        "If this independent app works well for you, would you consider a small donation? Thank you!": "Se este app independente funciona bem para você, que tal fazer uma pequena doação? Agradeço!",
        "Finding it useful?": "Está sendo útil?",
        "A short review helps others with tired eyes find it. Thank you!": "Uma avaliação curta ajuda outras pessoas com olhos cansados a encontrá-lo. Agradeço!",
        "Don’t ask again": "Não perguntar de novo",
        "Rate this app": "Avaliar este app",
        "Show countdown": "Mostrar contagem regressiva",

        # The welcome card, the taught reminder and the strength question.
        "Show me": "Mostrar",
        "Close…\nsqueeze…\nopen": "Feche…\naperte…\nabra",
        "How it works": "Como funciona",
        "Too weak or intrusive?": "Fraco demais ou incômodo?",
        "You can change these:": "Você pode mudar:",
        "How this app works?": "Como este app funciona",
        "Too weak or too intrusive? Change strength, size, duration and sound in Settings.": "Fraco demais ou incômodo? Mude a força, o tamanho, a duração e o som nas Configurações.",
        "A cue appears periodically, to remind you to blink fully: close, squeeze gently, open.": "Um sinal aparece periodicamente para lembrar você de piscar por completo: feche, aperte de leve e abra.",
        "Size": "Tamanho",
        "Duration": "Duração",
    },

    # Japanese. Interface Japanese is terse -- ですます endings are dropped
    # from labels and kept only in the two full sentences the notice shows.
    "ja": {
        "Blink now": "今すぐまばたき",
        "Resume reminders": "通知を再開",
        "Snooze 30 minutes": "30 分停止",
        "Settings": "設定",
        "Buy me a coffee": "コーヒーをおごる",
        "Quit": "終了",

        "Got it": "閉じる",

        "%s is already running.\n\nLook for its icon in the system tray, "
        "next to the clock -- you may need to click the ^ arrow to see it. "
        "Right-click the icon for Settings.":
            "%s はすでに実行中です。\n\n時計の横の通知領域にアイコンがあります"
            "— ^ をクリックしないと見えないことがあります。"
            "アイコンを右クリックすると設定が開きます。",

        "A gentle nudge on every screen.": "すべての画面にそっとお知らせします。",
        "Start with Windows": "Windows 起動時に開始",
        "Startup: managed by Windows": "起動：Windows が管理",
        "Startup: turned off in Task Manager": "起動：タスクマネージャーで無効",
        "Preview blink": "まばたきを試す",
        "Preview break": "休憩を試す",
        "Cancel": "キャンセル",
        "Save": "保存",
        "Save the changes you made?": "変更を保存しますか？",

        "Blink": "まばたき",
        "Remind me every": "通知の間隔",
        "seconds": "秒",
        "minutes": "分",

        "Break": "休憩",
        "Look at trees!": "緑を見よう！",
        "Remind me to look away": "遠くを見るよう通知",
        "min": "分",

        "A dot": "点",
        "A word": "文字",
        "Dim screen": "画面を暗く",
        "Strength": "強さ",
        "Colour": "色",
        "Change...": "変更…",
        "Play a sound": "音を鳴らす",
        "  Advanced settings": "　詳細設定",

        "Advanced settings - Blink": "詳細設定 — まばたき",
        "Blink timing and sound": "まばたきの時間と音",
        "Blink look": "まばたきの見た目",
        "Advanced settings - Break": "詳細設定 — 休憩",
        "Break timing and sound": "休憩の時間と音",
        "Break look": "休憩の見た目",
        "Flash style": "光り方",
        "Gentle": "やさしく",
        "Standard": "標準",
        "Sharp": "はっきり",
        "Custom": "カスタム",
        "Hold (s)": "表示（秒）",
        "Fade (s)": "フェード（秒）",
        "Pulses": "回数",
        "Gap between pulses": "各回の間隔",
        "Sound": "音",
        "Ding": "ディン",
        "Chord": "和音",
        "Chime": "チャイム",
        "Notify": "通知",
        "Volume": "音量",
        "Test": "試聴",
        "Dot size": "点の大きさ",
        "Word to show": "表示する文字",
        "Word size": "文字の大きさ",
        "Position": "位置",
        "Centre": "中央",
        "Top left": "左上",
        "Top right": "右上",
        "Bottom left": "左下",
        "Bottom right": "右下",
        "Edge margin": "端からの余白",
        "Show on every monitor": "すべての画面に表示",
        "Done": "完了",

        "Look into the distance": "遠くを見る",

        # The ask cards, the tray's review item, and the break's countdown switch.
        "Like the app?": "気に入っていただけましたか？",
        "If this independent app works well for you, would you consider a small donation? Thank you!": "この個人開発アプリがお役に立っているなら、少額のご支援をご検討いただけませんか？ありがとうございます！",
        "Finding it useful?": "役に立っていますか？",
        "A short review helps others with tired eyes find it. Thank you!": "短いレビューが、目の疲れに悩むほかの方がこのアプリを見つける助けになります。ありがとうございます！",
        "Don’t ask again": "今後は表示しない",
        "Rate this app": "このアプリを評価",
        "Show countdown": "カウントダウンを表示",

        # The welcome card, the taught reminder and the strength question.
        "Show me": "見てみる",
        "Close…\nsqueeze…\nopen": "閉じて…\nぎゅっと…\n開く",
        "How it works": "使い方",
        "Too weak or intrusive?": "弱すぎる、または邪魔ですか？",
        "You can change these:": "次の項目を変更できます：",
        "How this app works?": "このアプリの使い方",
        "Too weak or too intrusive? Change strength, size, duration and sound in Settings.": "弱すぎる、または邪魔なときは、設定で強さ・大きさ・表示時間・音を変更できます。",
        "A cue appears periodically, to remind you to blink fully: close, squeeze gently, open.": "合図が定期的に表示され、しっかりまばたきするよう促します：目を閉じ、軽くぎゅっとつむって、開く。",
        "Size": "大きさ",
        "Duration": "表示時間",
    },

    # Korean. Spacing follows 한글 맞춤법: "눈 깜박임" is two words, and the
    # interface style drops 하십시오체 endings from labels.
    "ko": {
        "Blink now": "지금 깜박이기",
        "Resume reminders": "알림 다시 시작",
        "Snooze 30 minutes": "30분 미루기",
        "Settings": "설정",
        "Buy me a coffee": "커피 한 잔 사주기",
        "Quit": "종료",

        "Got it": "확인",

        "%s is already running.\n\nLook for its icon in the system tray, "
        "next to the clock -- you may need to click the ^ arrow to see it. "
        "Right-click the icon for Settings.":
            "%s이(가) 이미 실행 중입니다.\n\n시계 옆 알림 영역에서 아이콘을 "
            "찾아보세요 — ^ 화살표를 눌러야 보일 수도 있습니다. 아이콘을 "
            "오른쪽 버튼으로 누르면 설정이 열립니다.",

        "A gentle nudge on every screen.": "모든 화면에 조용히 알려 줍니다.",
        "Start with Windows": "Windows 시작 시 실행",
        "Startup: managed by Windows": "시작: Windows가 관리",
        "Startup: turned off in Task Manager": "시작: 작업 관리자에서 해제됨",
        "Preview blink": "깜박임 미리보기",
        "Preview break": "휴식 미리보기",
        "Cancel": "취소",
        "Save": "저장",
        "Save the changes you made?": "변경 내용을 저장할까요?",

        "Blink": "눈 깜박임",
        "Remind me every": "알림 간격",
        "seconds": "초",
        "minutes": "분",

        "Break": "휴식",
        "Look at trees!": "나무를 보세요!",
        "Remind me to look away": "먼 곳 보기 알림",
        "min": "분",

        "A dot": "점",
        "A word": "글자",
        "Dim screen": "어둡게",
        "Strength": "세기",
        "Colour": "색",
        "Change...": "변경…",
        "Play a sound": "소리 재생",
        "  Advanced settings": "　고급 설정",

        "Advanced settings - Blink": "고급 설정 — 눈 깜박임",
        "Blink timing and sound": "깜박임 시간과 소리",
        "Blink look": "깜박임 모양",
        "Advanced settings - Break": "고급 설정 — 휴식",
        "Break timing and sound": "휴식 시간과 소리",
        "Break look": "휴식 모양",
        "Flash style": "번쩍임 방식",
        "Gentle": "부드럽게",
        "Standard": "표준",
        "Sharp": "뚜렷하게",
        "Custom": "사용자",
        "Hold (s)": "유지(초)",
        "Fade (s)": "페이드(초)",
        "Pulses": "횟수",
        "Gap between pulses": "각 회 사이 간격",
        "Sound": "소리",
        "Ding": "딩",
        "Chord": "화음",
        "Chime": "차임",
        "Notify": "알림",
        "Volume": "음량",
        "Test": "듣기",
        "Dot size": "점 크기",
        "Word to show": "표시할 글자",
        "Word size": "글자 크기",
        "Position": "위치",
        "Centre": "가운데",
        "Top left": "왼쪽 위",
        "Top right": "오른쪽 위",
        "Bottom left": "왼쪽 아래",
        "Bottom right": "오른쪽 아래",
        "Edge margin": "가장자리 여백",
        "Show on every monitor": "모든 화면에 표시",
        "Done": "완료",

        "Look into the distance": "먼 곳을 보세요",

        # The ask cards, the tray's review item, and the break's countdown switch.
        "Like the app?": "앱이 마음에 드세요?",
        "If this independent app works well for you, would you consider a small donation? Thank you!": "개인이 만든 이 앱이 잘 맞으신다면 작은 후원을 고려해 주시겠어요? 감사합니다!",
        "Finding it useful?": "유용하게 쓰고 계세요?",
        "A short review helps others with tired eyes find it. Thank you!": "짧은 리뷰 하나가 눈이 피로한 다른 사람들이 이 앱을 찾는 데 도움이 돼요. 감사합니다!",
        "Don’t ask again": "다시 묻지 않기",
        "Rate this app": "이 앱 평가하기",
        "Show countdown": "카운트다운 표시",

        # The welcome card, the taught reminder and the strength question.
        "Show me": "보여 주기",
        "Close…\nsqueeze…\nopen": "감고…\n꼭 감았다가…\n뜨세요",
        "How it works": "사용 방법",
        "Too weak or intrusive?": "너무 약하거나 방해되나요?",
        "You can change these:": "다음을 바꿀 수 있습니다:",
        "How this app works?": "이 앱의 작동 방식",
        "Too weak or too intrusive? Change strength, size, duration and sound in Settings.": "너무 약하거나 방해되나요? 설정에서 세기, 크기, 지속 시간, 소리를 바꾸세요.",
        "A cue appears periodically, to remind you to blink fully: close, squeeze gently, open.": "신호가 주기적으로 나타나 눈을 완전히 깜빡이도록 알려 줍니다: 감고, 살짝 꼭 감았다가, 뜨세요.",
        "Size": "크기",
        "Duration": "지속 시간",
    },

    # Hindi. Devanagari, shaped correctly by Windows through Tk.
    "hi": {
        "Blink now": "अभी पलक झपकाएँ",
        "Resume reminders": "याद दिलाना फिर शुरू",
        "Snooze 30 minutes": "30 मिनट रोकें",
        "Settings": "सेटिंग्स",
        "Buy me a coffee": "मुझे कॉफ़ी पिलाएँ",
        "Quit": "बंद करें",

        "Got it": "ठीक है",

        "%s is already running.\n\nLook for its icon in the system tray, "
        "next to the clock -- you may need to click the ^ arrow to see it. "
        "Right-click the icon for Settings.":
            "%s पहले से चल रहा है।\n\nघड़ी के पास सूचना क्षेत्र में इसका आइकन "
            "देखें — दिखने के लिए ^ तीर पर क्लिक करना पड़ सकता है। सेटिंग्स के "
            "लिए आइकन पर राइट-क्लिक करें।",

        "A gentle nudge on every screen.": "हर स्क्रीन पर एक हल्का संकेत।",
        "Start with Windows": "Windows के साथ शुरू",
        "Startup: managed by Windows": "शुरुआत: Windows द्वारा",
        "Startup: turned off in Task Manager": "शुरुआत: टास्क मैनेजर में बंद",
        "Preview blink": "पलक देखें",
        "Preview break": "विराम देखें",
        "Cancel": "रद्द करें",
        "Save": "सहेजें",
        "Save the changes you made?": "बदलाव सहेजें?",

        "Blink": "पलक",
        "Remind me every": "याद दिलाएँ हर",
        "seconds": "सेकंड",
        "minutes": "मिनट",

        "Break": "विराम",
        "Look at trees!": "पेड़ों को देखें!",
        "Remind me to look away": "दूर देखने की याद दिलाएँ",
        "min": "मि",

        "A dot": "बिंदु",
        "A word": "शब्द",
        "Dim screen": "मंद करें",
        "Strength": "तीव्रता",
        "Colour": "रंग",
        "Change...": "बदलें…",
        "Play a sound": "ध्वनि बजाएँ",
        "  Advanced settings": "  उन्नत सेटिंग्स",

        "Advanced settings - Blink": "उन्नत सेटिंग्स — पलक",
        "Blink timing and sound": "पलक: समय और ध्वनि",
        "Blink look": "पलक का रूप",
        "Advanced settings - Break": "उन्नत सेटिंग्स — विराम",
        "Break timing and sound": "विराम: समय और ध्वनि",
        "Break look": "विराम का रूप",
        "Flash style": "चमक का ढंग",
        "Gentle": "हल्का",
        "Standard": "सामान्य",
        "Sharp": "तेज़",
        "Custom": "अपना",
        "Hold (s)": "ठहराव (से)",
        "Fade (s)": "फ़ेड (से)",
        "Pulses": "बार",
        "Gap between pulses": "हर बार के बीच अंतर",
        "Sound": "ध्वनि",
        "Ding": "डिंग",
        "Chord": "स्वर",
        "Chime": "घंटी",
        "Notify": "सूचना",
        "Volume": "आवाज़",
        "Test": "सुनें",
        "Dot size": "बिंदु का आकार",
        "Word to show": "दिखाने का शब्द",
        "Word size": "शब्द का आकार",
        "Position": "स्थान",
        "Centre": "बीच में",
        "Top left": "ऊपर बाएँ",
        "Top right": "ऊपर दाएँ",
        "Bottom left": "नीचे बाएँ",
        "Bottom right": "नीचे दाएँ",
        "Edge margin": "किनारे से दूरी",
        "Show on every monitor": "हर स्क्रीन पर दिखाएँ",
        "Done": "हो गया",

        "Look into the distance": "दूर देखें",

        # The ask cards, the tray's review item, and the break's countdown switch.
        "Like the app?": "ऐप पसंद आया?",
        "If this independent app works well for you, would you consider a small donation? Thank you!": "अगर यह स्वतंत्र ऐप आपके लिए अच्छा काम करता है, तो क्या आप एक छोटा-सा दान देने पर विचार करेंगे? धन्यवाद!",
        "Finding it useful?": "क्या यह उपयोगी लग रहा है?",
        "A short review helps others with tired eyes find it. Thank you!": "एक छोटी-सी समीक्षा थकी आँखों वाले दूसरे लोगों को इसे ढूँढने में मदद करती है। धन्यवाद!",
        "Don’t ask again": "फिर से न पूछें",
        "Rate this app": "इस ऐप को रेट करें",
        "Show countdown": "उलटी गिनती दिखाएँ",

        # The welcome card, the taught reminder and the strength question.
        "Show me": "दिखाएँ",
        "Close…\nsqueeze…\nopen": "बंद करें…\nभींचें…\nखोलें",
        "How it works": "यह कैसे काम करता है",
        "Too weak or intrusive?": "बहुत कमज़ोर या खलल डालने वाला?",
        "You can change these:": "आप इन्हें बदल सकते हैं:",
        "How this app works?": "यह ऐप कैसे काम करता है",
        "Too weak or too intrusive? Change strength, size, duration and sound in Settings.": "बहुत कमज़ोर या खलल डालने वाला? सेटिंग्स में तीव्रता, आकार, अवधि और ध्वनि बदलें।",
        "A cue appears periodically, to remind you to blink fully: close, squeeze gently, open.": "एक संकेत समय-समय पर दिखता है, ताकि आपको पूरी तरह पलकें झपकाना याद रहे: आँखें बंद करें, हल्के से भींचें, खोलें।",
        "Size": "आकार",
        "Duration": "अवधि",
    },

    # Bengali. Nirmala UI covers it, and the conjuncts form correctly.
    "bn": {
        "Blink now": "এখনই চোখ পিটপিট",
        "Resume reminders": "মনে করানো চালু",
        "Snooze 30 minutes": "৩০ মিনিট থামান",
        "Settings": "সেটিংস",
        "Buy me a coffee": "আমাকে কফি খাওয়ান",
        "Quit": "বন্ধ করুন",

        "Got it": "বুঝেছি",

        "%s is already running.\n\nLook for its icon in the system tray, "
        "next to the clock -- you may need to click the ^ arrow to see it. "
        "Right-click the icon for Settings.":
            "%s ইতিমধ্যে চলছে।\n\nঘড়ির পাশে বিজ্ঞপ্তি এলাকায় এর আইকন "
            "খুঁজুন — দেখতে ^ তিরে ক্লিক করতে হতে পারে। সেটিংসের জন্য আইকনে "
            "ডান-ক্লিক করুন।",

        "A gentle nudge on every screen.": "প্রতিটি পর্দায় নরম একটি ইঙ্গিত।",
        "Start with Windows": "Windows চালু হলে শুরু",
        "Startup: managed by Windows": "শুরু: Windows পরিচালিত",
        "Startup: turned off in Task Manager": "শুরু: টাস্ক ম্যানেজারে বন্ধ",
        "Preview blink": "পলক দেখুন",
        "Preview break": "বিরতি দেখুন",
        "Cancel": "বাতিল",
        "Save": "সংরক্ষণ",
        "Save the changes you made?": "পরিবর্তন সংরক্ষণ করবেন?",

        "Blink": "পলক",
        "Remind me every": "মনে করান প্রতি",
        "seconds": "সেকেন্ড",
        "minutes": "মিনিট",

        "Break": "বিরতি",
        "Look at trees!": "গাছের দিকে তাকান!",
        "Remind me to look away": "দূরে তাকাতে মনে করান",
        "min": "মি",

        "A dot": "বিন্দু",
        "A word": "শব্দ",
        "Dim screen": "আবছা",
        "Strength": "তীব্রতা",
        "Colour": "রঙ",
        "Change...": "বদলান…",
        "Play a sound": "শব্দ বাজান",
        "  Advanced settings": "  উন্নত সেটিংস",

        "Advanced settings - Blink": "উন্নত সেটিংস — পলক",
        "Blink timing and sound": "পলক: সময় ও শব্দ",
        "Blink look": "পলকের চেহারা",
        "Advanced settings - Break": "উন্নত সেটিংস — বিরতি",
        "Break timing and sound": "বিরতি: সময় ও শব্দ",
        "Break look": "বিরতির চেহারা",
        "Flash style": "ঝলকের ধরন",
        "Gentle": "নরম",
        "Standard": "সাধারণ",
        "Sharp": "স্পষ্ট",
        "Custom": "নিজের",
        "Hold (s)": "স্থায়ী (সে)",
        "Fade (s)": "ফেড (সে)",
        "Pulses": "বার",
        "Gap between pulses": "প্রতি বারের ব্যবধান",
        "Sound": "শব্দ",
        "Ding": "ডিং",
        "Chord": "সুর",
        "Chime": "ঘণ্টা",
        "Notify": "বিজ্ঞপ্তি",
        "Volume": "আওয়াজ",
        "Test": "শুনুন",
        "Dot size": "বিন্দুর আকার",
        "Word to show": "যে শব্দ দেখাবে",
        "Word size": "শব্দের আকার",
        "Position": "অবস্থান",
        "Centre": "মাঝখানে",
        "Top left": "উপরে বাঁয়ে",
        "Top right": "উপরে ডানে",
        "Bottom left": "নিচে বাঁয়ে",
        "Bottom right": "নিচে ডানে",
        "Edge margin": "কিনারা থেকে দূরত্ব",
        "Show on every monitor": "প্রতিটি পর্দায় দেখান",
        "Done": "সম্পন্ন",

        "Look into the distance": "দূরে তাকান",

        # The ask cards, the tray's review item, and the break's countdown switch.
        "Like the app?": "অ্যাপটি ভালো লাগছে?",
        "If this independent app works well for you, would you consider a small donation? Thank you!": "স্বাধীনভাবে তৈরি এই অ্যাপটি আপনার কাজে এলে, একটি ছোট অনুদানের কথা ভাববেন কি? ধন্যবাদ!",
        "Finding it useful?": "এটি কি কাজে লাগছে?",
        "A short review helps others with tired eyes find it. Thank you!": "একটি ছোট রিভিউ ক্লান্ত চোখের অন্যদের এটি খুঁজে পেতে সাহায্য করে। ধন্যবাদ!",
        "Don’t ask again": "আর দেখাবেন না",
        "Rate this app": "এই অ্যাপটিকে রেটিং দিন",
        "Show countdown": "কাউন্টডাউন দেখান",

        # The welcome card, the taught reminder and the strength question.
        "Show me": "দেখান",
        "Close…\nsqueeze…\nopen": "বন্ধ করুন…\nআলতো চাপুন…\nখুলুন",
        "How it works": "কীভাবে কাজ করে",
        "Too weak or intrusive?": "খুব দুর্বল বা বিরক্তিকর?",
        "You can change these:": "আপনি এগুলো বদলাতে পারেন:",
        "How this app works?": "এই অ্যাপটি কীভাবে কাজ করে",
        "Too weak or too intrusive? Change strength, size, duration and sound in Settings.": "খুব দুর্বল বা বিরক্তিকর? সেটিংসে তীব্রতা, আকার, সময়কাল ও শব্দ বদলান।",
        "A cue appears periodically, to remind you to blink fully: close, squeeze gently, open.": "একটি সংকেত নিয়মিত দেখা দেয়, যাতে আপনি পুরোপুরি চোখের পলক ফেলতে মনে রাখেন: চোখ বন্ধ করুন, আলতো করে চেপে ধরুন, খুলুন।",
        "Size": "আকার",
        "Duration": "সময়কাল",
    },

    # Arabic. The TEXT shapes and runs right to left correctly -- Tk gets
    # that from Windows. The LAYOUT is not mirrored: labels sit on the left
    # of their rows and controls on the right, as in every other language.
    # That is a real compromise and it is the honest state of things; see
    # LOCALISATION.md.
    "ar": {
        "Blink now": "ارمش الآن",
        "Resume reminders": "استئناف التذكيرات",
        "Snooze 30 minutes": "إيقاف 30 دقيقة",
        "Settings": "الإعدادات",
        "Buy me a coffee": "ادعمني بقهوة",
        "Quit": "إنهاء",

        "Got it": "حسنًا",

        "%s is already running.\n\nLook for its icon in the system tray, "
        "next to the clock -- you may need to click the ^ arrow to see it. "
        "Right-click the icon for Settings.":
            "%s يعمل بالفعل.\n\nابحث عن أيقونته في منطقة الإشعارات بجوار "
            "الساعة — قد تحتاج إلى النقر على السهم ^ لرؤيتها. انقر بالزر "
            "الأيمن على الأيقونة لفتح الإعدادات.",

        "A gentle nudge on every screen.": "تنبيه لطيف على كل شاشة.",
        "Start with Windows": "التشغيل مع Windows",
        "Startup: managed by Windows": "بدء التشغيل: يديره Windows",
        "Startup: turned off in Task Manager": "بدء التشغيل: معطّل في المدير",
        "Preview blink": "معاينة الرمش",
        "Preview break": "معاينة الراحة",
        "Cancel": "إلغاء",
        "Save": "حفظ",
        "Save the changes you made?": "حفظ التغييرات؟",

        "Blink": "الرمش",
        "Remind me every": "ذكّرني كل",
        "seconds": "ثانية",
        "minutes": "دقيقة",

        "Break": "راحة",
        "Look at trees!": "انظر إلى الأشجار!",
        "Remind me to look away": "ذكّرني بالنظر بعيدًا",
        "min": "د",

        "A dot": "نقطة",
        "A word": "كلمة",
        "Dim screen": "تعتيم",
        "Strength": "الشدة",
        "Colour": "اللون",
        "Change...": "تغيير…",
        "Play a sound": "تشغيل صوت",
        "  Advanced settings": "  إعدادات متقدمة",

        "Advanced settings - Blink": "إعدادات متقدمة — الرمش",
        "Blink timing and sound": "الرمش: التوقيت والصوت",
        "Blink look": "مظهر الرمش",
        "Advanced settings - Break": "إعدادات متقدمة — الراحة",
        "Break timing and sound": "الراحة: التوقيت والصوت",
        "Break look": "مظهر الراحة",
        "Flash style": "نمط الوميض",
        "Gentle": "لطيف",
        "Standard": "عادي",
        "Sharp": "واضح",
        "Custom": "مخصص",
        "Hold (s)": "الثبات (ث)",
        "Fade (s)": "التلاشي (ث)",
        "Pulses": "مرات",
        "Gap between pulses": "الفاصل بين المرات",
        "Sound": "الصوت",
        "Ding": "رنة",
        "Chord": "وتر",
        "Chime": "جرس",
        "Notify": "تنبيه",
        "Volume": "مستوى الصوت",
        "Test": "تجربة",
        "Dot size": "حجم النقطة",
        "Word to show": "الكلمة المعروضة",
        "Word size": "حجم الكلمة",
        "Position": "الموضع",
        "Centre": "الوسط",
        "Top left": "أعلى اليسار",
        "Top right": "أعلى اليمين",
        "Bottom left": "أسفل اليسار",
        "Bottom right": "أسفل اليمين",
        "Edge margin": "المسافة من الحافة",
        "Show on every monitor": "إظهار على كل شاشة",
        "Done": "تم",

        "Look into the distance": "انظر بعيدًا",

        # The ask cards, the tray's review item, and the break's countdown switch.
        "Like the app?": "هل أعجبك التطبيق؟",
        "If this independent app works well for you, would you consider a small donation? Thank you!": "إن كان هذا التطبيق المستقل يناسبك، فهل تفكر في تبرع صغير؟ شكرًا!",
        "Finding it useful?": "هل تجده مفيدًا؟",
        "A short review helps others with tired eyes find it. Thank you!": "مراجعة قصيرة تساعد آخرين يعانون من إجهاد العين على العثور عليه. شكرًا!",
        "Don’t ask again": "لا تسألني مجددًا",
        "Rate this app": "قيّم هذا التطبيق",
        "Show countdown": "إظهار العد التنازلي",

        # The welcome card, the taught reminder and the strength question.
        "Show me": "أرني",
        "Close…\nsqueeze…\nopen": "أغمض…\nاضغط…\nافتح",
        "How it works": "طريقة العمل",
        "Too weak or intrusive?": "ضعيفة جدًا أو مزعجة؟",
        "You can change these:": "يمكنك تغيير ما يلي:",
        "How this app works?": "كيف يعمل هذا التطبيق؟",
        "Too weak or too intrusive? Change strength, size, duration and sound in Settings.": "ضعيفة جدًا أو مزعجة؟ غيّر الشدة والحجم والمدة والصوت من الإعدادات.",
        "A cue appears periodically, to remind you to blink fully: close, squeeze gently, open.": "تظهر إشارة بشكل دوري لتذكيرك بأن ترمش رمشة كاملة: أغمض عينيك، اضغط جفنيك برفق، ثم افتحهما.",
        "Size": "الحجم",
        "Duration": "المدة",
    },

    # Urdu. Same caveat as Arabic: the text is right, the layout is not
    # mirrored. Set in Segoe UI's naskh rather than Windows' nastaliq face,
    # which is calligraphic and far too tall for a 32-pixel row.
    "ur": {
        "Blink now": "ابھی پلک جھپکیں",
        "Resume reminders": "یاد دہانیاں دوبارہ",
        "Snooze 30 minutes": "30 منٹ روکیں",
        "Settings": "ترتیبات",
        "Buy me a coffee": "مجھے کافی پلائیں",
        "Quit": "بند کریں",

        "Got it": "ٹھیک ہے",

        "%s is already running.\n\nLook for its icon in the system tray, "
        "next to the clock -- you may need to click the ^ arrow to see it. "
        "Right-click the icon for Settings.":
            "%s پہلے سے چل رہا ہے۔\n\nگھڑی کے پاس اطلاعی حصے میں اس کا آئیکن "
            "تلاش کریں — دیکھنے کے لیے ^ تیر پر کلک کرنا پڑ سکتا ہے۔ "
            "ترتیبات کے لیے آئیکن پر دائیں کلک کریں۔",

        "A gentle nudge on every screen.": "ہر اسکرین پر ایک نرم اشارہ۔",
        "Start with Windows": "Windows کے ساتھ شروع",
        "Startup: managed by Windows": "آغاز: Windows کے تحت",
        "Startup: turned off in Task Manager": "آغاز: ٹاسک مینیجر میں بند",
        "Preview blink": "پلک دیکھیں",
        "Preview break": "وقفہ دیکھیں",
        "Cancel": "منسوخ",
        "Save": "محفوظ",
        "Save the changes you made?": "تبدیلیاں محفوظ کریں؟",

        "Blink": "پلک",
        "Remind me every": "یاد دلائیں ہر",
        "seconds": "سیکنڈ",
        "minutes": "منٹ",

        "Break": "وقفہ",
        "Look at trees!": "درختوں کو دیکھیں!",
        "Remind me to look away": "دور دیکھنے کی یاد دلائیں",
        "min": "منٹ",

        "A dot": "نقطہ",
        "A word": "لفظ",
        "Dim screen": "مدھم",
        "Strength": "شدت",
        "Colour": "رنگ",
        "Change...": "تبدیل…",
        "Play a sound": "آواز چلائیں",
        "  Advanced settings": "  اعلیٰ ترتیبات",

        "Advanced settings - Blink": "اعلیٰ ترتیبات — پلک",
        "Blink timing and sound": "پلک: وقت اور آواز",
        "Blink look": "پلک کی شکل",
        "Advanced settings - Break": "اعلیٰ ترتیبات — وقفہ",
        "Break timing and sound": "وقفہ: وقت اور آواز",
        "Break look": "وقفے کی شکل",
        "Flash style": "چمک کا انداز",
        "Gentle": "نرم",
        "Standard": "عام",
        "Sharp": "واضح",
        "Custom": "اپنا",
        "Hold (s)": "ٹھہراؤ (س)",
        "Fade (s)": "دھندلا (س)",
        "Pulses": "بار",
        "Gap between pulses": "ہر بار کا وقفہ",
        "Sound": "آواز",
        "Ding": "ڈنگ",
        "Chord": "سُر",
        "Chime": "گھنٹی",
        "Notify": "اطلاع",
        "Volume": "آواز کی سطح",
        "Test": "سنیں",
        "Dot size": "نقطے کا سائز",
        "Word to show": "دکھانے کا لفظ",
        "Word size": "لفظ کا سائز",
        "Position": "مقام",
        "Centre": "درمیان",
        "Top left": "اوپر بائیں",
        "Top right": "اوپر دائیں",
        "Bottom left": "نیچے بائیں",
        "Bottom right": "نیچے دائیں",
        "Edge margin": "کنارے سے فاصلہ",
        "Show on every monitor": "ہر اسکرین پر دکھائیں",
        "Done": "مکمل",

        "Look into the distance": "دور دیکھیں",

        # The ask cards, the tray's review item, and the break's countdown switch.
        "Like the app?": "ایپ پسند آئی؟",
        "If this independent app works well for you, would you consider a small donation? Thank you!": "اگر آزادانہ طور پر بنائی گئی یہ ایپ آپ کے کام آ رہی ہے تو کیا آپ ایک چھوٹے سے عطیے پر غور کریں گے؟ شکریہ!",
        "Finding it useful?": "کیا یہ مفید لگ رہی ہے؟",
        "A short review helps others with tired eyes find it. Thank you!": "ایک مختصر ریویو تھکی آنکھوں والے دوسرے لوگوں کو اسے ڈھونڈنے میں مدد دیتا ہے۔ شکریہ!",
        "Don’t ask again": "دوبارہ نہ پوچھیں",
        "Rate this app": "اس ایپ کی درجہ بندی کریں",
        "Show countdown": "الٹی گنتی دکھائیں",

        # The welcome card, the taught reminder and the strength question.
        "Show me": "دکھائیں",
        "Close…\nsqueeze…\nopen": "بند کریں…\nبھینچیں…\nکھولیں",
        "How it works": "یہ کیسے کام کرتی ہے",
        "Too weak or intrusive?": "بہت کمزور یا خلل ڈالنے والا؟",
        "You can change these:": "آپ یہ بدل سکتے ہیں:",
        "How this app works?": "یہ ایپ کیسے کام کرتی ہے",
        "Too weak or too intrusive? Change strength, size, duration and sound in Settings.": "بہت کمزور یا خلل ڈالنے والا؟ ترتیبات میں شدت، سائز، دورانیہ اور آواز بدلیں۔",
        "A cue appears periodically, to remind you to blink fully: close, squeeze gently, open.": "ایک اشارہ وقتاً فوقتاً ظاہر ہوتا ہے تاکہ آپ کو پوری طرح پلک جھپکنا یاد رہے: آنکھیں بند کریں، ہلکا سا بھینچیں، کھولیں۔",
        "Size": "سائز",
        "Duration": "دورانیہ",
    },

    # Indonesian.
    "id": {
        "Blink now": "Kedip sekarang",
        "Resume reminders": "Lanjutkan pengingat",
        "Snooze 30 minutes": "Tunda 30 menit",
        "Settings": "Pengaturan",
        "Buy me a coffee": "Traktir saya kopi",
        "Quit": "Keluar",

        "Got it": "Mengerti",

        "%s is already running.\n\nLook for its icon in the system tray, "
        "next to the clock -- you may need to click the ^ arrow to see it. "
        "Right-click the icon for Settings.":
            "%s sudah berjalan.\n\nCari ikonnya di area notifikasi, di "
            "sebelah jam — mungkin perlu klik panah ^ untuk melihatnya. "
            "Klik kanan ikon untuk membuka pengaturan.",

        "A gentle nudge on every screen.": "Pengingat lembut di setiap layar.",
        "Start with Windows": "Jalankan saat Windows mulai",
        "Startup: managed by Windows": "Startup: dikelola Windows",
        "Startup: turned off in Task Manager":
            "Startup: dimatikan di Task Manager",
        "Preview blink": "Coba kedip",
        "Preview break": "Coba istirahat",
        "Cancel": "Batal",
        "Save": "Simpan",
        "Save the changes you made?": "Simpan perubahan?",

        "Blink": "Kedip",
        "Remind me every": "Ingatkan setiap",
        "seconds": "detik",
        "minutes": "menit",

        "Break": "Istirahat",
        "Look at trees!": "Lihat pepohonan!",
        "Remind me to look away": "Ingatkan melihat jauh",
        "min": "mnt",

        "A dot": "Titik",
        "A word": "Kata",
        "Dim screen": "Redupkan",
        "Strength": "Kekuatan",
        "Colour": "Warna",
        "Change...": "Ubah…",
        "Play a sound": "Putar suara",
        "  Advanced settings": "  Pengaturan lanjutan",

        "Advanced settings - Blink": "Pengaturan lanjutan — Kedip",
        "Blink timing and sound": "Kedip: waktu dan suara",
        "Blink look": "Tampilan kedip",
        "Advanced settings - Break": "Pengaturan lanjutan — Istirahat",
        "Break timing and sound": "Istirahat: waktu dan suara",
        "Break look": "Tampilan istirahat",
        "Flash style": "Gaya kilatan",
        "Gentle": "Lembut",
        "Standard": "Standar",
        "Sharp": "Tegas",
        "Custom": "Khusus",
        "Hold (s)": "Tahan (dtk)",
        "Fade (s)": "Pudar (dtk)",
        "Pulses": "Jumlah",
        "Gap between pulses": "Jeda antar kilatan",
        "Sound": "Suara",
        "Ding": "Ding",
        "Chord": "Akor",
        "Chime": "Lonceng",
        "Notify": "Notif",
        "Volume": "Volume",
        "Test": "Coba",
        "Dot size": "Ukuran titik",
        "Word to show": "Kata yang tampil",
        "Word size": "Ukuran kata",
        "Position": "Posisi",
        "Centre": "Tengah",
        "Top left": "Kiri atas",
        "Top right": "Kanan atas",
        "Bottom left": "Kiri bawah",
        "Bottom right": "Kanan bawah",
        "Edge margin": "Jarak dari tepi",
        "Show on every monitor": "Tampilkan di semua layar",
        "Done": "Selesai",

        "Look into the distance": "Lihat ke kejauhan",

        # The ask cards, the tray's review item, and the break's countdown switch.
        "Like the app?": "Suka aplikasinya?",
        "If this independent app works well for you, would you consider a small donation? Thank you!": "Jika aplikasi independen ini bekerja dengan baik untuk Anda, maukah Anda mempertimbangkan donasi kecil? Terima kasih!",
        "Finding it useful?": "Apakah bermanfaat?",
        "A short review helps others with tired eyes find it. Thank you!": "Ulasan singkat membantu orang lain yang matanya lelah menemukannya. Terima kasih!",
        "Don’t ask again": "Jangan tanya lagi",
        "Rate this app": "Beri nilai aplikasi ini",
        "Show countdown": "Tampilkan hitung mundur",

        # The welcome card, the taught reminder and the strength question.
        "Show me": "Tunjukkan",
        "Close…\nsqueeze…\nopen": "Pejamkan…\nrapatkan…\nbuka",
        "How it works": "Cara kerjanya",
        "Too weak or intrusive?": "Terlalu lemah atau mengganggu?",
        "You can change these:": "Anda bisa mengubah:",
        "How this app works?": "Cara kerja aplikasi ini",
        "Too weak or too intrusive? Change strength, size, duration and sound in Settings.": "Terlalu lemah atau mengganggu? Ubah kekuatan, ukuran, durasi, dan suara di Pengaturan.",
        "A cue appears periodically, to remind you to blink fully: close, squeeze gently, open.": "Isyarat muncul secara berkala untuk mengingatkan Anda berkedip sepenuhnya: pejamkan, rapatkan perlahan, buka.",
        "Size": "Ukuran",
        "Duration": "Durasi",
    },

    # Polish. The interval strings use abbreviated units -- "co %d s", not
    # "co %d sekundy" -- because Polish has three plural forms and this
    # table has slots for two. An abbreviation is invariant, so it is
    # correct for 1, 2 and 5 alike; spelling it out would be wrong for two
    # of the three.
    "pl": {
        "Blink now": "Mrugnij teraz",
        "Resume reminders": "Wznów przypomnienia",
        "Snooze 30 minutes": "Wstrzymaj na 30 minut",
        "Settings": "Ustawienia",
        "Buy me a coffee": "Postaw mi kawę",
        "Quit": "Zakończ",

        "Got it": "Rozumiem",

        "%s is already running.\n\nLook for its icon in the system tray, "
        "next to the clock -- you may need to click the ^ arrow to see it. "
        "Right-click the icon for Settings.":
            "%s już działa.\n\nPoszukaj ikony w obszarze powiadomień obok "
            "zegara — może być potrzebne kliknięcie strzałki ^. Kliknij "
            "ikonę prawym przyciskiem, aby otworzyć ustawienia.",

        "A gentle nudge on every screen.":
            "Delikatne przypomnienie na każdym ekranie.",
        "Start with Windows": "Uruchamiaj z Windows",
        "Startup: managed by Windows": "Autostart: zarządza Windows",
        "Startup: turned off in Task Manager":
            "Autostart: wyłączony w Menedżerze",
        "Preview blink": "Podgląd mrugnięcia",
        "Preview break": "Podgląd przerwy",
        "Cancel": "Anuluj",
        "Save": "Zapisz",
        "Save the changes you made?": "Zapisać zmiany?",

        "Blink": "Mrugnięcie",
        "Remind me every": "Przypominaj co",
        "seconds": "sekundy",
        "minutes": "minuty",

        "Break": "Przerwa",
        "Look at trees!": "Popatrz na drzewa!",
        "Remind me to look away": "Przypominaj o patrzeniu w dal",
        "min": "min",

        "A dot": "Kropka",
        "A word": "Słowo",
        "Dim screen": "Ściemnij",
        "Strength": "Siła",
        "Colour": "Kolor",
        "Change...": "Zmień…",
        "Play a sound": "Odtwórz dźwięk",
        "  Advanced settings": "  Ustawienia zaawansowane",

        "Advanced settings - Blink": "Ustawienia zaawansowane — Mrugnięcie",
        "Blink timing and sound": "Mrugnięcie: czas i dźwięk",
        "Blink look": "Wygląd mrugnięcia",
        "Advanced settings - Break": "Ustawienia zaawansowane — Przerwa",
        "Break timing and sound": "Przerwa: czas i dźwięk",
        "Break look": "Wygląd przerwy",
        "Flash style": "Styl błysku",
        "Gentle": "Łagodny",
        "Standard": "Zwykły",
        "Sharp": "Ostry",
        "Custom": "Własny",
        "Hold (s)": "Trwanie (s)",
        "Fade (s)": "Zanik (s)",
        "Pulses": "Błyski",
        "Gap between pulses": "Odstęp między błyskami",
        "Sound": "Dźwięk",
        "Ding": "Ding",
        "Chord": "Akord",
        "Chime": "Dzwonek",
        "Notify": "Sygnał",
        "Volume": "Głośność",
        "Test": "Odsłuch",
        "Dot size": "Rozmiar kropki",
        "Word to show": "Wyświetlane słowo",
        "Word size": "Rozmiar słowa",
        "Position": "Pozycja",
        "Centre": "Środek",
        "Top left": "Lewy górny",
        "Top right": "Prawy górny",
        "Bottom left": "Lewy dolny",
        "Bottom right": "Prawy dolny",
        "Edge margin": "Margines od krawędzi",
        "Show on every monitor": "Pokaż na każdym ekranie",
        "Done": "Gotowe",

        "Look into the distance": "Popatrz w dal",

        # The ask cards, the tray's review item, and the break's countdown switch.
        "Like the app?": "Podoba ci się aplikacja?",
        "If this independent app works well for you, would you consider a small donation? Thank you!": "Jeśli ta niezależna aplikacja dobrze ci służy, może rozważysz drobną darowiznę? Dziękuję!",
        "Finding it useful?": "Przydaje się?",
        "A short review helps others with tired eyes find it. Thank you!": "Krótka opinia pomoże innym ze zmęczonymi oczami ją znaleźć. Dziękuję!",
        "Don’t ask again": "Nie pytaj więcej",
        "Rate this app": "Oceń tę aplikację",
        "Show countdown": "Pokaż odliczanie",

        # The welcome card, the taught reminder and the strength question.
        "Show me": "Pokaż",
        "Close…\nsqueeze…\nopen": "Zamknij…\nzaciśnij…\notwórz",
        "How it works": "Jak to działa",
        "Too weak or intrusive?": "Za słaby lub zbyt natrętny?",
        "You can change these:": "Możesz zmienić:",
        "How this app works?": "Jak działa ta aplikacja",
        "Too weak or too intrusive? Change strength, size, duration and sound in Settings.": "Za słaby lub zbyt natrętny? Zmień siłę, rozmiar, czas trwania i dźwięk w Ustawieniach.",
        "A cue appears periodically, to remind you to blink fully: close, squeeze gently, open.": "Sygnał pojawia się regularnie i przypomina, by mrugać do końca: zamknij oczy, lekko je zaciśnij, otwórz.",
        "Size": "Rozmiar",
        "Duration": "Czas trwania",
    },

    # Turkish.
    "tr": {
        "Blink now": "Şimdi göz kırp",
        "Resume reminders": "Hatırlatmaları sürdür",
        "Snooze 30 minutes": "30 dakika ertele",
        "Settings": "Ayarlar",
        "Buy me a coffee": "Bana kahve ısmarla",
        "Quit": "Çıkış",

        "Got it": "Anladım",

        "%s is already running.\n\nLook for its icon in the system tray, "
        "next to the clock -- you may need to click the ^ arrow to see it. "
        "Right-click the icon for Settings.":
            "%s zaten çalışıyor.\n\nSimgesini saatin yanındaki bildirim "
            "alanında arayın — görmek için ^ okuna tıklamanız gerekebilir. "
            "Ayarlar için simgeye sağ tıklayın.",

        "A gentle nudge on every screen.":
            "Her ekranda nazik bir hatırlatma.",
        "Start with Windows": "Windows ile başlat",
        "Startup: managed by Windows": "Başlangıç: Windows yönetir",
        "Startup: turned off in Task Manager":
            "Başlangıç: Görev Yöneticisinde kapalı",
        "Preview blink": "Göz kırpmayı dene",
        "Preview break": "Molayı dene",
        "Cancel": "İptal",
        "Save": "Kaydet",
        "Save the changes you made?": "Değişiklikler kaydedilsin mi?",

        "Blink": "Göz kırpma",
        "Remind me every": "Hatırlat her",
        "seconds": "saniye",
        "minutes": "dakika",

        "Break": "Mola",
        "Look at trees!": "Ağaçlara bak!",
        "Remind me to look away": "Uzağa bakmayı hatırlat",
        "min": "dk",

        "A dot": "Nokta",
        "A word": "Kelime",
        "Dim screen": "Karart",
        "Strength": "Şiddet",
        "Colour": "Renk",
        "Change...": "Değiştir…",
        "Play a sound": "Ses çal",
        "  Advanced settings": "  Gelişmiş ayarlar",

        "Advanced settings - Blink": "Gelişmiş ayarlar — Göz kırpma",
        "Blink timing and sound": "Göz kırpma: süre ve ses",
        "Blink look": "Göz kırpma görünümü",
        "Advanced settings - Break": "Gelişmiş ayarlar — Mola",
        "Break timing and sound": "Mola: süre ve ses",
        "Break look": "Mola görünümü",
        "Flash style": "Parlama biçimi",
        "Gentle": "Yumuşak",
        "Standard": "Standart",
        "Sharp": "Belirgin",
        "Custom": "Özel",
        "Hold (s)": "Süre (sn)",
        "Fade (s)": "Solma (sn)",
        "Pulses": "Tekrar",
        "Gap between pulses": "Tekrarlar arası",
        "Sound": "Ses",
        "Ding": "Ding",
        "Chord": "Akor",
        "Chime": "Çan",
        "Notify": "Uyarı",
        "Volume": "Ses düzeyi",
        "Test": "Dinle",
        "Dot size": "Nokta boyutu",
        "Word to show": "Gösterilecek kelime",
        "Word size": "Yazı boyutu",
        "Position": "Konum",
        "Centre": "Orta",
        "Top left": "Sol üst",
        "Top right": "Sağ üst",
        "Bottom left": "Sol alt",
        "Bottom right": "Sağ alt",
        "Edge margin": "Kenar boşluğu",
        "Show on every monitor": "Her ekranda göster",
        "Done": "Tamam",

        "Look into the distance": "Uzağa bak",

        # The ask cards, the tray's review item, and the break's countdown switch.
        "Like the app?": "Uygulamayı beğendiniz mi?",
        "If this independent app works well for you, would you consider a small donation? Thank you!": "Bu bağımsız uygulama işinize yarıyorsa, küçük bir bağış yapmayı düşünür müsünüz? Teşekkürler!",
        "Finding it useful?": "İşinize yarıyor mu?",
        "A short review helps others with tired eyes find it. Thank you!": "Kısa bir değerlendirme, gözleri yorgun başkalarının onu bulmasına yardımcı olur. Teşekkürler!",
        "Don’t ask again": "Bir daha sorma",
        "Rate this app": "Bu uygulamayı değerlendir",
        "Show countdown": "Geri sayımı göster",

        # The welcome card, the taught reminder and the strength question.
        "Show me": "Göster",
        "Close…\nsqueeze…\nopen": "Kapatın…\nsıkın…\naçın",
        "How it works": "Nasıl çalışır",
        "Too weak or intrusive?": "Zayıf mı, rahatsız edici mi?",
        "You can change these:": "Şunları değiştirebilirsiniz:",
        "How this app works?": "Bu uygulama nasıl çalışır?",
        "Too weak or too intrusive? Change strength, size, duration and sound in Settings.": "Çok mu zayıf, çok mu rahatsız edici? Ayarlar'dan şiddeti, boyutu, süreyi ve sesi değiştirin.",
        "A cue appears periodically, to remind you to blink fully: close, squeeze gently, open.": "Gözlerinizi tam kırpmanızı hatırlatmak için düzenli aralıklarla bir uyarı belirir: kapatın, hafifçe sıkın, açın.",
        "Size": "Boyut",
        "Duration": "Süre",
    },

    # Vietnamese.
    "vi": {
        "Blink now": "Chớp mắt ngay",
        "Resume reminders": "Tiếp tục nhắc",
        "Snooze 30 minutes": "Tạm dừng 30 phút",
        "Settings": "Cài đặt",
        "Buy me a coffee": "Mời tôi ly cà phê",
        "Quit": "Thoát",

        "Got it": "Đã hiểu",

        "%s is already running.\n\nLook for its icon in the system tray, "
        "next to the clock -- you may need to click the ^ arrow to see it. "
        "Right-click the icon for Settings.":
            "%s đang chạy rồi.\n\nTìm biểu tượng ở khay hệ thống, cạnh đồng "
            "hồ — có thể phải nhấp mũi tên ^ mới thấy. Nhấp chuột phải vào "
            "biểu tượng để mở cài đặt.",

        "A gentle nudge on every screen.":
            "Một nhắc nhở nhẹ trên mọi màn hình.",
        "Start with Windows": "Khởi động cùng Windows",
        "Startup: managed by Windows": "Khởi động: Windows quản lý",
        "Startup: turned off in Task Manager":
            "Khởi động: đã tắt trong Task Manager",
        "Preview blink": "Thử chớp mắt",
        "Preview break": "Thử nghỉ",
        "Cancel": "Hủy",
        "Save": "Lưu",
        "Save the changes you made?": "Lưu thay đổi?",

        "Blink": "Chớp mắt",
        "Remind me every": "Nhắc mỗi",
        "seconds": "giây",
        "minutes": "phút",

        "Break": "Nghỉ",
        "Look at trees!": "Nhìn cây xanh!",
        "Remind me to look away": "Nhắc tôi nhìn ra xa",
        "min": "phút",

        "A dot": "Chấm tròn",
        "A word": "Chữ",
        "Dim screen": "Làm mờ",
        "Strength": "Độ đậm",
        "Colour": "Màu",
        "Change...": "Đổi…",
        "Play a sound": "Phát âm thanh",
        "  Advanced settings": "  Cài đặt nâng cao",

        "Advanced settings - Blink": "Cài đặt nâng cao — Chớp mắt",
        "Blink timing and sound": "Chớp mắt: thời gian và âm thanh",
        "Blink look": "Giao diện chớp mắt",
        "Advanced settings - Break": "Cài đặt nâng cao — Nghỉ",
        "Break timing and sound": "Nghỉ: thời gian và âm thanh",
        "Break look": "Giao diện nghỉ",
        "Flash style": "Kiểu nháy",
        "Gentle": "Nhẹ",
        "Standard": "Chuẩn",
        "Sharp": "Rõ",
        "Custom": "Tùy ý",
        "Hold (s)": "Giữ (giây)",
        "Fade (s)": "Mờ dần (s)",
        "Pulses": "Số lần",
        "Gap between pulses": "Giữa các lần",
        "Sound": "Âm thanh",
        "Ding": "Ding",
        "Chord": "Hợp âm",
        "Chime": "Chuông",
        "Notify": "Báo",
        "Volume": "Âm lượng",
        "Test": "Nghe",
        "Dot size": "Cỡ chấm tròn",
        "Word to show": "Chữ hiển thị",
        "Word size": "Cỡ chữ",
        "Position": "Vị trí",
        "Centre": "Giữa",
        "Top left": "Trên trái",
        "Top right": "Trên phải",
        "Bottom left": "Dưới trái",
        "Bottom right": "Dưới phải",
        "Edge margin": "Cách mép",
        "Show on every monitor": "Hiện trên mọi màn hình",
        "Done": "Xong",

        "Look into the distance": "Nhìn ra xa",

        # The ask cards, the tray's review item, and the break's countdown switch.
        "Like the app?": "Bạn thích ứng dụng này chứ?",
        "If this independent app works well for you, would you consider a small donation? Thank you!": "Nếu ứng dụng độc lập này hữu ích với bạn, bạn có muốn ủng hộ một khoản nhỏ không? Cảm ơn bạn!",
        "Finding it useful?": "Bạn thấy hữu ích chứ?",
        "A short review helps others with tired eyes find it. Thank you!": "Một đánh giá ngắn giúp những người mỏi mắt khác tìm thấy nó. Cảm ơn bạn!",
        "Don’t ask again": "Đừng hỏi lại",
        "Rate this app": "Đánh giá ứng dụng này",
        "Show countdown": "Hiện đếm ngược",

        # The welcome card, the taught reminder and the strength question.
        "Show me": "Cho tôi xem",
        "Close…\nsqueeze…\nopen": "Nhắm mắt…\nkhép chặt…\nmở ra",
        "How it works": "Cách hoạt động",
        "Too weak or intrusive?": "Quá yếu hay gây phiền?",
        "You can change these:": "Bạn có thể thay đổi:",
        "How this app works?": "Cách ứng dụng hoạt động",
        "Too weak or too intrusive? Change strength, size, duration and sound in Settings.": "Quá yếu hay gây phiền? Đổi độ đậm, kích thước, thời lượng và âm thanh trong Cài đặt.",
        "A cue appears periodically, to remind you to blink fully: close, squeeze gently, open.": "Tín hiệu xuất hiện định kỳ để nhắc bạn chớp mắt trọn vẹn: nhắm mắt, khép chặt nhẹ nhàng, mở ra.",
        "Size": "Kích thước",
        "Duration": "Thời lượng",
    },

    # Russian. Abbreviated interval units for the same reason as Polish:
    # three plural forms, two slots, and "сек." is invariant.
    "ru": {
        "Blink now": "Моргнуть сейчас",
        "Resume reminders": "Возобновить напоминания",
        "Snooze 30 minutes": "Пауза 30 минут",
        "Settings": "Настройки",
        "Buy me a coffee": "Купить мне кофе",
        "Quit": "Выход",

        "Got it": "Понятно",

        "%s is already running.\n\nLook for its icon in the system tray, "
        "next to the clock -- you may need to click the ^ arrow to see it. "
        "Right-click the icon for Settings.":
            "%s уже работает.\n\nНайдите значок в области уведомлений рядом "
            "с часами — возможно, придётся нажать стрелку ^. Щёлкните по "
            "значку правой кнопкой, чтобы открыть настройки.",

        "A gentle nudge on every screen.":
            "Мягкое напоминание на каждом экране.",
        "Start with Windows": "Запускать с Windows",
        "Startup: managed by Windows": "Автозапуск: управляет Windows",
        "Startup: turned off in Task Manager":
            "Автозапуск: отключён в Диспетчере",
        "Preview blink": "Проба моргания",
        "Preview break": "Проба паузы",
        "Cancel": "Отмена",
        "Save": "Сохранить",
        "Save the changes you made?": "Сохранить изменения?",

        "Blink": "Моргание",
        "Remind me every": "Напоминать каждые",
        "seconds": "секунды",
        "minutes": "минуты",

        "Break": "Пауза",
        "Look at trees!": "Посмотрите на деревья!",
        "Remind me to look away": "Напоминать смотреть вдаль",
        "min": "мин",

        "A dot": "Точка",
        "A word": "Слово",
        "Dim screen": "Затемнить",
        "Strength": "Сила",
        "Colour": "Цвет",
        "Change...": "Изменить…",
        "Play a sound": "Звуковой сигнал",
        "  Advanced settings": "  Дополнительно",

        "Advanced settings - Blink": "Дополнительно — Моргание",
        "Blink timing and sound": "Моргание: время и звук",
        "Blink look": "Вид моргания",
        "Advanced settings - Break": "Дополнительно — Пауза",
        "Break timing and sound": "Пауза: время и звук",
        "Break look": "Вид паузы",
        "Flash style": "Тип вспышки",
        "Gentle": "Мягко",
        "Standard": "Обычно",
        "Sharp": "Резко",
        "Custom": "Своё",
        "Hold (s)": "Показ (с)",
        "Fade (s)": "Затухание (с)",
        "Pulses": "Повторы",
        "Gap between pulses": "Пауза между повторами",
        "Sound": "Звук",
        "Ding": "Дин",
        "Chord": "Аккорд",
        "Chime": "Звон",
        "Notify": "Сигнал",
        "Volume": "Громкость",
        "Test": "Проба",
        "Dot size": "Размер точки",
        "Word to show": "Какое слово",
        "Word size": "Размер слова",
        "Position": "Положение",
        "Centre": "По центру",
        "Top left": "Сверху слева",
        "Top right": "Сверху справа",
        "Bottom left": "Снизу слева",
        "Bottom right": "Снизу справа",
        "Edge margin": "Отступ от края",
        "Show on every monitor": "Показывать на всех экранах",
        "Done": "Готово",

        "Look into the distance": "Посмотрите вдаль",

        # The ask cards, the tray's review item, and the break's countdown switch.
        "Like the app?": "Нравится приложение?",
        "If this independent app works well for you, would you consider a small donation? Thank you!": "Если это независимое приложение вам подходит, не рассмотрите ли небольшое пожертвование? Спасибо!",
        "Finding it useful?": "Приложение полезно?",
        "A short review helps others with tired eyes find it. Thank you!": "Короткий отзыв поможет другим людям с уставшими глазами найти его. Спасибо!",
        "Don’t ask again": "Больше не спрашивать",
        "Rate this app": "Оценить приложение",
        "Show countdown": "Показывать обратный отсчёт",

        # The welcome card, the taught reminder and the strength question.
        "Show me": "Показать",
        "Close…\nsqueeze…\nopen": "Закройте…\nсожмите…\nоткройте",
        "How it works": "Как это работает",
        "Too weak or intrusive?": "Слишком слабо или навязчиво?",
        "You can change these:": "Можно изменить:",
        "How this app works?": "Как работает приложение",
        "Too weak or too intrusive? Change strength, size, duration and sound in Settings.": "Слишком слабо или навязчиво? Измените силу, размер, длительность и звук в настройках.",
        "A cue appears periodically, to remind you to blink fully: close, squeeze gently, open.": "Сигнал появляется регулярно и напоминает моргать полностью: закройте глаза, мягко сожмите веки, откройте.",
        "Size": "Размер",
        "Duration": "Длительность",
    },

    # Thai. Written without spaces between words, so the notice sentences
    # are single unbroken runs and are kept deliberately short.
    "th": {
        "Blink now": "กะพริบตาตอนนี้",
        "Resume reminders": "เริ่มเตือนอีกครั้ง",
        "Snooze 30 minutes": "หยุด 30 นาที",
        "Settings": "ตั้งค่า",
        "Buy me a coffee": "เลี้ยงกาแฟ",
        "Quit": "ออก",

        "Got it": "เข้าใจแล้ว",

        "%s is already running.\n\nLook for its icon in the system tray, "
        "next to the clock -- you may need to click the ^ arrow to see it. "
        "Right-click the icon for Settings.":
            "%s กำลังทำงานอยู่แล้ว\n\nมองหาไอคอนในพื้นที่แจ้งเตือนข้างนาฬิกา "
            "— อาจต้องคลิกลูกศร ^ ก่อนจึงจะเห็น คลิกขวาที่ไอคอนเพื่อตั้งค่า",

        "A gentle nudge on every screen.": "เตือนเบา ๆ บนทุกหน้าจอ",
        "Start with Windows": "เริ่มพร้อม Windows",
        "Startup: managed by Windows": "เริ่มต้น: Windows จัดการ",
        "Startup: turned off in Task Manager":
            "เริ่มต้น: ปิดใน Task Manager",
        "Preview blink": "ลองกะพริบตา",
        "Preview break": "ลองพัก",
        "Cancel": "ยกเลิก",
        "Save": "บันทึก",
        "Save the changes you made?": "บันทึกการเปลี่ยนแปลงไหม",

        "Blink": "กะพริบตา",
        "Remind me every": "เตือนทุก",
        "seconds": "วินาที",
        "minutes": "นาที",

        "Break": "พัก",
        "Look at trees!": "มองต้นไม้สิ!",
        "Remind me to look away": "เตือนให้มองไกล ๆ",
        "min": "นาที",

        "A dot": "จุด",
        "A word": "ข้อความ",
        "Dim screen": "หรี่จอ",
        "Strength": "ความเข้ม",
        "Colour": "สี",
        "Change...": "เปลี่ยน…",
        "Play a sound": "เล่นเสียง",
        "  Advanced settings": "  ตั้งค่าขั้นสูง",

        "Advanced settings - Blink": "ตั้งค่าขั้นสูง — กะพริบตา",
        "Blink timing and sound": "กะพริบตา: เวลาและเสียง",
        "Blink look": "รูปแบบกะพริบตา",
        "Advanced settings - Break": "ตั้งค่าขั้นสูง — พัก",
        "Break timing and sound": "พัก: เวลาและเสียง",
        "Break look": "รูปแบบการพัก",
        "Flash style": "ลักษณะการกะพริบ",
        "Gentle": "นุ่มนวล",
        "Standard": "มาตรฐาน",
        "Sharp": "ชัดเจน",
        "Custom": "กำหนดเอง",
        "Hold (s)": "ค้าง (วิ)",
        "Fade (s)": "จางหาย (วิ)",
        "Pulses": "จำนวนครั้ง",
        "Gap between pulses": "ช่วงห่างแต่ละครั้ง",
        "Sound": "เสียง",
        "Ding": "ติ๊ง",
        "Chord": "คอร์ด",
        "Chime": "ระฆัง",
        "Notify": "แจ้งเตือน",
        "Volume": "ระดับเสียง",
        "Test": "ฟัง",
        "Dot size": "ขนาดจุด",
        "Word to show": "ข้อความที่แสดง",
        "Word size": "ขนาดข้อความ",
        "Position": "ตำแหน่ง",
        "Centre": "กึ่งกลาง",
        "Top left": "บนซ้าย",
        "Top right": "บนขวา",
        "Bottom left": "ล่างซ้าย",
        "Bottom right": "ล่างขวา",
        "Edge margin": "ระยะจากขอบ",
        "Show on every monitor": "แสดงบนทุกหน้าจอ",
        "Done": "เสร็จ",

        "Look into the distance": "มองไปไกล ๆ",

        # The ask cards, the tray's review item, and the break's countdown switch.
        "Like the app?": "ชอบแอปนี้ไหม",
        "If this independent app works well for you, would you consider a small donation? Thank you!": "ถ้าแอปอิสระนี้ใช้ได้ดีสำหรับคุณ ช่วยพิจารณาบริจาคเล็กน้อยได้ไหม ขอบคุณ!",
        "Finding it useful?": "มีประโยชน์ไหม",
        "A short review helps others with tired eyes find it. Thank you!": "รีวิวสั้น ๆ ช่วยให้คนอื่นที่ตาล้าหาแอปนี้เจอ ขอบคุณ!",
        "Don’t ask again": "ไม่ต้องถามอีก",
        "Rate this app": "ให้คะแนนแอปนี้",
        "Show countdown": "แสดงการนับถอยหลัง",

        # The welcome card, the taught reminder and the strength question.
        "Show me": "ลองดู",
        "Close…\nsqueeze…\nopen": "หลับตา…\nบีบเบาๆ…\nลืมตา",
        "How it works": "วิธีใช้งาน",
        "Too weak or intrusive?": "อ่อนเกินไปหรือรบกวน",
        "You can change these:": "คุณเปลี่ยนสิ่งเหล่านี้ได้",
        "How this app works?": "แอปนี้ทำงานอย่างไร",
        "Too weak or too intrusive? Change strength, size, duration and sound in Settings.": "อ่อนเกินไปหรือรบกวน เปลี่ยนความเข้ม ขนาด ระยะเวลา และเสียงได้ในตั้งค่า",
        "A cue appears periodically, to remind you to blink fully: close, squeeze gently, open.": "สัญญาณจะปรากฏขึ้นเป็นระยะ เพื่อเตือนให้กะพริบตาให้เต็มที่ หลับตา บีบตาเบาๆ แล้วลืมตา",
        "Size": "ขนาด",
        "Duration": "ระยะเวลา",
    },

    # Ukrainian. Abbreviated interval units, as for Russian and Polish:
    # three plural forms, two slots, and "с"/"хв" are invariant.
    "uk": {
        "Blink now": "Кліпнути зараз",
        "Resume reminders": "Відновити нагадування",
        "Snooze 30 minutes": "Пауза 30 хвилин",
        "Settings": "Налаштування",
        "Buy me a coffee": "Пригостити кавою",
        "Quit": "Вийти",

        "Got it": "Зрозуміло",

        "%s is already running.\n\nLook for its icon in the system tray, "
        "next to the clock -- you may need to click the ^ arrow to see it. "
        "Right-click the icon for Settings.":
            "%s уже працює.\n\nЗнайдіть значок в області сповіщень біля "
            "годинника — можливо, доведеться натиснути стрілку ^. Клацніть "
            "по значку правою кнопкою, щоб відкрити налаштування.",

        "A gentle nudge on every screen.":
            "М'яке нагадування на кожному екрані.",
        "Start with Windows": "Запускати з Windows",
        "Startup: managed by Windows": "Автозапуск: керує Windows",
        "Startup: turned off in Task Manager":
            "Автозапуск: вимкнено в Диспетчері",
        "Preview blink": "Проба кліпання",
        "Preview break": "Проба паузи",
        "Cancel": "Скасувати",
        "Save": "Зберегти",
        "Save the changes you made?": "Зберегти зміни?",

        "Blink": "Кліпання",
        "Remind me every": "Нагадувати кожні",
        "seconds": "секунди",
        "minutes": "хвилини",

        "Break": "Пауза",
        "Look at trees!": "Погляньте на дерева!",
        "Remind me to look away": "Нагадувати дивитися вдалечінь",
        "min": "хв",

        "A dot": "Крапка",
        "A word": "Слово",
        "Dim screen": "Затемнити",
        "Strength": "Сила",
        "Colour": "Колір",
        "Change...": "Змінити…",
        "Play a sound": "Звуковий сигнал",
        "  Advanced settings": "  Додатково",

        "Advanced settings - Blink": "Додатково — Кліпання",
        "Blink timing and sound": "Кліпання: час і звук",
        "Blink look": "Вигляд кліпання",
        "Advanced settings - Break": "Додатково — Пауза",
        "Break timing and sound": "Пауза: час і звук",
        "Break look": "Вигляд паузи",
        "Flash style": "Тип спалаху",
        "Gentle": "М'яко",
        "Standard": "Норма",
        "Sharp": "Різко",
        "Custom": "Своє",
        "Hold (s)": "Показ (с)",
        "Fade (s)": "Згасання (с)",
        "Pulses": "Повтори",
        "Gap between pulses": "Пауза між повторами",
        "Sound": "Звук",
        "Ding": "Дзень",
        "Chord": "Акорд",
        "Chime": "Дзвін",
        "Notify": "Сигнал",
        "Volume": "Гучність",
        "Test": "Проба",
        "Dot size": "Розмір крапки",
        "Word to show": "Яке слово",
        "Word size": "Розмір слова",
        "Position": "Розташування",
        "Centre": "По центру",
        "Top left": "Згори зліва",
        "Top right": "Згори справа",
        "Bottom left": "Знизу зліва",
        "Bottom right": "Знизу справа",
        "Edge margin": "Відступ від краю",
        "Show on every monitor": "Показувати на всіх екранах",
        "Done": "Готово",

        "Look into the distance": "Погляньте вдалечінь",

        # The ask cards, the tray's review item, and the break's countdown switch.
        "Like the app?": "Подобається застосунок?",
        "If this independent app works well for you, would you consider a small donation? Thank you!": "Якщо цей незалежний застосунок вам підходить, чи не розглянете невелику пожертву? Дякую!",
        "Finding it useful?": "Застосунок корисний?",
        "A short review helps others with tired eyes find it. Thank you!": "Короткий відгук допоможе іншим людям із втомленими очима його знайти. Дякую!",
        "Don’t ask again": "Більше не питати",
        "Rate this app": "Оцінити застосунок",
        "Show countdown": "Показувати зворотний відлік",

        # The welcome card, the taught reminder and the strength question.
        "Show me": "Показати",
        "Close…\nsqueeze…\nopen": "Заплющте…\nстисніть…\nрозплющте",
        "How it works": "Як це працює",
        "Too weak or intrusive?": "Надто слабко чи нав’язливо?",
        "You can change these:": "Можна змінити:",
        "How this app works?": "Як працює застосунок",
        "Too weak or too intrusive? Change strength, size, duration and sound in Settings.": "Надто слабко чи нав’язливо? Змініть силу, розмір, тривалість і звук у налаштуваннях.",
        "A cue appears periodically, to remind you to blink fully: close, squeeze gently, open.": "Сигнал з’являється регулярно й нагадує кліпати повністю: заплющте очі, м’яко стисніть повіки, розплющте.",
        "Size": "Розмір",
        "Duration": "Тривалість",
    },

    # Czech. Same plural problem as the Slavic languages above, same fix.
    "cs": {
        "Blink now": "Mrknout teď",
        "Resume reminders": "Obnovit připomínky",
        "Snooze 30 minutes": "Pozastavit na 30 minut",
        "Settings": "Nastavení",
        "Buy me a coffee": "Kup mi kávu",
        "Quit": "Ukončit",

        "Got it": "Rozumím",

        "%s is already running.\n\nLook for its icon in the system tray, "
        "next to the clock -- you may need to click the ^ arrow to see it. "
        "Right-click the icon for Settings.":
            "%s už běží.\n\nNajděte ikonu v oznamovací oblasti u hodin — "
            "možná bude potřeba kliknout na šipku ^. Kliknutím pravým "
            "tlačítkem na ikonu otevřete nastavení.",

        "A gentle nudge on every screen.":
            "Jemné připomenutí na každé obrazovce.",
        "Start with Windows": "Spouštět s Windows",
        "Startup: managed by Windows": "Po spuštění: spravuje Windows",
        "Startup: turned off in Task Manager":
            "Po spuštění: vypnuto ve Správci",
        "Preview blink": "Vyzkoušet mrknutí",
        "Preview break": "Vyzkoušet přestávku",
        "Cancel": "Zrušit",
        "Save": "Uložit",
        "Save the changes you made?": "Uložit změny?",

        "Blink": "Mrknutí",
        "Remind me every": "Připomínat každých",
        "seconds": "sekundy",
        "minutes": "minuty",

        "Break": "Přestávka",
        "Look at trees!": "Podívejte se na stromy!",
        "Remind me to look away": "Připomínat pohled do dálky",
        "min": "min",

        "A dot": "Tečka",
        "A word": "Slovo",
        "Dim screen": "Ztlumit",
        "Strength": "Síla",
        "Colour": "Barva",
        "Change...": "Změnit…",
        "Play a sound": "Přehrát zvuk",
        "  Advanced settings": "  Pokročilé nastavení",

        "Advanced settings - Blink": "Pokročilé nastavení — Mrknutí",
        "Blink timing and sound": "Mrknutí: čas a zvuk",
        "Blink look": "Vzhled mrknutí",
        "Advanced settings - Break": "Pokročilé nastavení — Přestávka",
        "Break timing and sound": "Přestávka: čas a zvuk",
        "Break look": "Vzhled přestávky",
        "Flash style": "Styl záblesku",
        "Gentle": "Jemné",
        "Standard": "Běžné",
        "Sharp": "Ostré",
        "Custom": "Vlastní",
        "Hold (s)": "Trvání (s)",
        "Fade (s)": "Prolnutí (s)",
        "Pulses": "Záblesky",
        "Gap between pulses": "Mezera mezi záblesky",
        "Sound": "Zvuk",
        "Ding": "Cink",
        "Chord": "Akord",
        "Chime": "Zvonek",
        "Notify": "Signál",
        "Volume": "Hlasitost",
        "Test": "Přehrát",
        "Dot size": "Velikost tečky",
        "Word to show": "Zobrazené slovo",
        "Word size": "Velikost slova",
        "Position": "Pozice",
        "Centre": "Uprostřed",
        "Top left": "Vlevo nahoře",
        "Top right": "Vpravo nahoře",
        "Bottom left": "Vlevo dole",
        "Bottom right": "Vpravo dole",
        "Edge margin": "Odstup od okraje",
        "Show on every monitor": "Zobrazit na všech obrazovkách",
        "Done": "Hotovo",

        "Look into the distance": "Podívejte se do dálky",

        # The ask cards, the tray's review item, and the break's countdown switch.
        "Like the app?": "Líbí se vám aplikace?",
        "If this independent app works well for you, would you consider a small donation? Thank you!": "Pokud vám tato nezávislá aplikace dobře slouží, zvážili byste malý příspěvek? Děkuji!",
        "Finding it useful?": "Je pro vás užitečná?",
        "A short review helps others with tired eyes find it. Thank you!": "Krátké hodnocení pomůže dalším lidem s unavenýma očima ji najít. Děkuji!",
        "Don’t ask again": "Už se neptat",
        "Rate this app": "Ohodnotit aplikaci",
        "Show countdown": "Zobrazit odpočet",

        # The welcome card, the taught reminder and the strength question.
        "Show me": "Ukázat",
        "Close…\nsqueeze…\nopen": "Zavřete…\nstiskněte…\notevřete",
        "How it works": "Jak to funguje",
        "Too weak or intrusive?": "Příliš slabé nebo rušivé?",
        "You can change these:": "Můžete změnit:",
        "How this app works?": "Jak aplikace funguje",
        "Too weak or too intrusive? Change strength, size, duration and sound in Settings.": "Příliš slabé nebo rušivé? Změňte sílu, velikost, trvání a zvuk v Nastavení.",
        "A cue appears periodically, to remind you to blink fully: close, squeeze gently, open.": "Signál se pravidelně objevuje a připomíná vám, abyste mrkali úplně: zavřete oči, jemně je stiskněte, otevřete.",
        "Size": "Velikost",
        "Duration": "Trvání",
    },

    # Romanian.
    "ro": {
        "Blink now": "Clipește acum",
        "Resume reminders": "Reia mementourile",
        "Snooze 30 minutes": "Amână 30 de minute",
        "Settings": "Setări",
        "Buy me a coffee": "Fă-mi cinste cu o cafea",
        "Quit": "Ieșire",

        "Got it": "Am înțeles",

        "%s is already running.\n\nLook for its icon in the system tray, "
        "next to the clock -- you may need to click the ^ arrow to see it. "
        "Right-click the icon for Settings.":
            "%s rulează deja.\n\nCaută pictograma în zona de notificare, "
            "lângă ceas — s-ar putea să fie nevoie de un clic pe săgeata ^. "
            "Clic dreapta pe pictogramă pentru setări.",

        "A gentle nudge on every screen.":
            "Un memento discret pe fiecare ecran.",
        "Start with Windows": "Pornește cu Windows",
        "Startup: managed by Windows": "Pornire: gestionată de Windows",
        "Startup: turned off in Task Manager":
            "Pornire: dezactivată în Manager",
        "Preview blink": "Testează clipirea",
        "Preview break": "Testează pauza",
        "Cancel": "Anulează",
        "Save": "Salvează",
        "Save the changes you made?": "Salvezi modificările?",

        "Blink": "Clipire",
        "Remind me every": "Amintește-mi la fiecare",
        "seconds": "secunde",
        "minutes": "minute",

        "Break": "Pauză",
        "Look at trees!": "Privește copacii!",
        "Remind me to look away": "Amintește-mi să privesc departe",
        "min": "min",

        "A dot": "Un punct",
        "A word": "Un cuvânt",
        "Dim screen": "Întunecă",
        "Strength": "Intensitate",
        "Colour": "Culoare",
        "Change...": "Schimbă…",
        "Play a sound": "Redă un sunet",
        "  Advanced settings": "  Setări avansate",

        "Advanced settings - Blink": "Setări avansate — Clipire",
        "Blink timing and sound": "Clipire: timp și sunet",
        "Blink look": "Aspectul clipirii",
        "Advanced settings - Break": "Setări avansate — Pauză",
        "Break timing and sound": "Pauză: timp și sunet",
        "Break look": "Aspectul pauzei",
        "Flash style": "Stilul licăririi",
        "Gentle": "Blând",
        "Standard": "Standard",
        "Sharp": "Clar",
        "Custom": "Propriu",
        "Hold (s)": "Durată (s)",
        "Fade (s)": "Estompare (s)",
        "Pulses": "Repetări",
        "Gap between pulses": "Pauză între repetări",
        "Sound": "Sunet",
        "Ding": "Ding",
        "Chord": "Acord",
        "Chime": "Clopoțel",
        "Notify": "Alertă",
        "Volume": "Volum",
        "Test": "Ascultă",
        "Dot size": "Mărimea punctului",
        "Word to show": "Cuvântul afișat",
        "Word size": "Mărimea textului",
        "Position": "Poziție",
        "Centre": "Centru",
        "Top left": "Sus stânga",
        "Top right": "Sus dreapta",
        "Bottom left": "Jos stânga",
        "Bottom right": "Jos dreapta",
        "Edge margin": "Distanța de margine",
        "Show on every monitor": "Afișează pe fiecare ecran",
        "Done": "Gata",

        "Look into the distance": "Privește în depărtare",

        # The ask cards, the tray's review item, and the break's countdown switch.
        "Like the app?": "Îți place aplicația?",
        "If this independent app works well for you, would you consider a small donation? Thank you!": "Dacă această aplicație independentă îți este de folos, te-ai gândi la o mică donație? Mulțumesc!",
        "Finding it useful?": "Îți este utilă?",
        "A short review helps others with tired eyes find it. Thank you!": "O recenzie scurtă îi ajută pe alții cu ochii obosiți să o găsească. Mulțumesc!",
        "Don’t ask again": "Nu mai întreba",
        "Rate this app": "Evaluează aplicația",
        "Show countdown": "Afișează numărătoarea inversă",

        # The welcome card, the taught reminder and the strength question.
        "Show me": "Arată-mi",
        "Close…\nsqueeze…\nopen": "Închide…\nstrânge…\ndeschide",
        "How it works": "Cum funcționează",
        "Too weak or intrusive?": "Prea slab sau deranjant?",
        "You can change these:": "Poți schimba:",
        "How this app works?": "Cum funcționează aplicația",
        "Too weak or too intrusive? Change strength, size, duration and sound in Settings.": "Prea slab sau deranjant? Schimbă intensitatea, mărimea, durata și sunetul în Setări.",
        "A cue appears periodically, to remind you to blink fully: close, squeeze gently, open.": "Un semnal apare periodic ca să-ți amintească să clipești complet: închide ochii, strânge-i ușor, deschide-i.",
        "Size": "Mărime",
        "Duration": "Durată",
    },

    # Hungarian.
    "hu": {
        "Blink now": "Pislogj most",
        "Resume reminders": "Emlékeztetők folytatása",
        "Snooze 30 minutes": "Szünet 30 percre",
        "Settings": "Beállítások",
        "Buy me a coffee": "Hívj meg egy kávéra",
        "Quit": "Kilépés",

        "Got it": "Értem",

        "%s is already running.\n\nLook for its icon in the system tray, "
        "next to the clock -- you may need to click the ^ arrow to see it. "
        "Right-click the icon for Settings.":
            "A(z) %s már fut.\n\nKeresd az ikonját az értesítési területen, "
            "az óra mellett — lehet, hogy a ^ nyílra kell kattintani. Jobb "
            "gombbal kattintva nyílnak a beállítások.",

        "A gentle nudge on every screen.":
            "Finom emlékeztető minden képernyőn.",
        "Start with Windows": "Indítás a Windowsszal",
        "Startup: managed by Windows": "Indítás: a Windows kezeli",
        "Startup: turned off in Task Manager":
            "Indítás: kikapcsolva a Kezelőben",
        "Preview blink": "Pislogás kipróbálása",
        "Preview break": "Szünet kipróbálása",
        "Cancel": "Mégse",
        "Save": "Mentés",
        "Save the changes you made?": "Mented a változtatásokat?",

        "Blink": "Pislogás",
        "Remind me every": "Emlékeztess minden",
        "seconds": "mp",
        "minutes": "perc",

        "Break": "Szünet",
        "Look at trees!": "Nézz a fákra!",
        "Remind me to look away": "Emlékeztess a távolba nézésre",
        "min": "perc",

        "A dot": "Pont",
        "A word": "Szó",
        "Dim screen": "Elsötétítés",
        "Strength": "Erősség",
        "Colour": "Szín",
        "Change...": "Módosítás…",
        "Play a sound": "Hang lejátszása",
        "  Advanced settings": "  Speciális beállítások",

        "Advanced settings - Blink": "Speciális beállítások — Pislogás",
        "Blink timing and sound": "Pislogás: idő és hang",
        "Blink look": "A pislogás megjelenése",
        "Advanced settings - Break": "Speciális beállítások — Szünet",
        "Break timing and sound": "Szünet: idő és hang",
        "Break look": "A szünet megjelenése",
        "Flash style": "Villanás stílusa",
        "Gentle": "Lágy",
        "Standard": "Normál",
        "Sharp": "Éles",
        "Custom": "Egyéni",
        "Hold (s)": "Tartás (mp)",
        "Fade (s)": "Áttűnés (mp)",
        "Pulses": "Ismétlés",
        "Gap between pulses": "Szünet az ismétlések közt",
        "Sound": "Hang",
        "Ding": "Csing",
        "Chord": "Akkord",
        "Chime": "Harang",
        "Notify": "Jelzés",
        "Volume": "Hangerő",
        "Test": "Teszt",
        "Dot size": "Pont mérete",
        "Word to show": "Megjelenő szó",
        "Word size": "Szó mérete",
        "Position": "Pozíció",
        "Centre": "Középen",
        "Top left": "Bal felül",
        "Top right": "Jobb felül",
        "Bottom left": "Bal alul",
        "Bottom right": "Jobb alul",
        "Edge margin": "Távolság a széltől",
        "Show on every monitor": "Minden képernyőn",
        "Done": "Kész",

        "Look into the distance": "Nézz a távolba",

        # The ask cards, the tray's review item, and the break's countdown switch.
        "Like the app?": "Tetszik az alkalmazás?",
        "If this independent app works well for you, would you consider a small donation? Thank you!": "Ha ez a független alkalmazás beválik neked, megfontolnál egy kis adományt? Köszönöm!",
        "Finding it useful?": "Hasznosnak találod?",
        "A short review helps others with tired eyes find it. Thank you!": "Egy rövid értékelés segít más fáradt szemű embereknek megtalálni. Köszönöm!",
        "Don’t ask again": "Ne kérdezd többé",
        "Rate this app": "Értékeld az alkalmazást",
        "Show countdown": "Visszaszámlálás megjelenítése",

        # The welcome card, the taught reminder and the strength question.
        "Show me": "Mutasd",
        "Close…\nsqueeze…\nopen": "Csukd be…\nszorítsd…\nnyisd ki",
        "How it works": "Hogyan működik",
        "Too weak or intrusive?": "Túl gyenge vagy zavaró?",
        "You can change these:": "Ezeket módosíthatod:",
        "How this app works?": "Hogyan működik az app?",
        "Too weak or too intrusive? Change strength, size, duration and sound in Settings.": "Túl gyenge vagy zavaró? Az erősséget, a méretet, az időtartamot és a hangot a Beállításokban módosíthatod.",
        "A cue appears periodically, to remind you to blink fully: close, squeeze gently, open.": "Időnként megjelenik egy jelzés, hogy emlékeztessen a teljes pislogásra: csukd be a szemed, szorítsd össze finoman, nyisd ki.",
        "Size": "Méret",
        "Duration": "Időtartam",
    },

    # Greek.
    "el": {
        "Blink now": "Ανοιγοκλείσε τώρα",
        "Resume reminders": "Συνέχιση υπενθυμίσεων",
        "Snooze 30 minutes": "Παύση 30 λεπτών",
        "Settings": "Ρυθμίσεις",
        "Buy me a coffee": "Κέρασέ με έναν καφέ",
        "Quit": "Έξοδος",

        "Got it": "Εντάξει",

        "%s is already running.\n\nLook for its icon in the system tray, "
        "next to the clock -- you may need to click the ^ arrow to see it. "
        "Right-click the icon for Settings.":
            "Το %s εκτελείται ήδη.\n\nΨάξε το εικονίδιό του στην περιοχή "
            "ειδοποιήσεων, δίπλα στο ρολόι — ίσως χρειαστεί να πατήσεις το "
            "βέλος ^. Δεξί κλικ στο εικονίδιο για τις ρυθμίσεις.",

        "A gentle nudge on every screen.":
            "Μια διακριτική υπενθύμιση σε κάθε οθόνη.",
        "Start with Windows": "Εκκίνηση με τα Windows",
        "Startup: managed by Windows": "Εκκίνηση: τη διαχειρίζονται τα Windows",
        "Startup: turned off in Task Manager":
            "Εκκίνηση: ανενεργή στη Διαχείριση",
        "Preview blink": "Δοκιμή ματιού",
        "Preview break": "Δοκιμή παύσης",
        "Cancel": "Άκυρο",
        "Save": "Αποθήκευση",
        "Save the changes you made?": "Αποθήκευση αλλαγών;",

        "Blink": "Βλεφάρισμα",
        "Remind me every": "Υπενθύμιση κάθε",
        "seconds": "δευτ.",
        "minutes": "λεπτά",

        "Break": "Παύση",
        "Look at trees!": "Κοίτα τα δέντρα!",
        "Remind me to look away": "Υπενθύμιση να κοιτάω μακριά",
        "min": "λ",

        "A dot": "Κουκκίδα",
        "A word": "Λέξη",
        "Dim screen": "Σκούρο",
        "Strength": "Ένταση",
        "Colour": "Χρώμα",
        "Change...": "Αλλαγή…",
        "Play a sound": "Αναπαραγωγή ήχου",
        "  Advanced settings": "  Σύνθετες ρυθμίσεις",

        "Advanced settings - Blink": "Σύνθετες ρυθμίσεις — Βλεφάρισμα",
        "Blink timing and sound": "Βλεφάρισμα: χρόνος και ήχος",
        "Blink look": "Εμφάνιση βλεφαρίσματος",
        "Advanced settings - Break": "Σύνθετες ρυθμίσεις — Παύση",
        "Break timing and sound": "Παύση: χρόνος και ήχος",
        "Break look": "Εμφάνιση παύσης",
        "Flash style": "Τύπος αναλαμπής",
        "Gentle": "Ήπιο",
        "Standard": "Κανονικό",
        "Sharp": "Έντονο",
        "Custom": "Δικό μου",
        "Hold (s)": "Διάρκεια (δ)",
        "Fade (s)": "Σβήσιμο (δ)",
        "Pulses": "Φορές",
        "Gap between pulses": "Κενό μεταξύ τους",
        "Sound": "Ήχος",
        "Ding": "Ντινγκ",
        "Chord": "Ακόρντο",
        "Chime": "Καμπάνα",
        "Notify": "Σήμα",
        "Volume": "Ένταση ήχου",
        "Test": "Δοκιμή",
        "Dot size": "Μέγεθος κουκκίδας",
        "Word to show": "Λέξη προς εμφάνιση",
        "Word size": "Μέγεθος λέξης",
        "Position": "Θέση",
        "Centre": "Κέντρο",
        "Top left": "Πάνω αριστερά",
        "Top right": "Πάνω δεξιά",
        "Bottom left": "Κάτω αριστερά",
        "Bottom right": "Κάτω δεξιά",
        "Edge margin": "Απόσταση από άκρη",
        "Show on every monitor": "Σε κάθε οθόνη",
        "Done": "Τέλος",

        "Look into the distance": "Κοίτα μακριά",

        # The ask cards, the tray's review item, and the break's countdown switch.
        "Like the app?": "Σου αρέσει η εφαρμογή;",
        "If this independent app works well for you, would you consider a small donation? Thank you!": "Αν αυτή η ανεξάρτητη εφαρμογή σού κάνει, θα σκεφτόσουν μια μικρή δωρεά; Ευχαριστώ!",
        "Finding it useful?": "Σου φαίνεται χρήσιμη;",
        "A short review helps others with tired eyes find it. Thank you!": "Μια σύντομη κριτική βοηθά άλλους με κουρασμένα μάτια να τη βρουν. Ευχαριστώ!",
        "Don’t ask again": "Να μην ξαναρωτηθώ",
        "Rate this app": "Βαθμολόγησε την εφαρμογή",
        "Show countdown": "Αντίστροφη μέτρηση",

        # The welcome card, the taught reminder and the strength question.
        "Show me": "Δείξε μου",
        "Close…\nsqueeze…\nopen": "Κλείσε…\nσφίξε…\nάνοιξε",
        "How it works": "Πώς λειτουργεί",
        "Too weak or intrusive?": "Πολύ αδύναμο ή ενοχλητικό;",
        "You can change these:": "Μπορείς να αλλάξεις:",
        "How this app works?": "Πώς λειτουργεί η εφαρμογή",
        "Too weak or too intrusive? Change strength, size, duration and sound in Settings.": "Πολύ αδύναμο ή ενοχλητικό; Άλλαξε ένταση, μέγεθος, διάρκεια και ήχο στις Ρυθμίσεις.",
        "A cue appears periodically, to remind you to blink fully: close, squeeze gently, open.": "Ένα σήμα εμφανίζεται περιοδικά για να σου θυμίζει να ανοιγοκλείνεις πλήρως τα μάτια: κλείσε, σφίξε απαλά, άνοιξε.",
        "Size": "Μέγεθος",
        "Duration": "Διάρκεια",
    },

    # Swedish.
    "sv": {
        "Blink now": "Blinka nu",
        "Resume reminders": "Återuppta påminnelser",
        "Snooze 30 minutes": "Pausa i 30 minuter",
        "Settings": "Inställningar",
        "Buy me a coffee": "Bjud på en kaffe",
        "Quit": "Avsluta",

        "Got it": "Uppfattat",

        "%s is already running.\n\nLook for its icon in the system tray, "
        "next to the clock -- you may need to click the ^ arrow to see it. "
        "Right-click the icon for Settings.":
            "%s körs redan.\n\nLeta efter ikonen i meddelandefältet, bredvid "
            "klockan — du kan behöva klicka på pilen ^ för att se den. "
            "Högerklicka på ikonen för inställningar.",

        "A gentle nudge on every screen.":
            "En mjuk påminnelse på varje skärm.",
        "Start with Windows": "Starta med Windows",
        "Startup: managed by Windows": "Uppstart: hanteras av Windows",
        "Startup: turned off in Task Manager":
            "Uppstart: avstängd i Aktivitetshanteraren",
        "Preview blink": "Testa blinkning",
        "Preview break": "Testa paus",
        "Cancel": "Avbryt",
        "Save": "Spara",
        "Save the changes you made?": "Spara ändringarna?",

        "Blink": "Blinkning",
        "Remind me every": "Påminn mig var",
        "seconds": "sekunder",
        "minutes": "minuter",

        "Break": "Paus",
        "Look at trees!": "Titta på träden!",
        "Remind me to look away": "Påminn om att titta bort",
        "min": "min",

        "A dot": "En prick",
        "A word": "Ett ord",
        "Dim screen": "Dämpa",
        "Strength": "Styrka",
        "Colour": "Färg",
        "Change...": "Ändra…",
        "Play a sound": "Spela ett ljud",
        "  Advanced settings": "  Avancerade inställningar",

        "Advanced settings - Blink": "Avancerade inställningar — Blinkning",
        "Blink timing and sound": "Blinkning: tid och ljud",
        "Blink look": "Blinkningens utseende",
        "Advanced settings - Break": "Avancerade inställningar — Paus",
        "Break timing and sound": "Paus: tid och ljud",
        "Break look": "Pausens utseende",
        "Flash style": "Blinkstil",
        "Gentle": "Mjuk",
        "Standard": "Normal",
        "Sharp": "Skarp",
        "Custom": "Egen",
        "Hold (s)": "Håll (s)",
        "Fade (s)": "Toning (s)",
        "Pulses": "Antal",
        "Gap between pulses": "Mellanrum mellan pulser",
        "Sound": "Ljud",
        "Ding": "Pling",
        "Chord": "Ackord",
        "Chime": "Klocka",
        "Notify": "Signal",
        "Volume": "Volym",
        "Test": "Testa",
        "Dot size": "Prickens storlek",
        "Word to show": "Ord att visa",
        "Word size": "Ordets storlek",
        "Position": "Position",
        "Centre": "Mitten",
        "Top left": "Uppe till vänster",
        "Top right": "Uppe till höger",
        "Bottom left": "Nere till vänster",
        "Bottom right": "Nere till höger",
        "Edge margin": "Avstånd från kanten",
        "Show on every monitor": "Visa på alla skärmar",
        "Done": "Klar",

        "Look into the distance": "Titta långt bort",

        # The ask cards, the tray's review item, and the break's countdown switch.
        "Like the app?": "Gillar du appen?",
        "If this independent app works well for you, would you consider a small donation? Thank you!": "Om den här oberoende appen fungerar bra för dig, kan du tänka dig att skänka en liten gåva? Tack!",
        "Finding it useful?": "Har du nytta av den?",
        "A short review helps others with tired eyes find it. Thank you!": "En kort recension hjälper andra med trötta ögon att hitta den. Tack!",
        "Don’t ask again": "Fråga inte igen",
        "Rate this app": "Betygsätt appen",
        "Show countdown": "Visa nedräkning",

        # The welcome card, the taught reminder and the strength question.
        "Show me": "Visa mig",
        "Close…\nsqueeze…\nopen": "Blunda…\nkläm…\nöppna",
        "How it works": "Så fungerar det",
        "Too weak or intrusive?": "För svag eller störande?",
        "You can change these:": "Du kan ändra:",
        "How this app works?": "Så fungerar appen",
        "Too weak or too intrusive? Change strength, size, duration and sound in Settings.": "För svag eller störande? Ändra styrka, storlek, varaktighet och ljud i Inställningar.",
        "A cue appears periodically, to remind you to blink fully: close, squeeze gently, open.": "En signal visas regelbundet för att påminna dig om att blinka ordentligt: blunda, kläm ihop lätt, öppna.",
        "Size": "Storlek",
        "Duration": "Varaktighet",
    },

    # Finnish.
    "fi": {
        "Blink now": "Räpäytä nyt",
        "Resume reminders": "Jatka muistutuksia",
        "Snooze 30 minutes": "Tauko 30 minuutiksi",
        "Settings": "Asetukset",
        "Buy me a coffee": "Tarjoa kahvit",
        "Quit": "Lopeta",

        "Got it": "Selvä",

        "%s is already running.\n\nLook for its icon in the system tray, "
        "next to the clock -- you may need to click the ^ arrow to see it. "
        "Right-click the icon for Settings.":
            "%s on jo käynnissä.\n\nEtsi sen kuvake ilmoitusalueelta kellon "
            "vierestä — sinun voi olla tarpeen napsauttaa nuolta ^. Avaa "
            "asetukset napsauttamalla kuvaketta hiiren oikealla.",

        "A gentle nudge on every screen.":
            "Hillitty muistutus jokaisella näytöllä.",
        "Start with Windows": "Käynnisty Windowsin mukana",
        "Startup: managed by Windows": "Käynnistys: Windowsin hallinnassa",
        "Startup: turned off in Task Manager":
            "Käynnistys: pois Tehtävienhallinnassa",
        "Preview blink": "Kokeile räpäytystä",
        "Preview break": "Kokeile taukoa",
        "Cancel": "Peruuta",
        "Save": "Tallenna",
        "Save the changes you made?": "Tallennetaanko muutokset?",

        "Blink": "Räpäytys",
        "Remind me every": "Muistuta joka",
        "seconds": "sekuntia",
        "minutes": "minuuttia",

        "Break": "Tauko",
        "Look at trees!": "Katso puita!",
        "Remind me to look away": "Muistuta katsomaan kauas",
        "min": "min",

        "A dot": "Piste",
        "A word": "Sana",
        "Dim screen": "Himmennä",
        "Strength": "Voima",
        "Colour": "Väri",
        "Change...": "Vaihda…",
        "Play a sound": "Toista ääni",
        "  Advanced settings": "  Lisäasetukset",

        "Advanced settings - Blink": "Lisäasetukset — Räpäytys",
        "Blink timing and sound": "Räpäytys: aika ja ääni",
        "Blink look": "Räpäytyksen ulkoasu",
        "Advanced settings - Break": "Lisäasetukset — Tauko",
        "Break timing and sound": "Tauko: aika ja ääni",
        "Break look": "Tauon ulkoasu",
        "Flash style": "Välähdystyyli",
        "Gentle": "Pehmeä",
        "Standard": "Tavallinen",
        "Sharp": "Terävä",
        "Custom": "Oma",
        "Hold (s)": "Kesto (s)",
        "Fade (s)": "Häivytys (s)",
        "Pulses": "Kerrat",
        "Gap between pulses": "Väli kertojen välillä",
        "Sound": "Ääni",
        "Ding": "Kilaus",
        "Chord": "Sointu",
        "Chime": "Kello",
        "Notify": "Merkki",
        "Volume": "Äänenvoimakkuus",
        "Test": "Kokeile",
        "Dot size": "Pisteen koko",
        "Word to show": "Näytettävä sana",
        "Word size": "Sanan koko",
        "Position": "Sijainti",
        "Centre": "Keskellä",
        "Top left": "Ylhäällä vasemmalla",
        "Top right": "Ylhäällä oikealla",
        "Bottom left": "Alhaalla vasemmalla",
        "Bottom right": "Alhaalla oikealla",
        "Edge margin": "Etäisyys reunasta",
        "Show on every monitor": "Näytä kaikilla näytöillä",
        "Done": "Valmis",

        "Look into the distance": "Katso kauas",

        # The ask cards, the tray's review item, and the break's countdown switch.
        "Like the app?": "Pidätkö sovelluksesta?",
        "If this independent app works well for you, would you consider a small donation? Thank you!": "Jos tämä itsenäinen sovellus toimii sinulle hyvin, harkitsisitko pientä lahjoitusta? Kiitos!",
        "Finding it useful?": "Onko siitä hyötyä?",
        "A short review helps others with tired eyes find it. Thank you!": "Lyhyt arvio auttaa muita väsyneistä silmistä kärsiviä löytämään sen. Kiitos!",
        "Don’t ask again": "Älä kysy uudelleen",
        "Rate this app": "Arvioi sovellus",
        "Show countdown": "Näytä lähtölaskenta",

        # The welcome card, the taught reminder and the strength question.
        "Show me": "Näytä",
        "Close…\nsqueeze…\nopen": "Sulje…\npurista…\navaa",
        "How it works": "Näin se toimii",
        "Too weak or intrusive?": "Liian heikko tai häiritsevä?",
        "You can change these:": "Voit muuttaa näitä:",
        "How this app works?": "Näin sovellus toimii",
        "Too weak or too intrusive? Change strength, size, duration and sound in Settings.": "Liian heikko tai häiritsevä? Muuta voimaa, kokoa, kestoa ja ääntä asetuksista.",
        "A cue appears periodically, to remind you to blink fully: close, squeeze gently, open.": "Merkki näkyy säännöllisesti muistuttamassa räpäyttämään kunnolla: sulje, purista kevyesti, avaa.",
        "Size": "Koko",
        "Duration": "Kesto",
    },

    # Danish.
    "da": {
        "Blink now": "Blink nu",
        "Resume reminders": "Genoptag påmindelser",
        "Snooze 30 minutes": "Pause i 30 minutter",
        "Settings": "Indstillinger",
        "Buy me a coffee": "Giv mig en kaffe",
        "Quit": "Afslut",

        "Got it": "Forstået",

        "%s is already running.\n\nLook for its icon in the system tray, "
        "next to the clock -- you may need to click the ^ arrow to see it. "
        "Right-click the icon for Settings.":
            "%s kører allerede.\n\nLed efter ikonet i meddelelsesområdet ved "
            "uret — du skal måske klikke på pilen ^ for at se det. Højreklik "
            "på ikonet for indstillinger.",

        "A gentle nudge on every screen.":
            "En blid påmindelse på hver skærm.",
        "Start with Windows": "Start med Windows",
        "Startup: managed by Windows": "Opstart: styres af Windows",
        "Startup: turned off in Task Manager":
            "Opstart: slået fra i Jobliste",
        "Preview blink": "Prøv blink",
        "Preview break": "Prøv pause",
        "Cancel": "Annuller",
        "Save": "Gem",
        "Save the changes you made?": "Gem ændringerne?",

        "Blink": "Blink",
        "Remind me every": "Mind mig hvert",
        "seconds": "sekunder",
        "minutes": "minutter",

        "Break": "Pause",
        "Look at trees!": "Kig på træerne!",
        "Remind me to look away": "Mind mig om at kigge væk",
        "min": "min",

        "A dot": "En prik",
        "A word": "Et ord",
        "Dim screen": "Dæmp",
        "Strength": "Styrke",
        "Colour": "Farve",
        "Change...": "Skift…",
        "Play a sound": "Afspil en lyd",
        "  Advanced settings": "  Avancerede indstillinger",

        "Advanced settings - Blink": "Avancerede indstillinger — Blink",
        "Blink timing and sound": "Blink: tid og lyd",
        "Blink look": "Blinkets udseende",
        "Advanced settings - Break": "Avancerede indstillinger — Pause",
        "Break timing and sound": "Pause: tid og lyd",
        "Break look": "Pausens udseende",
        "Flash style": "Blinkstil",
        "Gentle": "Blid",
        "Standard": "Normal",
        "Sharp": "Skarp",
        "Custom": "Egen",
        "Hold (s)": "Hold (s)",
        "Fade (s)": "Toning (s)",
        "Pulses": "Antal",
        "Gap between pulses": "Mellemrum mellem pulser",
        "Sound": "Lyd",
        "Ding": "Pling",
        "Chord": "Akkord",
        "Chime": "Klokke",
        "Notify": "Signal",
        "Volume": "Lydstyrke",
        "Test": "Lyt",
        "Dot size": "Prikkens størrelse",
        "Word to show": "Ord der vises",
        "Word size": "Ordets størrelse",
        "Position": "Placering",
        "Centre": "Midten",
        "Top left": "Øverst til venstre",
        "Top right": "Øverst til højre",
        "Bottom left": "Nederst til venstre",
        "Bottom right": "Nederst til højre",
        "Edge margin": "Afstand fra kanten",
        "Show on every monitor": "Vis på alle skærme",
        "Done": "Færdig",

        "Look into the distance": "Kig langt væk",

        # The ask cards, the tray's review item, and the break's countdown switch.
        "Like the app?": "Kan du lide appen?",
        "If this independent app works well for you, would you consider a small donation? Thank you!": "Hvis denne uafhængige app fungerer godt for dig, vil du så overveje en lille donation? Tak!",
        "Finding it useful?": "Har du gavn af den?",
        "A short review helps others with tired eyes find it. Thank you!": "En kort anmeldelse hjælper andre med trætte øjne med at finde den. Tak!",
        "Don’t ask again": "Spørg ikke igen",
        "Rate this app": "Bedøm appen",
        "Show countdown": "Vis nedtælling",

        # The welcome card, the taught reminder and the strength question.
        "Show me": "Vis mig",
        "Close…\nsqueeze…\nopen": "Luk…\nklem…\nåbn",
        "How it works": "Sådan virker det",
        "Too weak or intrusive?": "For svagt eller forstyrrende?",
        "You can change these:": "Du kan ændre:",
        "How this app works?": "Sådan virker appen",
        "Too weak or too intrusive? Change strength, size, duration and sound in Settings.": "For svagt eller forstyrrende? Skift styrke, størrelse, varighed og lyd i Indstillinger.",
        "A cue appears periodically, to remind you to blink fully: close, squeeze gently, open.": "Et signal vises med jævne mellemrum for at minde dig om at blinke helt: luk øjnene, klem blidt, åbn.",
        "Size": "Størrelse",
        "Duration": "Varighed",
    },

    # Norwegian, Bokmal.
    "nb": {
        "Blink now": "Blunk nå",
        "Resume reminders": "Fortsett påminnelser",
        "Snooze 30 minutes": "Pause i 30 minutter",
        "Settings": "Innstillinger",
        "Buy me a coffee": "Spander en kaffe",
        "Quit": "Avslutt",

        "Got it": "Skjønner",

        "%s is already running.\n\nLook for its icon in the system tray, "
        "next to the clock -- you may need to click the ^ arrow to see it. "
        "Right-click the icon for Settings.":
            "%s kjører allerede.\n\nSe etter ikonet i varslingsområdet ved "
            "klokken — du må kanskje klikke på pilen ^ for å se det. "
            "Høyreklikk ikonet for innstillinger.",

        "A gentle nudge on every screen.":
            "En mild påminnelse på hver skjerm.",
        "Start with Windows": "Start med Windows",
        "Startup: managed by Windows": "Oppstart: styres av Windows",
        "Startup: turned off in Task Manager":
            "Oppstart: slått av i Oppgavebehandling",
        "Preview blink": "Prøv blunk",
        "Preview break": "Prøv pause",
        "Cancel": "Avbryt",
        "Save": "Lagre",
        "Save the changes you made?": "Lagre endringene?",

        "Blink": "Blunk",
        "Remind me every": "Minn meg hvert",
        "seconds": "sekunder",
        "minutes": "minutter",

        "Break": "Pause",
        "Look at trees!": "Se på trærne!",
        "Remind me to look away": "Minn meg om å se bort",
        "min": "min",

        "A dot": "En prikk",
        "A word": "Et ord",
        "Dim screen": "Demp",
        "Strength": "Styrke",
        "Colour": "Farge",
        "Change...": "Endre…",
        "Play a sound": "Spill en lyd",
        "  Advanced settings": "  Avanserte innstillinger",

        "Advanced settings - Blink": "Avanserte innstillinger — Blunk",
        "Blink timing and sound": "Blunk: tid og lyd",
        "Blink look": "Blunkets utseende",
        "Advanced settings - Break": "Avanserte innstillinger — Pause",
        "Break timing and sound": "Pause: tid og lyd",
        "Break look": "Pausens utseende",
        "Flash style": "Blinkstil",
        "Gentle": "Mild",
        "Standard": "Vanlig",
        "Sharp": "Skarp",
        "Custom": "Egen",
        "Hold (s)": "Hold (s)",
        "Fade (s)": "Toning (s)",
        "Pulses": "Antall",
        "Gap between pulses": "Opphold mellom pulser",
        "Sound": "Lyd",
        "Ding": "Pling",
        "Chord": "Akkord",
        "Chime": "Klokke",
        "Notify": "Signal",
        "Volume": "Volum",
        "Test": "Hør",
        "Dot size": "Prikkens størrelse",
        "Word to show": "Ord som vises",
        "Word size": "Ordets størrelse",
        "Position": "Plassering",
        "Centre": "Midten",
        "Top left": "Øverst til venstre",
        "Top right": "Øverst til høyre",
        "Bottom left": "Nederst til venstre",
        "Bottom right": "Nederst til høyre",
        "Edge margin": "Avstand fra kanten",
        "Show on every monitor": "Vis på alle skjermer",
        "Done": "Ferdig",

        "Look into the distance": "Se langt bort",

        # The ask cards, the tray's review item, and the break's countdown switch.
        "Like the app?": "Liker du appen?",
        "If this independent app works well for you, would you consider a small donation? Thank you!": "Hvis denne uavhengige appen fungerer bra for deg, kan du tenke deg å gi en liten donasjon? Takk!",
        "Finding it useful?": "Har du nytte av den?",
        "A short review helps others with tired eyes find it. Thank you!": "En kort anmeldelse hjelper andre med slitne øyne å finne den. Takk!",
        "Don’t ask again": "Ikke spør igjen",
        "Rate this app": "Vurder appen",
        "Show countdown": "Vis nedtelling",

        # The welcome card, the taught reminder and the strength question.
        "Show me": "Vis meg",
        "Close…\nsqueeze…\nopen": "Lukk…\nklem…\nåpne",
        "How it works": "Slik fungerer det",
        "Too weak or intrusive?": "For svakt eller forstyrrende?",
        "You can change these:": "Du kan endre:",
        "How this app works?": "Slik fungerer appen",
        "Too weak or too intrusive? Change strength, size, duration and sound in Settings.": "For svakt eller forstyrrende? Endre styrke, størrelse, varighet og lyd i Innstillinger.",
        "A cue appears periodically, to remind you to blink fully: close, squeeze gently, open.": "Et signal vises med jevne mellomrom for å minne deg på å blunke helt: lukk øynene, klem forsiktig, åpne.",
        "Size": "Størrelse",
        "Duration": "Varighet",
    },

    # Dutch.
    "nl": {
        "Blink now": "Knipper nu",
        "Resume reminders": "Herinneringen hervatten",
        "Snooze 30 minutes": "30 minuten pauzeren",
        "Settings": "Instellingen",
        "Buy me a coffee": "Trakteer op een koffie",
        "Quit": "Afsluiten",

        "Got it": "Begrepen",

        "%s is already running.\n\nLook for its icon in the system tray, "
        "next to the clock -- you may need to click the ^ arrow to see it. "
        "Right-click the icon for Settings.":
            "%s draait al.\n\nZoek het pictogram in het systeemvak, naast de "
            "klok — misschien moet je op de pijl ^ klikken om het te zien. "
            "Klik met rechts op het pictogram voor instellingen.",

        "A gentle nudge on every screen.":
            "Een rustige herinnering op elk scherm.",
        "Start with Windows": "Starten met Windows",
        "Startup: managed by Windows": "Opstarten: beheerd door Windows",
        "Startup: turned off in Task Manager":
            "Opstarten: uit in Taakbeheer",
        "Preview blink": "Knipperen testen",
        "Preview break": "Pauze testen",
        "Cancel": "Annuleren",
        "Save": "Opslaan",
        "Save the changes you made?": "Wijzigingen opslaan?",

        "Blink": "Knipperen",
        "Remind me every": "Herinner me elke",
        "seconds": "seconden",
        "minutes": "minuten",

        "Break": "Pauze",
        "Look at trees!": "Kijk naar de bomen!",
        "Remind me to look away": "Herinner me weg te kijken",
        "min": "min",

        "A dot": "Een stip",
        "A word": "Een woord",
        "Dim screen": "Dimmen",
        "Strength": "Sterkte",
        "Colour": "Kleur",
        "Change...": "Wijzigen…",
        "Play a sound": "Geluid afspelen",
        "  Advanced settings": "  Geavanceerde instellingen",

        "Advanced settings - Blink": "Geavanceerde instellingen — Knipperen",
        "Blink timing and sound": "Knipperen: tijd en geluid",
        "Blink look": "Uiterlijk van het knipperen",
        "Advanced settings - Break": "Geavanceerde instellingen — Pauze",
        "Break timing and sound": "Pauze: tijd en geluid",
        "Break look": "Uiterlijk van de pauze",
        "Flash style": "Flitsstijl",
        "Gentle": "Zacht",
        "Standard": "Normaal",
        "Sharp": "Scherp",
        "Custom": "Eigen",
        "Hold (s)": "Duur (s)",
        "Fade (s)": "Vervaging (s)",
        "Pulses": "Aantal",
        "Gap between pulses": "Tussenpoos",
        "Sound": "Geluid",
        "Ding": "Ping",
        "Chord": "Akkoord",
        "Chime": "Bel",
        "Notify": "Signaal",
        "Volume": "Volume",
        "Test": "Test",
        "Dot size": "Grootte van de stip",
        "Word to show": "Te tonen woord",
        "Word size": "Woordgrootte",
        "Position": "Positie",
        "Centre": "Midden",
        "Top left": "Linksboven",
        "Top right": "Rechtsboven",
        "Bottom left": "Linksonder",
        "Bottom right": "Rechtsonder",
        "Edge margin": "Afstand tot de rand",
        "Show on every monitor": "Op elk scherm tonen",
        "Done": "Klaar",

        "Look into the distance": "Kijk in de verte",

        # The ask cards, the tray's review item, and the break's countdown switch.
        "Like the app?": "Bevalt de app?",
        "If this independent app works well for you, would you consider a small donation? Thank you!": "Als deze onafhankelijke app goed voor je werkt, zou je dan een kleine donatie willen overwegen? Bedankt!",
        "Finding it useful?": "Heb je er iets aan?",
        "A short review helps others with tired eyes find it. Thank you!": "Een korte review helpt anderen met vermoeide ogen hem te vinden. Bedankt!",
        "Don’t ask again": "Niet meer vragen",
        "Rate this app": "Beoordeel deze app",
        "Show countdown": "Aftellen tonen",

        # The welcome card, the taught reminder and the strength question.
        "Show me": "Laat zien",
        "Close…\nsqueeze…\nopen": "Ogen dicht…\nknijpen…\nopen",
        "How it works": "Zo werkt het",
        "Too weak or intrusive?": "Te zwak of storend?",
        "You can change these:": "Je kunt dit wijzigen:",
        "How this app works?": "Zo werkt de app",
        "Too weak or too intrusive? Change strength, size, duration and sound in Settings.": "Te zwak of storend? Wijzig sterkte, grootte, duur en geluid bij Instellingen.",
        "A cue appears periodically, to remind you to blink fully: close, squeeze gently, open.": "Er verschijnt regelmatig een signaal om je eraan te herinneren volledig te knipperen: ogen dicht, zacht knijpen, open.",
        "Size": "Grootte",
        "Duration": "Duur",
    },
}
