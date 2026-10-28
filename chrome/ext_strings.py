"""
The words only the Chrome extension says, in every language it speaks.

Data only, like blink_i18n.py, which holds everything the extension shares
with the desktop app. build_extension.py merges the two into strings.js.
Keys are the ENGLISH strings. "extDescription" is the one exception: it is
the store and chrome://extensions description, at most 132 characters.
"""

KEYS = [
    'Reminders on',
    'Show the cue on web pages',
    'Nothing on the page is read or sent anywhere.',
    'Without it, reminders come as notifications.',
    'Full version for Windows',
    'extDescription',
    'Show a dot in the corner',
    'Blink reminders need access to web pages.',
]

ENGLISH_DESCRIPTION = ('Blink more often and rest your eyes: a gentle on-page cue for '
                       'dry eyes and digital eye strain, with 20-20-20 screen breaks.')

STRINGS = {
    "zh-Hant": [
        # Reminders on
        "開啟提醒",
        # Show the cue on web pages
        "在網頁上顯示提示",
        # Nothing on the page is read or sent anywhere.
        "不會讀取或傳送網頁上的任何內容。",
        # Without it, reminders come as notifications.
        "未開啟時，提醒會以通知顯示。",
        # Full version for Windows
        "Windows 完整版",
        # extDescription
        "多眨眼，讓眼睛休息：頁面上的輕柔提示，針對乾眼與數位視疲勞，並有 20-20-20 休息。",
        # Show a dot in the corner
        "在角落顯示小圓點",
        # Blink reminders need access to web pages.
        "眨眼提醒需要存取網頁的權限。",
    ],
    "zh-Hans": [
        # Reminders on
        "开启提醒",
        # Show the cue on web pages
        "在网页上显示提示",
        # Nothing on the page is read or sent anywhere.
        "不会读取或发送网页上的任何内容。",
        # Without it, reminders come as notifications.
        "未开启时，提醒会以通知显示。",
        # Full version for Windows
        "Windows 完整版",
        # extDescription
        "多眨眼，让眼睛休息：页面上的轻柔提示，针对干眼与数码视疲劳，并有 20-20-20 休息。",
        # Show a dot in the corner
        "在角落显示小圆点",
        # Blink reminders need access to web pages.
        "眨眼提醒需要访问网页的权限。",
    ],
    "ja": [
        # Reminders on
        "リマインダー オン",
        # Show the cue on web pages
        "ウェブページに合図を表示",
        # Nothing on the page is read or sent anywhere.
        "ページの内容を読み取ったり送信したりすることはありません。",
        # Without it, reminders come as notifications.
        "オフの場合、リマインダーは通知で届きます。",
        # Full version for Windows
        "Windows 版（フル機能）",
        # extDescription
        "まばたきを増やして目を休める：ドライアイと眼精疲労のための控えめな画面上の合図と、20-20-20 休憩。",
        # Show a dot in the corner
        "隅に点を表示",
        # Blink reminders need access to web pages.
        "まばたきリマインダーにはウェブページへのアクセスが必要です。",
    ],
    "ko": [
        # Reminders on
        "알림 켜기",
        # Show the cue on web pages
        "웹 페이지에 신호 표시",
        # Nothing on the page is read or sent anywhere.
        "페이지의 내용을 읽거나 전송하지 않습니다.",
        # Without it, reminders come as notifications.
        "끄면 알림은 시스템 알림으로 표시됩니다.",
        # Full version for Windows
        "Windows용 정식 버전",
        # extDescription
        "더 자주 깜빡이고 눈을 쉬게 하세요: 안구건조증과 디지털 눈 피로를 위한 페이지 내 부드러운 신호, 20-20-20 휴식 포함.",
        # Show a dot in the corner
        "모서리에 점 표시",
        # Blink reminders need access to web pages.
        "깜빡임 알림에는 웹페이지 접근 권한이 필요합니다.",
    ],
    "fr": [
        # Reminders on
        "Rappels activés",
        # Show the cue on web pages
        "Afficher le signal sur les pages web",
        # Nothing on the page is read or sent anywhere.
        "Rien sur la page n'est lu ni envoyé nulle part.",
        # Without it, reminders come as notifications.
        "Sinon, les rappels arrivent sous forme de notifications.",
        # Full version for Windows
        "Version complète pour Windows",
        # extDescription
        "Clignez plus souvent, reposez vos yeux : signal discret sur la page pour yeux secs et fatigue visuelle, avec pauses 20-20-20.",
        # Show a dot in the corner
        "Afficher un point dans le coin",
        # Blink reminders need access to web pages.
        "Les rappels de clignement nécessitent l'accès aux pages web.",
    ],
    "es": [
        # Reminders on
        "Recordatorios activados",
        # Show the cue on web pages
        "Mostrar la señal en las páginas web",
        # Nothing on the page is read or sent anywhere.
        "No se lee ni se envía nada de la página.",
        # Without it, reminders come as notifications.
        "Si no, los recordatorios llegan como notificaciones.",
        # Full version for Windows
        "Versión completa para Windows",
        # extDescription
        "Parpadea más y descansa la vista: una señal discreta en la página para ojo seco y fatiga visual digital, con pausas 20-20-20.",
        # Show a dot in the corner
        "Mostrar un punto en la esquina",
        # Blink reminders need access to web pages.
        "Los recordatorios de parpadeo necesitan acceso a las páginas web.",
    ],
    "de": [
        # Reminders on
        "Erinnerungen an",
        # Show the cue on web pages
        "Hinweis auf Webseiten anzeigen",
        # Nothing on the page is read or sent anywhere.
        "Vom Seiteninhalt wird nichts gelesen oder gesendet.",
        # Without it, reminders come as notifications.
        "Ohne das kommen Erinnerungen als Benachrichtigungen.",
        # Full version for Windows
        "Vollversion für Windows",
        # extDescription
        "Öfter blinzeln, Augen entspannen: dezenter Hinweis auf der Seite bei trockenen Augen und digitaler Augenbelastung, 20-20-20-Pausen.",
        # Show a dot in the corner
        "Punkt in der Ecke anzeigen",
        # Blink reminders need access to web pages.
        "Blinzel-Erinnerungen brauchen Zugriff auf Webseiten.",
    ],
    "it": [
        # Reminders on
        "Promemoria attivi",
        # Show the cue on web pages
        "Mostra il segnale sulle pagine web",
        # Nothing on the page is read or sent anywhere.
        "Nulla della pagina viene letto o inviato.",
        # Without it, reminders come as notifications.
        "Altrimenti i promemoria arrivano come notifiche.",
        # Full version for Windows
        "Versione completa per Windows",
        # extDescription
        "Sbatti le palpebre e riposa gli occhi: segnale discreto in pagina per occhi secchi e affaticamento visivo digitale, pause 20-20-20.",
        # Show a dot in the corner
        "Mostra un punto nell'angolo",
        # Blink reminders need access to web pages.
        "I promemoria per sbattere le palpebre richiedono l'accesso alle pagine web.",
    ],
    "pt": [
        # Reminders on
        "Lembretes ativados",
        # Show the cue on web pages
        "Mostrar o sinal nas páginas da web",
        # Nothing on the page is read or sent anywhere.
        "Nada da página é lido ou enviado.",
        # Without it, reminders come as notifications.
        "Sem isso, os lembretes chegam como notificações.",
        # Full version for Windows
        "Versão completa para Windows",
        # extDescription
        "Pisque mais e descanse os olhos: um sinal suave na página para olho seco e fadiga ocular digital, com pausas 20-20-20.",
        # Show a dot in the corner
        "Mostrar um ponto no canto",
        # Blink reminders need access to web pages.
        "Os lembretes para piscar precisam de acesso às páginas da web.",
    ],
    "ru": [
        # Reminders on
        "Напоминания включены",
        # Show the cue on web pages
        "Показывать сигнал на веб-страницах",
        # Nothing on the page is read or sent anywhere.
        "Ничего со страницы не читается и никуда не отправляется.",
        # Without it, reminders come as notifications.
        "Без этого напоминания приходят как уведомления.",
        # Full version for Windows
        "Полная версия для Windows",
        # extDescription
        "Моргайте чаще и давайте глазам отдых: мягкий сигнал на странице при сухости и усталости глаз, с перерывами 20-20-20.",
        # Show a dot in the corner
        "Показывать точку в углу",
        # Blink reminders need access to web pages.
        "Напоминания моргать требуют доступа к веб-страницам.",
    ],
    "uk": [
        # Reminders on
        "Нагадування увімкнено",
        # Show the cue on web pages
        "Показувати сигнал на вебсторінках",
        # Nothing on the page is read or sent anywhere.
        "Нічого зі сторінки не зчитується й нікуди не надсилається.",
        # Without it, reminders come as notifications.
        "Без цього нагадування надходять як сповіщення.",
        # Full version for Windows
        "Повна версія для Windows",
        # extDescription
        "Кліпайте частіше й давайте очам відпочинок: м’який сигнал на сторінці при сухості та втомі очей, з перервами 20-20-20.",
        # Show a dot in the corner
        "Показувати крапку в кутку",
        # Blink reminders need access to web pages.
        "Нагадування кліпати потребують доступу до вебсторінок.",
    ],
    "pl": [
        # Reminders on
        "Przypomnienia włączone",
        # Show the cue on web pages
        "Pokazuj sygnał na stronach",
        # Nothing on the page is read or sent anywhere.
        "Nic ze strony nie jest odczytywane ani wysyłane.",
        # Without it, reminders come as notifications.
        "Bez tego przypomnienia przychodzą jako powiadomienia.",
        # Full version for Windows
        "Pełna wersja dla Windows",
        # extDescription
        "Mrugaj częściej i daj oczom odpocząć: delikatny sygnał na stronie przy suchych oczach i cyfrowym zmęczeniu wzroku, przerwy 20-20-20.",
        # Show a dot in the corner
        "Pokaż kropkę w rogu",
        # Blink reminders need access to web pages.
        "Przypomnienia o mruganiu wymagają dostępu do stron.",
    ],
    "cs": [
        # Reminders on
        "Připomínky zapnuté",
        # Show the cue on web pages
        "Zobrazovat signál na webových stránkách",
        # Nothing on the page is read or sent anywhere.
        "Ze stránky se nic nečte ani neodesílá.",
        # Without it, reminders come as notifications.
        "Bez toho přicházejí připomínky jako oznámení.",
        # Full version for Windows
        "Plná verze pro Windows",
        # extDescription
        "Mrkejte častěji a dopřejte očím odpočinek: jemný signál na stránce pro suché oči a digitální únavu očí, s přestávkami 20-20-20.",
        # Show a dot in the corner
        "Zobrazit tečku v rohu",
        # Blink reminders need access to web pages.
        "Připomínky mrkání potřebují přístup k webovým stránkám.",
    ],
    "tr": [
        # Reminders on
        "Hatırlatıcılar açık",
        # Show the cue on web pages
        "Uyarıyı web sayfalarında göster",
        # Nothing on the page is read or sent anywhere.
        "Sayfadaki hiçbir şey okunmaz veya gönderilmez.",
        # Without it, reminders come as notifications.
        "Bu kapalıyken hatırlatıcılar bildirim olarak gelir.",
        # Full version for Windows
        "Windows için tam sürüm",
        # extDescription
        "Daha sık göz kırpın, gözlerinizi dinlendirin: sayfada hafif uyarı; kuru göz ve dijital göz yorgunluğu için, 20-20-20 molalarıyla.",
        # Show a dot in the corner
        "Köşede bir nokta göster",
        # Blink reminders need access to web pages.
        "Göz kırpma hatırlatıcıları web sayfalarına erişim gerektirir.",
    ],
    "id": [
        # Reminders on
        "Pengingat aktif",
        # Show the cue on web pages
        "Tampilkan isyarat di halaman web",
        # Nothing on the page is read or sent anywhere.
        "Tidak ada isi halaman yang dibaca atau dikirim.",
        # Without it, reminders come as notifications.
        "Tanpa ini, pengingat muncul sebagai notifikasi.",
        # Full version for Windows
        "Versi lengkap untuk Windows",
        # extDescription
        "Berkedip lebih sering dan istirahatkan mata: isyarat lembut di halaman untuk mata kering dan kelelahan mata digital, jeda 20-20-20.",
        # Show a dot in the corner
        "Tampilkan titik di sudut",
        # Blink reminders need access to web pages.
        "Pengingat berkedip memerlukan akses ke halaman web.",
    ],
    "vi": [
        # Reminders on
        "Bật nhắc nhở",
        # Show the cue on web pages
        "Hiện tín hiệu trên trang web",
        # Nothing on the page is read or sent anywhere.
        "Không đọc hay gửi bất cứ thứ gì trên trang.",
        # Without it, reminders come as notifications.
        "Nếu tắt, nhắc nhở sẽ đến dưới dạng thông báo.",
        # Full version for Windows
        "Bản đầy đủ cho Windows",
        # extDescription
        "Chớp mắt nhiều hơn và để mắt nghỉ: tín hiệu nhẹ trên trang cho mắt khô và mỏi mắt do màn hình, kèm nghỉ 20-20-20.",
        # Show a dot in the corner
        "Hiện chấm tròn ở góc",
        # Blink reminders need access to web pages.
        "Nhắc chớp mắt cần quyền truy cập trang web.",
    ],
    "th": [
        # Reminders on
        "เปิดการเตือน",
        # Show the cue on web pages
        "แสดงสัญญาณบนหน้าเว็บ",
        # Nothing on the page is read or sent anywhere.
        "ไม่มีการอ่านหรือส่งข้อมูลใดๆ จากหน้าเว็บ",
        # Without it, reminders come as notifications.
        "หากปิดไว้ การเตือนจะมาเป็นการแจ้งเตือน",
        # Full version for Windows
        "เวอร์ชันเต็มสำหรับ Windows",
        # extDescription
        "กะพริบตาบ่อยขึ้นและพักสายตา: สัญญาณเบาๆ บนหน้าเว็บ สำหรับตาแห้งและอาการตาล้าจากจอ พร้อมพัก 20-20-20",
        # Show a dot in the corner
        "แสดงจุดที่มุมจอ",
        # Blink reminders need access to web pages.
        "การเตือนให้กะพริบตาต้องเข้าถึงหน้าเว็บ",
    ],
    "hi": [
        # Reminders on
        "रिमाइंडर चालू",
        # Show the cue on web pages
        "वेब पेजों पर संकेत दिखाएँ",
        # Nothing on the page is read or sent anywhere.
        "पेज से कुछ भी पढ़ा या कहीं भेजा नहीं जाता।",
        # Without it, reminders come as notifications.
        "इसके बिना, रिमाइंडर सूचनाओं के रूप में आते हैं।",
        # Full version for Windows
        "Windows के लिए पूरा संस्करण",
        # extDescription
        "अधिक पलक झपकाएँ और आँखों को आराम दें: सूखी आँखों और डिजिटल आई स्ट्रेन के लिए पेज पर हल्का संकेत, 20-20-20 ब्रेक के साथ।",
        # Show a dot in the corner
        "कोने में एक बिंदु दिखाएँ",
        # Blink reminders need access to web pages.
        "पलक झपकाने के रिमाइंडर को वेब पेजों तक पहुँच चाहिए।",
    ],
    "bn": [
        # Reminders on
        "রিমাইন্ডার চালু",
        # Show the cue on web pages
        "ওয়েব পেজে সংকেত দেখান",
        # Nothing on the page is read or sent anywhere.
        "পেজের কিছুই পড়া বা কোথাও পাঠানো হয় না।",
        # Without it, reminders come as notifications.
        "এটি ছাড়া রিমাইন্ডার নোটিফিকেশন হিসেবে আসে।",
        # Full version for Windows
        "Windows-এর পূর্ণ সংস্করণ",
        # extDescription
        "আরও পলক ফেলুন, চোখ বিশ্রাম দিন: শুষ্ক চোখ ও ডিজিটাল আই স্ট্রেনের জন্য পাতায় মৃদু সংকেত, সঙ্গে 20-20-20 বিরতি।",
        # Show a dot in the corner
        "কোণে একটি বিন্দু দেখান",
        # Blink reminders need access to web pages.
        "পলক ফেলার রিমাইন্ডারের জন্য ওয়েব পেজে প্রবেশাধিকার দরকার।",
    ],
    "ar": [
        # Reminders on
        "التذكيرات مفعّلة",
        # Show the cue on web pages
        "إظهار الإشارة على صفحات الويب",
        # Nothing on the page is read or sent anywhere.
        "لا يُقرأ أي شيء من الصفحة ولا يُرسل إلى أي مكان.",
        # Without it, reminders come as notifications.
        "بدونه، تصلك التذكيرات كإشعارات.",
        # Full version for Windows
        "النسخة الكاملة لنظام Windows",
        # extDescription
        "ارمش أكثر وأرِح عينيك: تنبيه لطيف داخل الصفحة لجفاف العين وإجهاد العين الرقمي، مع فترات راحة 20-20-20.",
        # Show a dot in the corner
        "إظهار نقطة في الزاوية",
        # Blink reminders need access to web pages.
        "تحتاج تذكيرات الرمش إلى الوصول إلى صفحات الويب.",
    ],
    # No Chrome locale for Urdu, so its description is never shown;
    # the rest appear through the extension's own language picker.
    "ur": [
        # Reminders on
        "یاد دہانیاں آن",
        # Show the cue on web pages
        "ویب صفحات پر اشارہ دکھائیں",
        # Nothing on the page is read or sent anywhere.
        "صفحے سے کچھ بھی پڑھا یا کہیں بھیجا نہیں جاتا۔",
        # Without it, reminders come as notifications.
        "اس کے بغیر یاد دہانیاں اطلاعات کی صورت میں آتی ہیں۔",
        # Full version for Windows
        "Windows کے لیے مکمل ورژن",
        # extDescription
        "زیادہ پلکیں جھپکائیں اور آنکھوں کو آرام دیں: خشک آنکھوں اور ڈیجیٹل آنکھوں کے تناؤ کے لیے صفحے پر ہلکا اشارہ، 20-20-20 وقفوں کے ساتھ۔",
        # Show a dot in the corner
        "کونے میں ایک نقطہ دکھائیں",
        # Blink reminders need access to web pages.
        "پلک جھپکنے کی یاد دہانیوں کو ویب صفحات تک رسائی درکار ہے۔",
    ],
    "ro": [
        # Reminders on
        "Mementouri active",
        # Show the cue on web pages
        "Arată semnalul pe paginile web",
        # Nothing on the page is read or sent anywhere.
        "Nimic de pe pagină nu este citit sau trimis.",
        # Without it, reminders come as notifications.
        "Fără asta, mementourile vin ca notificări.",
        # Full version for Windows
        "Versiunea completă pentru Windows",
        # extDescription
        "Clipește mai des și odihnește-ți ochii: un semnal discret în pagină pentru ochi uscați și oboseală vizuală, cu pauze 20-20-20.",
        # Show a dot in the corner
        "Arată un punct în colț",
        # Blink reminders need access to web pages.
        "Mementourile de clipit au nevoie de acces la paginile web.",
    ],
    "hu": [
        # Reminders on
        "Emlékeztetők bekapcsolva",
        # Show the cue on web pages
        "Jelzés megjelenítése weboldalakon",
        # Nothing on the page is read or sent anywhere.
        "Az oldalról semmit nem olvas be és nem küld el.",
        # Without it, reminders come as notifications.
        "Enélkül az emlékeztetők értesítésként érkeznek.",
        # Full version for Windows
        "Teljes verzió Windowsra",
        # extDescription
        "Pislogjon többet, pihentesse a szemét: finom jelzés az oldalon száraz szemre és digitális szemfáradtságra, 20-20-20 szünetekkel.",
        # Show a dot in the corner
        "Pont megjelenítése a sarokban",
        # Blink reminders need access to web pages.
        "A pislogás-emlékeztetőkhöz hozzáférés kell a weboldalakhoz.",
    ],
    "el": [
        # Reminders on
        "Υπενθυμίσεις ενεργές",
        # Show the cue on web pages
        "Εμφάνιση του σήματος σε ιστοσελίδες",
        # Nothing on the page is read or sent anywhere.
        "Τίποτα από τη σελίδα δεν διαβάζεται ούτε αποστέλλεται.",
        # Without it, reminders come as notifications.
        "Χωρίς αυτό, οι υπενθυμίσεις έρχονται ως ειδοποιήσεις.",
        # Full version for Windows
        "Πλήρης έκδοση για Windows",
        # extDescription
        "Ανοιγοκλείνετε τα μάτια πιο συχνά: διακριτικό σήμα στη σελίδα για ξηροφθαλμία και ψηφιακή καταπόνηση, με διαλείμματα 20-20-20.",
        # Show a dot in the corner
        "Εμφάνιση κουκκίδας στη γωνία",
        # Blink reminders need access to web pages.
        "Οι υπενθυμίσεις για ανοιγοκλείσιμο χρειάζονται πρόσβαση στις ιστοσελίδες.",
    ],
    "sv": [
        # Reminders on
        "Påminnelser på",
        # Show the cue on web pages
        "Visa signalen på webbsidor",
        # Nothing on the page is read or sent anywhere.
        "Inget på sidan läses eller skickas någonstans.",
        # Without it, reminders come as notifications.
        "Utan det kommer påminnelserna som aviseringar.",
        # Full version for Windows
        "Fullversion för Windows",
        # extDescription
        "Blinka oftare och vila ögonen: en diskret signal på sidan mot torra ögon och digital ögontrötthet, med 20-20-20-pauser.",
        # Show a dot in the corner
        "Visa en prick i hörnet",
        # Blink reminders need access to web pages.
        "Blinkpåminnelser behöver åtkomst till webbsidor.",
    ],
    "fi": [
        # Reminders on
        "Muistutukset päällä",
        # Show the cue on web pages
        "Näytä merkki verkkosivuilla",
        # Nothing on the page is read or sent anywhere.
        "Sivulta ei lueta eikä lähetetä mitään.",
        # Without it, reminders come as notifications.
        "Ilman sitä muistutukset tulevat ilmoituksina.",
        # Full version for Windows
        "Täysi versio Windowsille",
        # extDescription
        "Räpäytä useammin ja lepuuta silmiä: hienovarainen merkki sivulla kuiviin silmiin ja silmien rasitukseen, 20-20-20-tauoilla.",
        # Show a dot in the corner
        "Näytä piste kulmassa",
        # Blink reminders need access to web pages.
        "Räpäytysmuistutukset tarvitsevat pääsyn verkkosivuille.",
    ],
    "da": [
        # Reminders on
        "Påmindelser til",
        # Show the cue on web pages
        "Vis signalet på websider",
        # Nothing on the page is read or sent anywhere.
        "Intet på siden læses eller sendes nogen steder hen.",
        # Without it, reminders come as notifications.
        "Uden det kommer påmindelserne som notifikationer.",
        # Full version for Windows
        "Fuld version til Windows",
        # extDescription
        "Blink oftere, og hvil øjnene: et diskret signal på siden mod tørre øjne og digital øjenbelastning, med 20-20-20-pauser.",
        # Show a dot in the corner
        "Vis en prik i hjørnet",
        # Blink reminders need access to web pages.
        "Blinkpåmindelser kræver adgang til websider.",
    ],
    "nb": [
        # Reminders on
        "Påminnelser på",
        # Show the cue on web pages
        "Vis signalet på nettsider",
        # Nothing on the page is read or sent anywhere.
        "Ingenting på siden leses eller sendes noe sted.",
        # Without it, reminders come as notifications.
        "Uten dette kommer påminnelsene som varsler.",
        # Full version for Windows
        "Fullversjon for Windows",
        # extDescription
        "Blunk oftere og hvil øynene: et diskret signal på siden mot tørre øyne og digital øyebelastning, med 20-20-20-pauser.",
        # Show a dot in the corner
        "Vis en prikk i hjørnet",
        # Blink reminders need access to web pages.
        "Blunkepåminnelser krever tilgang til nettsider.",
    ],
    "nl": [
        # Reminders on
        "Herinneringen aan",
        # Show the cue on web pages
        "Signaal tonen op webpagina's",
        # Nothing on the page is read or sent anywhere.
        "Niets op de pagina wordt gelezen of verstuurd.",
        # Without it, reminders come as notifications.
        "Zonder dit komen herinneringen als meldingen.",
        # Full version for Windows
        "Volledige versie voor Windows",
        # extDescription
        "Knipper vaker en rust je ogen: een zacht signaal op de pagina bij droge ogen en digitale oogklachten, met 20-20-20-pauzes.",
        # Show a dot in the corner
        "Een stip in de hoek tonen",
        # Blink reminders need access to web pages.
        "Knipperherinneringen hebben toegang tot webpagina's nodig.",
    ],
}
