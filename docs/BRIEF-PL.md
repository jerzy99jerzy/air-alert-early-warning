# MAVO

**System wczesnego ostrzegania przed zagrożeniem z powietrza, budowany po
godzinach. Projekt prywatny, w fazie pre-alfa; nikt nie dostaje z niego dziś
żadnego powiadomienia.**

Dla czytelnika, który nie pisze kodu.

```
Document:  docs/BRIEF-PL.md, version 2.26
Measured:  każdą zmierzoną liczbę z tego pliku bramka zestawia ze
           STATUS.json przy każdym przebiegu, więc ręczy za nią to
           porównanie, a nie data w nagłówku. Wartości, z którymi są
           zestawiane, pochodzą z 0.55.2.0. Dwa wcześniejsze nagłówki
           podawały zamiast tego datę i oba mijały się z prawdą, zanim
           ktokolwiek je przeczytał: wersja 2.4 datowała się na 2026-08-31,
           a cztery liczby w środku pochodziły z 0.32.9.0; wersja 2.23
           zostawiła tę linijkę, choć wartości odniesienia przesunęły się
           przez pięć wydań. Obie sprawy opisuje sekcja „Czego nie trzeba
           brać na słowo”. Liczby z korpusu zmierzono 2026-08-17 i nie
           zmieniły się; zmieniło się źródło, i jest to powiedziane tam,
           gdzie się stało
Audience:  polski czytelnik bez przygotowania technicznego: dziennikarz,
           analityk z innej dziedziny, ktoś, kto mógłby te ostrzeżenia
           odbierać, ktoś, kto ocenia staranność autora
Companion: BRIEF (ten sam dokument po angielsku), FOUNDATIONS (te same
           twierdzenia z etykietami pochodzenia), METHODOLOGY (rejestr
           błędów)
Note:      to jest wersja pierwotna, angielska powstała po niej. Czytelnicy,
           dla których ten tekst powstaje, są Polakami. Żaden termin nie
           pojawia się tu przed wyjaśnieniem, a każda zmierzona liczba ma
           swój zapis w STATUS.json
```

---

## O co w tym chodzi, w jednym akapicie

Kiedy nad Ukrainą lecą pociski albo drony, ukraińskie władze ogłaszają alarm dla
wskazanych z nazwy rejonów. Ogłoszenia te są publiczne i pojawiają się
natychmiast. Komuś, kto mieszka w Hrubieszowie, wiadomość, że alarm objął
właśnie rejon oddalony o 40 kilometrów, ma znaczenie i dociera wcześniej niż
cokolwiek, co powie polska strona. MAVO czyta te ogłoszenia i pokazuje je po
polsku: który rejon, jakie zagrożenie, ile kilometrów do granicy.

Tyle. Nie przewiduje, czy cokolwiek przekroczy polską granicę.

## Skąd to się wzięło

W nocy z 29 na 30 lipca 2026 r., podczas zmasowanego rosyjskiego ataku
rakietowego na Ukrainę, pocisk manewrujący Ch-101 wszedł w polską przestrzeń
powietrzną. Wykryto go o 03:40 i zgubiono z radarów o 03:46, sześć minut
później; spadł na pole pod Tarnawą-Kolonią w Lubelskiem, jakieś sto kilometrów w
głąb kraju `[raportowane; Dowództwo Operacyjne RSZ za prasą krajową]`.

Sześć minut. W tym oknie najszybszą informacją dla mieszkańca były syreny, a te
odzywają się dopiero wtedy, gdy coś już leci w tę stronę.

Ten projekt zaczyna się nie od tamtych sześciu minut, tylko od **godziny, która
je poprzedza**. Alarmy w ukraińskich rejonach przygranicznych ogłasza się
znacznie wcześniej, a nikt nie podaje ich polskiemu czytelnikowi w formie, którą
da się przeczytać w trzy sekundy o wpół do czwartej nad ranem.

Jeden szczegół z tamtej nocy należy do tekstu, a nie do przypisu, bo najjaśniej
pokazuje, czego ten projekt robić nie zamierza. Ukraińskie myśliwce ścigały
pociski aż do granicy i próbowały je zniszczyć, a ich sygnatura radarowa była
trudna do odróżnienia od samych pocisków, co opóźniło decyzję po polskiej
stronie `[raportowane]`. Od tego właśnie zależy, czy coś przekroczy granicę: od
przechwyceń, od pościgów, od decyzji podejmowanych w powietrzu. Niczego z tego
nie ma w żadnym kanale, który ten projekt potrafi czytać.

