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
]

ENGLISH_DESCRIPTION = 'A gentle cue to blink, and a reminder to look away from the screen. Free, no ads, nothing collected.'

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
        "溫和地提醒你眨眼，並提醒你把視線移開螢幕。免費、無廣告、不收集任何資料。",
        # Show a dot in the corner
        "在角落顯示小圓點",
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
        "温和地提醒你眨眼，并提醒你把视线移开屏幕。免费、无广告、不收集任何数据。",
        # Show a dot in the corner
        "在角落显示小圆点",
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
        "まばたきをそっと促し、画面から目を離すよう知らせます。無料・広告なし・データ収集なし。",
        # Show a dot in the corner
        "隅に点を表示",
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
        "눈을 깜빡이도록 부드럽게 알려 주고, 화면에서 눈을 떼도록 알려 줍니다. 무료, 광고 없음, 데이터 수집 없음.",
        # Show a dot in the corner
        "모서리에 점 표시",
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
        "Un signal discret pour cligner des yeux et un rappel de regarder ailleurs. Gratuit, sans pub, aucune donnée collectée.",
        # Show a dot in the corner
        "Afficher un point dans le coin",
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
        "Una señal discreta para parpadear y un aviso para apartar la vista. Gratis, sin anuncios, sin recopilar datos.",
        # Show a dot in the corner
        "Mostrar un punto en la esquina",
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
        "Ein dezenter Hinweis zum Blinzeln und eine Erinnerung, wegzuschauen. Kostenlos, ohne Werbung, ohne Datensammlung.",
        # Show a dot in the corner
        "Punkt in der Ecke anzeigen",
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
        "Un segnale discreto per sbattere le palpebre e uno per distogliere lo sguardo. Gratis, senza pubblicità né raccolta di dati.",
        # Show a dot in the corner
        "Mostra un punto nell'angolo",
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
        "Um sinal suave para piscar e um lembrete para desviar o olhar da tela. Grátis, sem anúncios, sem coleta de dados.",
        # Show a dot in the corner
        "Mostrar um ponto no canto",
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
        "Мягкий сигнал моргнуть и напоминание отвести взгляд от экрана. Бесплатно, без рекламы, без сбора данных.",
        # Show a dot in the corner
        "Показывать точку в углу",
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
        "М’який сигнал кліпнути й нагадування відвести погляд від екрана. Безкоштовно, без реклами, без збору даних.",
        # Show a dot in the corner
        "Показувати крапку в кутку",
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
        "Delikatny sygnał, by mrugnąć, i przypomnienie, by oderwać wzrok od ekranu. Za darmo, bez reklam, bez zbierania danych.",
        # Show a dot in the corner
        "Pokaż kropkę w rogu",
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
        "Jemný signál k mrknutí a připomínka, abyste odvrátili zrak od obrazovky. Zdarma, bez reklam, bez sběru dat.",
        # Show a dot in the corner
        "Zobrazit tečku v rohu",
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
        "Göz kırpmanız için hafif bir uyarı ve ekrandan uzağa bakmanız için bir hatırlatma. Ücretsiz, reklamsız, veri toplamaz.",
        # Show a dot in the corner
        "Köşede bir nokta göster",
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
        "Isyarat lembut untuk berkedip dan pengingat untuk mengalihkan pandangan dari layar. Gratis, tanpa iklan, tanpa pengumpulan data.",
        # Show a dot in the corner
        "Tampilkan titik di sudut",
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
        "Tín hiệu nhẹ nhàng nhắc bạn chớp mắt và nhìn ra xa màn hình. Miễn phí, không quảng cáo, không thu thập dữ liệu.",
        # Show a dot in the corner
        "Hiện chấm tròn ở góc",
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
        "สัญญาณเบาๆ ให้กะพริบตา และเตือนให้ละสายตาจากหน้าจอ ฟรี ไม่มีโฆษณา ไม่เก็บข้อมูล",
        # Show a dot in the corner
        "แสดงจุดที่มุมจอ",
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
        "पलक झपकाने के लिए एक हल्का संकेत और स्क्रीन से नज़र हटाने की याद। मुफ़्त, कोई विज्ञापन नहीं, कोई डेटा संग्रह नहीं।",
        # Show a dot in the corner
        "कोने में एक बिंदु दिखाएँ",
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
        "পলক ফেলার জন্য একটি মৃদু সংকেত এবং স্ক্রিন থেকে চোখ সরানোর রিমাইন্ডার। বিনামূল্যে, বিজ্ঞাপন নেই, কোনো ডেটা সংগ্রহ নেই।",
        # Show a dot in the corner
        "কোণে একটি বিন্দু দেখান",
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
        "إشارة لطيفة لترمش، وتذكير لتبعد نظرك عن الشاشة. مجاني، بلا إعلانات، ولا يجمع أي بيانات.",
        # Show a dot in the corner
        "إظهار نقطة في الزاوية",
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
        "پلک جھپکنے کا ہلکا سا اشارہ، اور اسکرین سے نظر ہٹانے کی یاد دہانی۔ مفت، بغیر اشتہار، کوئی ڈیٹا جمع نہیں۔",
        # Show a dot in the corner
        "کونے میں ایک نقطہ دکھائیں",
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
        "Un semnal discret să clipești și un memento să privești în altă parte. Gratuit, fără reclame, fără colectare de date.",
        # Show a dot in the corner
        "Arată un punct în colț",
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
        "Finom jelzés a pislogáshoz és emlékeztető, hogy nézz el a képernyőtől. Ingyenes, reklámmentes, nem gyűjt adatot.",
        # Show a dot in the corner
        "Pont megjelenítése a sarokban",
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
        "Διακριτικό σήμα να ανοιγοκλείνεις τα μάτια και να κοιτάς μακριά. Δωρεάν, χωρίς διαφημίσεις, καμία συλλογή δεδομένων.",
        # Show a dot in the corner
        "Εμφάνιση κουκκίδας στη γωνία",
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
        "En diskret signal att blinka och en påminnelse att titta bort från skärmen. Gratis, utan reklam, ingen datainsamling.",
        # Show a dot in the corner
        "Visa en prick i hörnet",
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
        "Hienovarainen merkki räpäyttää ja muistutus katsoa pois näytöltä. Ilmainen, ei mainoksia, ei tietojen keruuta.",
        # Show a dot in the corner
        "Näytä piste kulmassa",
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
        "Et diskret signal til at blinke og en påmindelse om at se væk fra skærmen. Gratis, ingen reklamer, ingen dataindsamling.",
        # Show a dot in the corner
        "Vis en prik i hjørnet",
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
        "Et diskret signal om å blunke og en påminnelse om å se bort fra skjermen. Gratis, uten reklame, ingen datainnsamling.",
        # Show a dot in the corner
        "Vis en prikk i hjørnet",
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
        "Een zacht signaal om te knipperen en een herinnering om weg te kijken van het scherm. Gratis, zonder advertenties, verzamelt niets.",
        # Show a dot in the corner
        "Een stip in de hoek tonen",
    ],
}
