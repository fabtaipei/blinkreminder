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
LANGUAGE_FONTS = {
    "zh-Hant": ("Microsoft JhengHei UI", "Microsoft JhengHei", "PMingLiU",
                "MingLiU", "Microsoft YaHei UI", "Yu Gothic UI"),
    # YaHei is Windows' own Simplified Chinese interface font, and the ladder
    # below it runs the other way from Traditional's: JhengHei sets the same
    # characters in Taiwanese conventions, which is a compromise on how the
    # text looks and never on whether it can be read.
    "zh-Hans": ("Microsoft YaHei UI", "Microsoft YaHei", "SimSun", "NSimSun",
                "Microsoft JhengHei UI", "Yu Gothic UI"),
    # French, Spanish, German and Italian need nothing: Segoe UI Variable
    # covers every Latin-script language, and Cyrillic and Greek besides.
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
}