## Skąd dane

**Ta sekcja zmieniła się 30 sierpnia 2026 r. i ta zmiana jest najbardziej
pouczającą rzeczą w całym dokumencie.**

Do tamtego dnia źródłem był jeden publiczny kanał na Telegramie, na którym
ukraińskie służby ogłaszają alarmy. Zebrano z niego **61 041 wiadomości**,
jednym ciągiem, bez luk, z sumą kontrolną zapisaną nad całością. Pomiary w tym
dokumencie nadal pochodzą z tamtego korpusu, a dokładniej z okna projektowego
liczącego **99 nocy i 48 540 wiadomości**; resztę odłożono i piszemy o tym
niżej.

29 sierpnia 2026 r. o 04:55 UTC kanał przestał publikować. Milczał około
trzydziestu czterech godzin, przez noc nalotów, które inne doniesienia opisywały
jako nieprzerwane. Z projektem nie stało się przy tym nic złego: przez cały ten
czas pisał, że jego obraz jest stary, i podawał, o ile, bo właśnie do tego
został zbudowany. System, który rzetelnie melduje własną ślepotę, pozostaje
jednak ślepy, więc następnego dnia źródło przełączono na oficjalne ukraińskie
API alarmowe, które nie przestało publikować. Kanał jest dalej czytany, ale nie
jako drugie źródło, tylko jako czujka: gdy nadawca wróci, projekt to zauważy i
powie, które z dwóch źródeł się odezwało.

**Dwa kanały to nie są dwa źródła i na tym rozróżnieniu wszystko tu stoi.** Oba
pochodzą od tego samego nadawcy, więc ich zgodność mierzy drogę dostawy i nic
poza tym. Jedno źródło to poważna słabość i dokumentacja mówi to wprost, zamiast
ją upiększać. Komercyjne API, które wyglądały na niezależną alternatywę, okazały
się czytać ten sam kanał, dlatego sięgnięcie po nie dałoby poczucie
potwierdzenia bez niczego, co by je uzasadniało.

Przełączenie kosztowało coś konkretnego i jest to nazwane, a nie schowane: API
ma jeden typ na wszystko, co lata, więc tam, gdzie kanał powiedziałby, co jest w
powietrzu, API zwykle milczy. Przez kilka godzin mapa tłumaczyła to milczenie na
„rakietę”, co było błędem projektu, a nie słowem nadawcy; teraz pisze w takim
wypadku **typ nieznany**, czyli to, co rzeczywiście wiadomo.

Kanał miał jedną cechę, która przesądziła o całej konstrukcji, i dlatego korpus
opisany niżej jest wart tyle, ile jest wart: **99,3% wiadomości niesie hasztag z
nazwą rejonu**, w mianowniku, z podkreśleniami w miejscu spacji. Kanał sam
etykietuje swoje wiadomości, a projekt tę etykietę czyta. Nie ma tu uczenia
maszynowego ani rozpoznawania nazw w samym tekście, bo nie ma czego rozpoznawać.
W oknie projektowym jest 127 różnych hasztagów, z czego **126 daje się
jednoznacznie przypisać** do kodu w ukraińskim rejestrze państwowym.

Pierwsza wersja tego czytnika działała inaczej: szukała nazw obwodów w treści
wiadomości. Sprawdzona na dwudziestu prawdziwych wiadomościach trafiła **0 razy
na 20**. Nie dlatego, że była źle napisana, tylko dlatego, że powstała z
wyobrażenia o tym, jak kanał formułuje zdania, a nie z tego, jak formułuje je
naprawdę. Wynik zapisano w repozytorium jako błąd z numerem, razem z
wyjaśnieniem, dlaczego żaden przegląd kodu by go nie znalazł.

