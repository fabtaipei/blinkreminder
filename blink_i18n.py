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
LANGUAGES = [
    ("English", "en"),
    ("繁體中文", "zh-Hant"),
    ("简体中文", "zh-Hans"),
    ("Français", "fr"),
    ("Español", "es"),
    ("Deutsch", "de"),
    ("Italiano", "it"),
    ("Português", "pt"),
    ("日本語", "ja"),
    ("한국어", "ko"),
    ("हिन्दी", "hi"),
    ("বাংলা", "bn"),
    ("العربية", "ar"),
    ("اردو", "ur"),
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
    # French, Spanish, German, Italian and Portuguese need nothing: Segoe UI
    # Variable covers every Latin-script language, and Cyrillic and Greek.
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
}
