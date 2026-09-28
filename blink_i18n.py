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

        "every second": "每秒",
        "every %d seconds": "每 %d 秒",
        "every minute": "每分钟",
        "every %d minutes": "每 %d 分钟",

        "%s is running": "%s 正在运行",
        "It stays in the background and will nudge you to blink\n%s.":
            "它会在后台运行，%s提醒你眨眼。",
        "Right-click the tray icon, by the clock, for settings.":
            "在时钟旁的图标上点右键即可打开设置。",
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

        "every second": "chaque seconde",
        "every %d seconds": "toutes les %d secondes",
        "every minute": "chaque minute",
        "every %d minutes": "toutes les %d minutes",

        # Not "est en cours d'exécution": with the product name in front of
        # it that is 464 pixels in a 440-pixel window.
        "%s is running": "%s fonctionne",
        "It stays in the background and will nudge you to blink\n%s.":
            "Il reste en arrière-plan et vous rappellera de cligner "
            "des yeux\n%s.",
        "Right-click the tray icon, by the clock, for settings.":
            "Clic droit sur l'icône près de l'horloge pour les paramètres.",
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

        "every second": "cada segundo",
        "every %d seconds": "cada %d segundos",
        "every minute": "cada minuto",
        "every %d minutes": "cada %d minutos",

        "%s is running": "%s está en ejecución",
        "It stays in the background and will nudge you to blink\n%s.":
            "Se queda en segundo plano y te recordará parpadear\n%s.",
        "Right-click the tray icon, by the clock, for settings.":
            "Clic derecho en el icono junto al reloj para la configuración.",
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

        "every second": "jede Sekunde",
        "every %d seconds": "alle %d Sekunden",
        "every minute": "jede Minute",
        "every %d minutes": "alle %d Minuten",

        "%s is running": "%s läuft",
        "It stays in the background and will nudge you to blink\n%s.":
            "Läuft im Hintergrund und erinnert Sie\n%s ans Blinzeln.",
        # "öffnet die Einstellungen" would be 440 pixels in a 408-pixel card.
        "Right-click the tray icon, by the clock, for settings.":
            "Rechtsklick auf das Symbol neben der Uhr für Einstellungen.",
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

        "every second": "ogni secondo",
        "every %d seconds": "ogni %d secondi",
        "every minute": "ogni minuto",
        "every %d minutes": "ogni %d minuti",

        "%s is running": "%s è in esecuzione",
        "It stays in the background and will nudge you to blink\n%s.":
            "Resta in background e ti ricorderà di battere le palpebre\n%s.",
        "Right-click the tray icon, by the clock, for settings.":
            "Clic destro sull'icona vicino all'orologio per le impostazioni.",
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

        "every second": "a cada segundo",
        "every %d seconds": "a cada %d segundos",
        "every minute": "a cada minuto",
        "every %d minutes": "a cada %d minutos",

        "%s is running": "%s está em execução",
        "It stays in the background and will nudge you to blink\n%s.":
            "Fica em segundo plano e vai lembrar você de piscar\n%s.",
        "Right-click the tray icon, by the clock, for settings.":
            "Clique com o botão direito no ícone ao lado do relógio.",
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

        "every second": "毎秒",
        "every %d seconds": "%d 秒ごとに",
        "every minute": "毎分",
        "every %d minutes": "%d 分ごとに",

        "%s is running": "%s は実行中です",
        "It stays in the background and will nudge you to blink\n%s.":
            "バックグラウンドで動き、%sまばたきをお知らせします。",
        "Right-click the tray icon, by the clock, for settings.":
            "時計の横のアイコンを右クリックすると設定が開きます。",
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

        "every second": "매초",
        "every %d seconds": "%d초마다",
        "every minute": "매분",
        "every %d minutes": "%d분마다",

        "%s is running": "%s 실행 중",
        "It stays in the background and will nudge you to blink\n%s.":
            "백그라운드에서 실행되며 %s 눈 깜박임을 알려 줍니다.",
        # The full "마우스 오른쪽 버튼으로 누르면" is 448px in a 408px card.
        "Right-click the tray icon, by the clock, for settings.":
            "시계 옆 아이콘을 오른쪽 클릭하면 설정이 열립니다.",
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
    },

    # Hindi. Devanagari, shaped correctly by Windows through Tk.
    "hi": {
        "Blink now": "अभी पलक झपकाएँ",
        "Resume reminders": "याद दिलाना फिर शुरू",
        "Snooze 30 minutes": "30 मिनट रोकें",
        "Settings": "सेटिंग्स",
        "Buy me a coffee": "मुझे कॉफ़ी पिलाएँ",
        "Quit": "बंद करें",

        "every second": "हर सेकंड",
        "every %d seconds": "हर %d सेकंड",
        "every minute": "हर मिनट",
        "every %d minutes": "हर %d मिनट",

        "%s is running": "%s चल रहा है",
        "It stays in the background and will nudge you to blink\n%s.":
            "यह पृष्ठभूमि में चलता है और %s पलक झपकाने की याद दिलाएगा।",
        "Right-click the tray icon, by the clock, for settings.":
            "घड़ी के पास वाले आइकन पर राइट-क्लिक करें।",
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
    },

    # Bengali. Nirmala UI covers it, and the conjuncts form correctly.
    "bn": {
        "Blink now": "এখনই চোখ পিটপিট",
        "Resume reminders": "মনে করানো চালু",
        "Snooze 30 minutes": "৩০ মিনিট থামান",
        "Settings": "সেটিংস",
        "Buy me a coffee": "আমাকে কফি খাওয়ান",
        "Quit": "বন্ধ করুন",

        "every second": "প্রতি সেকেন্ডে",
        "every %d seconds": "প্রতি %d সেকেন্ডে",
        "every minute": "প্রতি মিনিটে",
        "every %d minutes": "প্রতি %d মিনিটে",

        "%s is running": "%s চলছে",
        # Broken across two lines like the English, which is what keeps it
        # inside the notice: on one line it runs 446px of the 440 available.
        "It stays in the background and will nudge you to blink\n%s.":
            "এটি পটভূমিতে চলে এবং\n%s চোখের পলক ফেলার কথা মনে করাবে।",
        "Right-click the tray icon, by the clock, for settings.":
            "ঘড়ির পাশের আইকনে ডান-ক্লিক করুন।",
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

        "every second": "كل ثانية",
        "every %d seconds": "كل %d ثانية",
        "every minute": "كل دقيقة",
        "every %d minutes": "كل %d دقيقة",

        "%s is running": "%s قيد التشغيل",
        "It stays in the background and will nudge you to blink\n%s.":
            "يعمل في الخلفية ويذكّرك بالرمش %s.",
        "Right-click the tray icon, by the clock, for settings.":
            "انقر بزر الفأرة الأيمن على الأيقونة بجوار الساعة.",
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

        "every second": "ہر سیکنڈ",
        "every %d seconds": "ہر %d سیکنڈ",
        "every minute": "ہر منٹ",
        "every %d minutes": "ہر %d منٹ",

        "%s is running": "%s چل رہا ہے",
        "It stays in the background and will nudge you to blink\n%s.":
            "یہ پس منظر میں چلتا ہے اور %s پلک جھپکنے کی یاد دلائے گا۔",
        "Right-click the tray icon, by the clock, for settings.":
            "گھڑی کے پاس آئیکن پر دائیں کلک کریں۔",
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
    },

    # Indonesian.
    "id": {
        "Blink now": "Kedip sekarang",
        "Resume reminders": "Lanjutkan pengingat",
        "Snooze 30 minutes": "Tunda 30 menit",
        "Settings": "Pengaturan",
        "Buy me a coffee": "Traktir saya kopi",
        "Quit": "Keluar",

        "every second": "setiap detik",
        "every %d seconds": "setiap %d detik",
        "every minute": "setiap menit",
        "every %d minutes": "setiap %d menit",

        "%s is running": "%s sedang berjalan",
        "It stays in the background and will nudge you to blink\n%s.":
            "Berjalan di latar dan akan mengingatkan Anda berkedip\n%s.",
        "Right-click the tray icon, by the clock, for settings.":
            "Klik kanan ikon di sebelah jam untuk pengaturan.",
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

        "every second": "co sekundę",
        "every %d seconds": "co %d s",
        "every minute": "co minutę",
        "every %d minutes": "co %d min",

        "%s is running": "%s działa",
        "It stays in the background and will nudge you to blink\n%s.":
            "Działa w tle i będzie przypominać o mrugnięciu\n%s.",
        "Right-click the tray icon, by the clock, for settings.":
            "Kliknij prawym przyciskiem ikonę obok zegara.",
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
    },

    # Turkish.
    "tr": {
        "Blink now": "Şimdi göz kırp",
        "Resume reminders": "Hatırlatmaları sürdür",
        "Snooze 30 minutes": "30 dakika ertele",
        "Settings": "Ayarlar",
        "Buy me a coffee": "Bana kahve ısmarla",
        "Quit": "Çıkış",

        "every second": "her saniye",
        "every %d seconds": "her %d saniyede",
        "every minute": "her dakika",
        "every %d minutes": "her %d dakikada",

        "%s is running": "%s çalışıyor",
        "It stays in the background and will nudge you to blink\n%s.":
            "Arka planda çalışır ve %s göz kırpmanızı hatırlatır.",
        "Right-click the tray icon, by the clock, for settings.":
            "Saatin yanındaki simgeye sağ tıklayın.",
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
    },

    # Vietnamese.
    "vi": {
        "Blink now": "Chớp mắt ngay",
        "Resume reminders": "Tiếp tục nhắc",
        "Snooze 30 minutes": "Tạm dừng 30 phút",
        "Settings": "Cài đặt",
        "Buy me a coffee": "Mời tôi ly cà phê",
        "Quit": "Thoát",

        "every second": "mỗi giây",
        "every %d seconds": "mỗi %d giây",
        "every minute": "mỗi phút",
        "every %d minutes": "mỗi %d phút",

        "%s is running": "%s đang chạy",
        "It stays in the background and will nudge you to blink\n%s.":
            "Chạy nền và sẽ nhắc bạn chớp mắt\n%s.",
        "Right-click the tray icon, by the clock, for settings.":
            "Nhấp chuột phải vào biểu tượng cạnh đồng hồ.",
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

        "every second": "каждую секунду",
        "every %d seconds": "каждые %d сек.",
        "every minute": "каждую минуту",
        "every %d minutes": "каждые %d мин.",

        "%s is running": "%s работает",
        "It stays in the background and will nudge you to blink\n%s.":
            "Работает в фоне и напомнит моргнуть\n%s.",
        "Right-click the tray icon, by the clock, for settings.":
            "Щёлкните правой кнопкой по значку у часов.",
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

        "every second": "ทุกวินาที",
        "every %d seconds": "ทุก %d วินาที",
        "every minute": "ทุกนาที",
        "every %d minutes": "ทุก %d นาที",

        "%s is running": "%s กำลังทำงาน",
        "It stays in the background and will nudge you to blink\n%s.":
            "ทำงานอยู่เบื้องหลัง และจะเตือนให้กะพริบตา\n%s",
        "Right-click the tray icon, by the clock, for settings.":
            "คลิกขวาที่ไอคอนข้างนาฬิกาเพื่อตั้งค่า",
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

        "every second": "щосекунди",
        "every %d seconds": "кожні %d с",
        "every minute": "щохвилини",
        "every %d minutes": "кожні %d хв",

        "%s is running": "%s працює",
        "It stays in the background and will nudge you to blink\n%s.":
            "Працює у фоні й нагадає кліпнути\n%s.",
        "Right-click the tray icon, by the clock, for settings.":
            "Клацніть правою кнопкою по значку біля годинника.",
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
    },

    # Czech. Same plural problem as the Slavic languages above, same fix.
    "cs": {
        "Blink now": "Mrknout teď",
        "Resume reminders": "Obnovit připomínky",
        "Snooze 30 minutes": "Pozastavit na 30 minut",
        "Settings": "Nastavení",
        "Buy me a coffee": "Kup mi kávu",
        "Quit": "Ukončit",

        "every second": "každou sekundu",
        "every %d seconds": "každých %d s",
        "every minute": "každou minutu",
        "every %d minutes": "každých %d min",

        "%s is running": "%s běží",
        "It stays in the background and will nudge you to blink\n%s.":
            "Běží na pozadí a připomene vám mrknout\n%s.",
        "Right-click the tray icon, by the clock, for settings.":
            "Klikněte pravým tlačítkem na ikonu u hodin.",
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
    },

    # Romanian.
    "ro": {
        "Blink now": "Clipește acum",
        "Resume reminders": "Reia mementourile",
        "Snooze 30 minutes": "Amână 30 de minute",
        "Settings": "Setări",
        "Buy me a coffee": "Fă-mi cinste cu o cafea",
        "Quit": "Ieșire",

        "every second": "în fiecare secundă",
        "every %d seconds": "la fiecare %d secunde",
        "every minute": "în fiecare minut",
        "every %d minutes": "la fiecare %d minute",

        "%s is running": "%s rulează",
        "It stays in the background and will nudge you to blink\n%s.":
            "Rulează în fundal și îți va aminti să clipești\n%s.",
        "Right-click the tray icon, by the clock, for settings.":
            "Clic dreapta pe pictograma de lângă ceas pentru setări.",
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
    },

    # Hungarian.
    "hu": {
        "Blink now": "Pislogj most",
        "Resume reminders": "Emlékeztetők folytatása",
        "Snooze 30 minutes": "Szünet 30 percre",
        "Settings": "Beállítások",
        "Buy me a coffee": "Hívj meg egy kávéra",
        "Quit": "Kilépés",

        "every second": "másodpercenként",
        "every %d seconds": "%d másodpercenként",
        "every minute": "percenként",
        "every %d minutes": "%d percenként",

        "%s is running": "A(z) %s fut",
        "It stays in the background and will nudge you to blink\n%s.":
            "A háttérben fut, és %s emlékeztet a pislogásra.",
        "Right-click the tray icon, by the clock, for settings.":
            "Kattints jobb gombbal az óra melletti ikonra.",
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
    },

    # Greek.
    "el": {
        "Blink now": "Ανοιγοκλείσε τώρα",
        "Resume reminders": "Συνέχιση υπενθυμίσεων",
        "Snooze 30 minutes": "Παύση 30 λεπτών",
        "Settings": "Ρυθμίσεις",
        "Buy me a coffee": "Κέρασέ με έναν καφέ",
        "Quit": "Έξοδος",

        "every second": "κάθε δευτερόλεπτο",
        "every %d seconds": "κάθε %d δευτ.",
        "every minute": "κάθε λεπτό",
        "every %d minutes": "κάθε %d λεπτά",

        "%s is running": "Το %s εκτελείται",
        "It stays in the background and will nudge you to blink\n%s.":
            "Τρέχει στο παρασκήνιο και θα σου θυμίζει να "
            "ανοιγοκλείνεις\n%s.",
        "Right-click the tray icon, by the clock, for settings.":
            "Δεξί κλικ στο εικονίδιο δίπλα στο ρολόι για ρυθμίσεις.",
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
    },

    # Swedish.
    "sv": {
        "Blink now": "Blinka nu",
        "Resume reminders": "Återuppta påminnelser",
        "Snooze 30 minutes": "Pausa i 30 minuter",
        "Settings": "Inställningar",
        "Buy me a coffee": "Bjud på en kaffe",
        "Quit": "Avsluta",

        "every second": "varje sekund",
        "every %d seconds": "var %d:e sekund",
        "every minute": "varje minut",
        "every %d minutes": "var %d:e minut",

        "%s is running": "%s körs",
        "It stays in the background and will nudge you to blink\n%s.":
            "Den ligger i bakgrunden och påminner dig att blinka\n%s.",
        "Right-click the tray icon, by the clock, for settings.":
            "Högerklicka på ikonen bredvid klockan för inställningar.",
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
    },

    # Finnish.
    "fi": {
        "Blink now": "Räpäytä nyt",
        "Resume reminders": "Jatka muistutuksia",
        "Snooze 30 minutes": "Tauko 30 minuutiksi",
        "Settings": "Asetukset",
        "Buy me a coffee": "Tarjoa kahvit",
        "Quit": "Lopeta",

        "every second": "joka sekunti",
        "every %d seconds": "%d sekunnin välein",
        "every minute": "joka minuutti",
        "every %d minutes": "%d minuutin välein",

        "%s is running": "%s on käynnissä",
        "It stays in the background and will nudge you to blink\n%s.":
            "Se toimii taustalla ja muistuttaa räpäyttämään\n%s.",
        "Right-click the tray icon, by the clock, for settings.":
            "Napsauta kellon vieressä olevaa kuvaketta hiiren oikealla.",
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
    },

    # Danish.
    "da": {
        "Blink now": "Blink nu",
        "Resume reminders": "Genoptag påmindelser",
        "Snooze 30 minutes": "Pause i 30 minutter",
        "Settings": "Indstillinger",
        "Buy me a coffee": "Giv mig en kaffe",
        "Quit": "Afslut",

        "every second": "hvert sekund",
        "every %d seconds": "hvert %d. sekund",
        "every minute": "hvert minut",
        "every %d minutes": "hvert %d. minut",

        "%s is running": "%s kører",
        "It stays in the background and will nudge you to blink\n%s.":
            "Den kører i baggrunden og minder dig om at blinke\n%s.",
        "Right-click the tray icon, by the clock, for settings.":
            "Højreklik på ikonet ved uret for indstillinger.",
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
    },

    # Norwegian, Bokmal.
    "nb": {
        "Blink now": "Blunk nå",
        "Resume reminders": "Fortsett påminnelser",
        "Snooze 30 minutes": "Pause i 30 minutter",
        "Settings": "Innstillinger",
        "Buy me a coffee": "Spander en kaffe",
        "Quit": "Avslutt",

        "every second": "hvert sekund",
        "every %d seconds": "hvert %d. sekund",
        "every minute": "hvert minutt",
        "every %d minutes": "hvert %d. minutt",

        "%s is running": "%s kjører",
        "It stays in the background and will nudge you to blink\n%s.":
            "Den ligger i bakgrunnen og minner deg på å blunke\n%s.",
        "Right-click the tray icon, by the clock, for settings.":
            "Høyreklikk ikonet ved klokken for innstillinger.",
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
    },

    # Dutch.
    "nl": {
        "Blink now": "Knipper nu",
        "Resume reminders": "Herinneringen hervatten",
        "Snooze 30 minutes": "30 minuten pauzeren",
        "Settings": "Instellingen",
        "Buy me a coffee": "Trakteer op een koffie",
        "Quit": "Afsluiten",

        "every second": "elke seconde",
        "every %d seconds": "elke %d seconden",
        "every minute": "elke minuut",
        "every %d minutes": "elke %d minuten",

        "%s is running": "%s is actief",
        "It stays in the background and will nudge you to blink\n%s.":
            "Draait op de achtergrond en herinnert je eraan te "
            "knipperen\n%s.",
        "Right-click the tray icon, by the clock, for settings.":
            "Klik met rechts op het pictogram naast de klok.",
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
    },
}