Wersja po przebudowie ustala obszar w **20 wiadomościach na 20** z takiej samej
próby prawdziwej treści, a wynik zapisano jako warunek, którego nie da się
złamać po cichu. Osobno sprawdzono zgodność hasztagu z tym, co wiadomość mówi
własnymi słowami: na **38 521 porównywalnych wiadomościach oba wskazania
zgadzają się w ponad 99,99% przypadków**. To jedyna wewnętrzna kontrola
rozpoznawania obszaru dostępna bez drugiego źródła i tak jest opisywana, a nie
jako niezależne potwierdzenie.

## Dlaczego nie przewiduje przekroczenia granicy

To najważniejsza część i jedyna, która potrzebuje liczb.

Obserwacja, od której projekt się zaczął: każde naruszenie polskiej przestrzeni
powietrznej w badanym okresie wypadło w noc zmasowanego uderzenia na zachodnią
Ukrainę. Brzmi to jak gotowy przepis na przewidywanie.

Kłopot w tym, że **noce zmasowanych uderzeń to około 57% dób**
`[liczba cudza, dla okresu i obszaru, których ten projekt nie mierzył]`.
Naruszeń było kilkanaście w ciągu czterech lat, czyli mniej więcej trzy rocznie.

Zbudujmy z tego najprostszy możliwy system: alarm w każdą noc uderzenia. Odezwie
się ponad 200 razy w roku i trafi 3 razy. Nie przegapi niczego. I nie powie
nikomu nic, czego nie mówi kalendarz.

Jest też liczba własna, zmierzona na tym korpusie, a nie pożyczona. W oknie
projektowym alarm objął całą zachodnią Ukrainę w **22 noce**, a naruszeń
polskiej przestrzeni powietrznej zgłoszono w te noce **zero**. Reguła budząca
ludzi w każdą taką noc zanotowałaby w tym oknie 22 pobudki i 0 trafień. Dla
skali: w tych 99 nocach było 81 epizodów alarmowych w zachodnich rejonach, z
czego 22 objęły cały zachód, czyli **5,7 i 1,6 epizodu tygodniowo**. Jedno
miejsce po przecinku, bo przy dwudziestu dwóch zdarzeniach drugie opisywałoby
szum, a nie tempo; pełne ilorazy stoją w `docs/CHANNEL.md`, gdzie czyta je ktoś,
kto sprawdza rachunek.

Można zapytać, czy taki system nie jest jednak odrobinę lepszy niż nic.
Prawdopodobnie tak, odrobinę. **Ale przy trzech zdarzeniach rocznie nie da się
tego wykazać.** Jedna nietypowa noc przeważa cały wynik. To tak, jakby po
dwunastu rzutach twierdzić, że moneta jest fałszywa: może i jest, ale nie na tej
podstawie.

Dlatego w projekcie jest część, której jedynym zadaniem jest **próba wykazania,
że każda proponowana reguła alarmu nic nie daje**. Mierzy, o ile reguła
wyprzedza kalendarz, i bierze pesymistyczny koniec przedziału ufności, pytając
nie „ile wyszło”, tylko „ile da się jeszcze utrzymać, jeśli akurat dopisało nam
szczęście”. Żadna reguła nie ma prawa nikogo obudzić, dopóki tego nie przejdzie.
Jak dotąd przeszła jedna, dla zagrożenia rakietowego.

Jest też powód głębszy niż statystyka. To, czy coś przekroczy granicę, zależy od
obrony powietrznej, od spadających szczątków, od awarii nawigacji i od decyzji
przeciwnika. Niczego z tego nie widać w dostępnych danych. Więcej danych tego
nie zmieni, bo brakuje nie ich ilości, tylko obserwacji innego rodzaju.

## Co system mówi, a czego odmawia

Mówi: które rejony zachodniej Ukrainy zgłaszają teraz alarm, jakiego rodzaju,
jak daleko leżą od polskiej granicy i o której powstał ten obraz.

Odmawia trzech rzeczy, a są to decyzje, nie ograniczenia techniczne:

**Nie podaje prawdopodobieństwa.** Niczego takiego nie liczy.

**Nie mówi, co robić.** Instruują służby państwowe. Ten projekt informuje.

**Nie podaje jednej liczby kilometrów, tylko przedział.** Zapis „0–46 km”
`[przykład]` znaczy, że najbliższa krawędź rejonu leży gdzieś w tym zakresie.
Pojedyncza liczba sugerowałaby dokładność, której nie ma, a fałszywa dokładność
z miejscem po przecinku jest gorsza niż jawnie nazwana niepewność. Odległość
policzono dla 127 obszarów; 5 przedziałów sięga zera, czyli obszar dotyka
granicy, a najbliższy środek obszaru leży 14,2 km od niej.

Jest jeszcze czwarta odmowa, mniej oczywista i najważniejsza ze wszystkich:
**cisza nigdy nie znaczy „bezpiecznie”**. Jeśli zbieranie danych przestanie
działać, strona napisze, że nie wie, co się dzieje, zamiast pokazać pustą mapę.
Pusta mapa i zepsuty system wyglądają tak samo, a znaczą coś przeciwnego, i cała
konstrukcja jest ułożona wokół tego rozróżnienia.

## Czego nie trzeba brać na słowo

Przy prywatnym projekcie wiarygodność waży więcej niż technologia, więc zamiast
zapewnień konkrety. Każdy z nich da się sprawdzić bez pytania autora o zdanie.

**Rejestr błędów ma 160 wpisów.** Każdy mówi, co się zepsuło, dlaczego nikt tego
nie zauważył i jakiej klasy był to błąd. Są tam także wpisy przeciw interesowi
projektu, w tym ten o wyniku 0 na 20 oraz ten, w którym dokumentacja twierdziła,
że coś jest sprawdzane, a nie było. Osobno zapisano **54 decyzje projektowe**,
każdą z warunkiem, który otworzyłby ją z powrotem.

**Część danych zapieczętowano, zanim ktokolwiek je przeczytał.** Odłożono 20,01%
zebranych wiadomości i nikt ich nie otwierał. Nie da się dostroić systemu do
materiału, którego się nie widziało, a tylko wtedy późniejszy wynik cokolwiek
znaczy. Cały korpus ma zapisaną sumę kontrolną i potwierdzoną ciągłość, więc
podmiana albo wycięcie fragmentu są wykrywalne.

**Każda liczba w dokumentacji nosi etykietę pochodzenia:** zmierzona,
raportowana, wywnioskowana, założona. Te 57% wyżej to liczba cudza i jest tak
oznaczona, razem z uwagą, że jej źródło mogło mieć na myśli inny obszar niż ten
projekt.

**Bramka jest jedna i jest maszynowa.** Jedno polecenie uruchamia 937 testów, w
tym 13 scenariuszy ataku na zabezpieczenia samego projektu; pokrycie kodu
wynosi 95,91% przy progu 95%, którego nigdy się nie obniża. Same ataki także są
sprawdzane: 12 z 13 zweryfikowano, psując celowo chronioną przez nie kontrolę i
wymagając, żeby atak to wychwycił. Ten jeden bez takiej weryfikacji jest przy
każdym uruchomieniu wypisywany jako niezweryfikowany, zamiast przemilczany.

**I tutaj ten dokument potknął się o siebie samego.** Cztery liczby wyżej były
nieprawdziwe w wersji 2.4 tego pliku: 87 błędów wobec 118 zapisanych wówczas, 31
decyzji zamiast 45, 410 testów zamiast 642 i pokrycie 96,61% zamiast 95,42%.
Pochodziły z wydania oddalonego o siedemnaście numerów. Tekst wokół nich
przepisano, kiedy zmieniło się źródło danych, liczb nie przeliczył nikt, a
nagłówek dokumentu twierdził, że ktoś to zrobił. Żadna kontrola tego nie
zobaczyła, bo bramka porównywała oba briefy ze sobą i z dwiema wartościami
odniesienia, z których jedna była wyłączona warunkiem odcinającym wszystko
poniżej tysiąca. Błąd przeciw interesowi projektu, w sekcji, której cała treść
to zapewnienie, że liczby są pilnowane. Zapisano go jako F140 i zamknięto
kontrolą, która czyta ten plik liczba po liczbie, porównuje obie wersje językowe
co do wartości i co do krotności, a **zanim pozwolono jej przejść, pokazano ją
jako czerwoną**: sześć celowo wprowadzonych błędów, sześć wychwyconych.

**Zdarzyło się to jeszcze dwa razy, ciszej, i to właśnie ta wersja dokumentu oba
przypadki zapisuje.** Liczby przeliczano przy każdym wydaniu po wprowadzeniu
tamtej kontroli, dokładnie tak, jak miało być, a nagłówek nad nimi dalej
wskazywał wydanie, wobec którego odczytano je kiedyś; zdanie mówiące, skąd
liczba pochodzi, samo jest twierdzeniem, a bramka takiego zdania nie czyta.
Osobno: odpowiedź niżej na pytanie, co by autora zatrzymało, dalej głosiła, że
nie znaleziono polskiego strumienia czytelnego maszynowo, już po tym, jak
projekt taki strumień znalazł, zmierzył, opisał we własnej specyfikacji i zaczął
czytać w stałym rytmie. Tamta naprawa dotarła do specyfikacji i do listy zadań,
a zatrzymała się o jeden dokument przed tym, który czytelnik z zewnątrz otwiera
najpierw. Oba przypadki są wyżej poprawione i zapisane jako F180 i F181. Dla
żadnego nie proponuje się kontroli, bo uczciwą kontrolą jest człowiek czytający
plik jeszcze raz.

## Gdzie to jest teraz, bez upiększeń

Działa: zbieranie danych, rozpoznawanie rejonu z hasztagów, odległość do
granicy, raport, plik zasilający stronę, mapa oraz sama strona, **publicznie
dostępna pod adresem mavo.org.pl od 12 sierpnia 2026 r.** Adres jest tu podany,
bo dokument, który mówi „działa publicznie”, a nie podaje gdzie, prosi o
zaufanie w jedynym miejscu, które czytelnik sprawdziłby w sekundę.

**Od tamtej pory doszły do strony trzy warstwy i jest tu ich miejsce: sekcja
urywająca się na sierpniu to ten sam błąd co liczba urywająca się na sierpniu.**
Polskie komunikaty o zagrożeniu z powietrza rysowane są na wymienionych w nich
województwach, a treść komunikatu otwiera się po dotknięciu. Rezerwacje
przestrzeni powietrznej oznaczone przez polską agencję ruchu lotniczego jako
aktywowane rysowane są obrysem, co mówi o dokumentach, a nie o czymkolwiek, co
lata. Miejsca poza Ukrainą, w których spadł dron, zaznaczono na podstawie
opublikowanych zapisów. Żadna z tych trzech warstw nie zmienia tego, czego
narzędzie odmawia, a każda niesie twierdzenie innego rodzaju niż ukraiński obraz
alarmów i dlatego każda ma własny przełącznik.

18 sierpnia, podczas prawdziwego nalotu, alarm objął osiem zachodnich rejonów w
czterech obwodach, a autor zestawiał wtedy tę stronę z kanałem na bieżąco. To
jedyny raz, kiedy ten przyrząd był oglądany przy pracy, do której powstał, i
**nie spisano z tego żadnego protokołu**. Pliki kontraktowe z tamtej nocy
zachowano, ale odczytanie ich skryptem porównuje przyrząd z jego własnymi
tablicami, więc sam zapis niczego nie dowodzi; oceny zostały w głowie osoby,
która je wydawała. Arkusz, który zamieniłby taką noc na wiersze do sprawdzenia,
istnieje, a dla 18 sierpnia ma wpisane pytania bez odpowiedzi.

Jedna rzecz o tej stronie jest jednak policzona i warto o niej powiedzieć, bo
wcześniej projekt nie miał niczego takiego: **ktoś ją otwiera każdego dnia.**
Nikt jej nie promuje, nikt nie dostaje z niej powiadomień, a odkąd ruch jest
mierzony, liczba wejść utrzymuje się z dnia na dzień na podobnym poziomie. To
jest odpowiedź na pytanie, czy po taki przyrząd ktokolwiek sięga, i pierwsza
odpowiedź twierdząca, jaką ten projekt ma. Z zastrzeżeniem, które należy do
niej, a nie do przypisu: licznik nie odróżnia czytelnika od robota
indeksującego, więc mówi, że coś tę stronę pobiera, a nie że ktoś ją czyta.

Kusi, żeby dopisać do tego zdanie drugie: że w noc ataku ludzie sięgają po nią
częściej. **Z zebranych danych nie da się tego obronić i nie jest to tutaj
twierdzone.** Wzrost z nocy 18 sierpnia nie bierze się z tego, że przyszło
więcej osób, tylko z tego, że ktoś odświeżał, a osobą, która odświeżała tę
stronę przez całą tamtą noc, był autor. Pomiar zaczyna się dopiero w dobie
samego nalotu, więc nie ma spokojnego tła do porównania, i wypada w pierwszych
dniach po publicznym uruchomieniu, kiedy każdy nowy adres ma ruch z samej
nowości. W tym samym okresie zdarzył się dzień zupełnie spokojny, w którym
odwiedzający obejrzeli więcej niż tamtej nocy, oraz doba nalotów, w którą źródło
milczało, a w ruchu nie było widać niczego. Hipoteza do zbadania, nie wynik do
ogłoszenia.

Kolumnę odległości sprawdzono na trzy sposoby, ale tylko jeden z nich jest
źródłem niezależnym: inna geometria i inna metoda dają trzy punkty kontrolne z
dokładnością do 1,1 kilometra. Drugi przelicza ten sam kontur uproszczony
inaczej i daje 0,04 kilometra, czyli sprawdza rachunek, a nie źródło. Trzeci
mierzy, o ile samo źródło może się mylić, o mniej więcej kilometr, i to jest
dolna granica błędu, a nie potwierdzenie.
`[te trzy liczby pochodzą z przeglądu wydania, a nie z bramki]`

Nie działa dobrze: rozpoznawanie **rodzaju** zagrożenia. Znacznik rodzaju
występuje w **19,6% wiadomości**, a po połączeniu go ze stanem alarmu zostaje
**17,0%**. Reszta wyświetla się jako „typ nieznany”, co jest uczciwe, ale nie
jest dobrym wynikiem i nie jest tu tak nazywane. To sufit samego kanału, a nie
parsera: każde proponowane rozszerzenie słownika sprawdzono na pełnym korpusie i
żadne nie dało nowych trafień.

Nie zaczęto tego, co zamienia publiczną stronę w usługę ostrzegania. Nie ma
stanowiska prawnego w sprawie rozsyłania ostrzeżeń osobom, których operator nie
zna, i nie ma żadnego kanału powiadomień: stronę się otwiera, samo nic nie
przychodzi.

Rozmowa z kimś, kto miałby te ostrzeżenia odbierać, odbyła się. Jest tu opisana
w formie, której da się bronić, a nie w tej, w której wygląda lepiej: **rozmowa
się odbyła, protokołu z niej nie ma, więc dopóki nie powstanie, jest to
świadectwo, a nie pomiar.** Tak samo opisana jest tu kontrola z 18 sierpnia i
tak samo oznaczona. Domknięcie tej pozycji wymaga dwóch rozmów i jednej liczby:
przy jakiej częstości alarmów odbiorca przestałby je czytać. Dopóki ta liczba
nie zostanie zapisana, próg alarmu pozostaje ustawiony względem tolerancji,
której nikt nie zmierzył, i tak jest w tym repozytorium opisany.

Korespondencja z instytucjami jest prowadzona i celowo nie jest trzymana w tym
repozytorium: opisuje ludzi, a nie oprogramowanie, a bramka nie wpuszcza takich
plików do drzewa. Ten dokument nie relacjonuje jej stanu i jego milczenia nie
należy czytać jako informacji w żadną stronę.

**Nikt nie dostaje dziś żadnego powiadomienia i nie dostanie, dopóki nie zostaną
zamknięte stanowisko prawne i T11.** Publiczna strona nie jest publiczną usługą
ostrzegania i dokumentacja mówi to tymi słowami.

Daty nie ma i jest to świadome. Naruszenia zdarzają się kilka razy w roku, więc
żaden czterotygodniowy test nie pokaże, czy system je łapie. To właściwość
zjawiska, a nie porażka harmonogramu, a obiecana data byłaby wygodną fikcją.

## Co by autora zatrzymało

Lista spisana z góry, bo tylko wtedy taka lista cokolwiek znaczy.

Jeśli powstanie polski publiczny kanał danych o alarmach, projekt straci sens i
zostanie zamknięty, a nie przestawiony na inny cel. Co liczy się jako taki
kanał, trzeba było zapisać, bo pierwsza odpowiedź była zbyt zgrubna i nie
przetrwała tego, co projekt sam potem odczytał. Przejrzano katalog otwartych
danych: 1 510 768 zasobów, z czego 29 dotyczy ostrzegania, a **strumieni
czytelnych maszynowo jest wśród nich zero**. To nadal jest prawda i nadal jest
wąskie. Obejmuje jeden katalog i dowodzi tego, że nie znaleziono takiego
strumienia tam, gdzie powinien leżeć, a nie tego, że nie istnieje.

**Polski strumień istnieje poza tym katalogiem i ten projekt go czyta.** Usługa
stojąca za aplikacją RSO publikuje swoje strony list w XML i JSON, publicznie i
bez tokenu. Pierwszy odczyt tych danych projekt wykonał 22 sierpnia 2026 r. i od
września czyta je w stałym rytmie; stamtąd biorą się polskie komunikaty rysowane
dziś na mapie. Dane RSO nie są jednak kanałem, który zamknąłby ten projekt, a
powody wypisano właściwość po właściwości w `docs/FEED-SPEC.md`: żaden rekord
nie mówi, do jakiej kategorii należy, żaden nie mówi, który organ go wydał,
zakres nazwany „wszystkie” zwraca część danych, a historia topnieje do garstki
rekordów tygodniowo na cały kraj. **Warunkiem jest więc polski kanał niosący te
właściwości, a nie jakikolwiek polski kanał.** Zapisanie tego w ten sposób
powstrzymuje warunek przed staniem się czymś, czego nic nigdy nie spełni.

Jeśli okaże się, że raportowanie po polsku pomaga komuś kierować ogniem, praca
zostanie wstrzymana. Wygląda to na mało prawdopodobne, bo dane są publiczne i po
ukraińsku dostępne szybciej, ale prawdopodobieństwo nie jest tu argumentem.

Jeśli osoby, dla których to powstaje, powiedzą, że tego nie chcą, projekt się
kończy. Pierwsza taka rozmowa się odbyła i nie została spisana, więc ten warunek
pozostaje niesprawdzony, a nie spełniony.

## Pytania, które warto zadać

Dla kogoś, kto woli sprawdzić, niż uwierzyć na słowo:

*Co się dzieje, kiedy zbieranie danych padnie w środku ataku?* Odpowiedź ma
brzmieć „strona mówi, że nie wie”, a nie „strona wygląda spokojnie”. To jest
sprawdzalne w kodzie i w testach.

*Ile z tych liczb pochodzi z pomiaru, a ile z rozsądnego przypuszczenia?* Każda
ma etykietę. Warto sprawdzić kilka na wyrywki.

*Co ten system robi w noc, kiedy nic się nie dzieje?* Ma mówić „żaden zachodni
rejon nie zgłasza alarmu”, a nie „bezpiecznie”. Różnica nie jest kosmetyczna.

*Czego autor jeszcze nie zmierzył?* Lista jest w repozytorium, podzielona na
trzy poziomy pilności. Bywała dłuższa niż lista rzeczy zrobionych i już nie
jest, a takiej zmiany nic w bramce nie każe nikomu szukać.

*Które liczby w tym dokumencie są pilnowane maszynowo?* Do wersji 2.5 mniej, niż
ten dokument twierdził, i od tego warto zacząć. Bramka porównywała oba briefy ze
sobą wyłącznie dla liczb czterocyfrowych i większych; wszystko poniżej tysiąca
przechodziło bez kontroli i tak zdryfowały cztery liczby w sekcji o kontroli.
Od 2.5 każda zmierzona liczba w tym pliku jest porównywana ze `STATUS.json` co
do wartości, a obie wersje językowe ze sobą co do wartości i co do krotności;
rozjazd wywraca bramkę. Liczby oznaczone jako cudze, jako przykład albo jako
pochodzące z przeglądu wydania nie są pilnowane wcale i jest to przy nich
napisane.

---

**W jednym zdaniu:** MAVO czyta publiczne ukraińskie alarmy powietrzne i
pokazuje po polsku, który przygraniczny rejon jest właśnie pod alarmem i jak
daleko to od granicy; celowo niczego nie przewiduje, bo przy trzech naruszeniach
rocznie żadnej reguły przewidującej nie da się uczciwie obronić; jest w fazie
pre-alfa i nikt nie dostaje jeszcze powiadomień.
