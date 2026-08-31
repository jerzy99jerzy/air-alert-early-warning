# MAVO

**System wczesnego ostrzegania o zagrożeniu z powietrza, budowany po godzinach.
Projekt prywatny, pre-alfa, nikt jeszcze nie dostaje z niego żadnego
powiadomienia.**

Dokument dla czytelnika, który nie pisze kodu.

```
Document:  docs/BRIEF-PL.md, version 2.4
Measured:  2026-08-31, against STATUS.json at 0.50.0.0. Liczby korpusowe
           poniżej zmierzono 2026-08-17 i nie zmieniły się; zmieniło się
           źródło, i jest to powiedziane w miejscu, w którym się stało
Audience:  a Polish reader without a technical background: a journalist, an
           analyst, a prospective recipient, anyone deciding whether the
           author is careful
Companion: BRIEF (the same document in English), FOUNDATIONS (the same claims
           with provenance labels), METHODOLOGY (the defect log)
Note:      this is the original and the English version follows it. The
           readers this is written for are Polish. Every figure below is
           either pinned in STATUS.json or labelled as somebody else's, as a
           prior measurement, or as an illustration
```

---

## O co chodzi w jednym akapicie

Kiedy nad Ukrainą lecą rakiety albo drony, ukraińskie władze ogłaszają alarmy
dla konkretnych powiatów. Te ogłoszenia są publiczne i pojawiają się
natychmiast. Jeśli mieszkasz w Hrubieszowie, informacja, że alarm właśnie
objął rejon oddalony o 40 kilometrów od Ciebie, jest istotna i dostępna
wcześniej niż cokolwiek, co powie polska strona. MAVO czyta te ogłoszenia i
pokazuje je po polsku: który rejon, jakiego typu zagrożenie, ile kilometrów do
granicy.

To wszystko. Nie przewiduje, czy coś przeleci nad Polskę.

## Skąd to się wzięło

W nocy z 29 na 30 lipca 2026 roku, podczas zmasowanego rosyjskiego ataku
rakietowego na Ukrainę, rosyjski pocisk manewrujący Ch-101 naruszył polską
przestrzeń powietrzną. Wykryto go o 3:40, zniknął z radarów o 3:46, sześć minut
później, i spadł na pole pod Tarnawą-Kolonią w województwie lubelskim, około stu
kilometrów w głąb kraju `[dane zewnętrzne: Dowództwo Operacyjne RSZ za prasą]`.

Sześć minut. W tym oknie najszybszą informacją dla mieszkańca były syreny,
które odzywają się dopiero wtedy, gdy coś już leci w naszą stronę.

Punkt wyjścia dla tego projektu to nie te sześć minut, tylko **godzina, która
je poprzedza**. Ukraińskie alarmy w rejonach przygranicznych są ogłaszane
znacznie wcześniej. Nikt nie podaje ich Polakom w formie, którą da się
przeczytać w trzy sekundy o wpół do czwartej nad ranem.

Jeden szczegół z tamtej nocy należy tu, a nie do przypisu, bo jest
najczytelniejszym opisem tego, czego ten projekt odmawia. Ukraińskie myśliwce
ścigały pociski aż do granicy i próbowały je niszczyć, a ich sygnatura radarowa
była trudna do odróżnienia od samych rakiet, co opóźniło decyzję po polskiej
stronie `[dane zewnętrzne]`. Od tego zależy, czy cokolwiek przekroczy granicę:
od przechwytów, pościgów i decyzji podejmowanych w powietrzu. Żadnej z tych
rzeczy nie ma w feedzie, który ten projekt czyta.

## Skąd dane

**Ta sekcja zmieniła się 30 sierpnia 2026 i ta zmiana jest najbardziej
pouczającą rzeczą w całym dokumencie.**

Do tego dnia źródłem był jeden publiczny kanał Telegram, na którym ukraińskie
służby ogłaszają alarmy. Zebrano z niego **61 041 wiadomości**, ciągłych, bez
luk, z zapisaną sumą kontrolną całości. Pomiary w tym dokumencie nadal
pochodzą z tego korpusu, a konkretnie z okna projektowego, czyli z **99 nocy i
48 540 wiadomości**; reszta to materiał odłożony, o którym niżej.

29 sierpnia 2026 o 04:55 UTC ten kanał przestał publikować. Milczał około
trzydziestu czterech godzin, przez noc nalotów, które inne źródła opisywały
jako ciągłe. Z tym projektem nie stało się nic złego: przez cały ten czas
pisał, że jego obraz jest stary, i podawał, ile ma godzin, bo dokładnie do
tego został zbudowany. Ale system, który rzetelnie melduje własną ślepotę,
nadal jest ślepy, więc następnego dnia źródło przełączono na oficjalne
ukraińskie API alarmowe, które przez cały ten czas działało. Kanał jest dalej
czytany, ale nie jako drugie źródło, tylko jako czujka: jeśli nadawca wróci,
projekt to zauważy i powie, które z dwóch się odezwało.

**Dwa feedy to nie są dwa źródła i to rozróżnienie jest tu sednem.** Oba
czerpią z tej samej góry strumienia, więc ich zgodność mierzy drogę dostawy i
nic poza tym. Jedno źródło to poważna słabość i dokumentacja mówi to wprost,
zamiast to upiększać. Komercyjne API, które wyglądały na niezależną
alternatywę, okazały się czytać ten sam kanał, i właśnie dlatego korzystanie z
nich dawałoby złudzenie potwierdzenia bez potwierdzenia.

Przełączenie kosztowało coś konkretnego i to też jest nazwane, a nie schowane:
API ma jeden typ na wszystko, co lata, więc tam gdzie kanał powiedziałby, co
jest w powietrzu, API często nie mówi. Przez kilka godzin mapa tłumaczyła to
milczenie na „rakietę", co było błędem tego projektu, a nie słowem nadawcy;
teraz takie alarmy mają opis **typ niepodany**, czyli to, co faktycznie
wiadomo.

Kanał miał jedną cechę, która przesądziła o konstrukcji, i to dlatego korpus
opisany niżej jest wart tyle, ile jest wart: **99,3% wiadomości ma hasztag z
nazwą powiatu**, w mianowniku, z podkreśleniami zamiast spacji. To
znaczy, że kanał sam etykietuje swoje wiadomości, a projekt tylko czyta
etykietę. Nie ma tu żadnego uczenia maszynowego ani rozpoznawania nazw w
tekście, bo nie ma czego rozpoznawać. W oknie projektowym jest 127 różnych
hasztagów, z czego **126 rozwiązuje się jednoznacznie** do kodu ukraińskiego
rejestru państwowego.

Pierwsza wersja tego czytnika działała inaczej: szukała nazw obwodów w treści
wiadomości. Sprawdzona na dwudziestu prawdziwych wiadomościach trafiła **0 razy
na 20**. Nie dlatego, że była źle napisana, tylko dlatego, że zbudowano ją na
wyobrażeniu o tym, jak kanał pisze, zamiast na tym, jak pisze naprawdę. Ten
wynik jest w repozytorium zapisany jako defekt z numerem, razem z wyjaśnieniem,
czemu żaden przegląd kodu by go nie znalazł.

Wersja po przebudowie rozwiązuje obszar w **20 wiadomościach na 20** z tej samej
próby prawdziwej treści, a wynik jest przypięty jako asercja, więc nie da się go
po cichu popsuć. Osobno sprawdzono, czy hasztag zgadza się z tym, co wiadomość
mówi prozą: na **38 521 porównywalnych wiadomościach zgodność przekracza 99,99%**.
To jedyny wewnętrzny sposób weryfikacji geokodera, jaki był dostępny bez drugiego
źródła, i jest opisany jako taki, a nie jako niezależne potwierdzenie.

## Dlaczego to nie przewiduje przelotu nad granicę

To jest najważniejsza część i jedyna, która wymaga liczb.

Obserwacja, od której projekt się zaczął: każde naruszenie polskiej przestrzeni
w badanym okresie wypadło w noc masowego ataku na zachodnią Ukrainę. Brzmi jak
gotowy predyktor.

Problem: **noce masowych ataków to około 57% dób** `[liczba cudza, z zewnątrz,
dla okresu i obszaru, których ten projekt nie mierzył]`. Naruszeń było
kilkanaście w cztery lata, czyli około trzech rocznie.

Zbudujmy z tego najprostszy możliwy system: alarm w każdą noc ataku. Odezwie
się ponad 200 razy w roku i trafi 3 razy. Nie przegapi niczego. I nie powie
nikomu nic, czego nie mówi kalendarz.

Jest też liczba własna, zmierzona na tym korpusie, a nie pożyczona. W oknie
projektowym alarm objął całą zachodnią Ukrainę **22 razy**, a liczba
raportowanych naruszeń polskiej przestrzeni w te noce wynosi **zero**. Reguła
budząca ludzi w każdą taką noc miałaby w tym oknie 22 pobudki i 0 trafień. Dla
skali: epizodów alarmowych w zachodnich rejonach jest średnio 5,73 tygodniowo, a
tych obejmujących cały zachód 1,56 tygodniowo.

Można zapytać: czy taki system nie jest jednak odrobinę lepszy niż nic?
Prawdopodobnie tak, odrobinę. **Ale przy trzech zdarzeniach rocznie nie da się
tego wykazać.** Jedna nietypowa noc przechyla cały wynik. To jak twierdzić, że
moneta jest fałszywa, po dwunastu rzutach: może i jest, ale nie na tej
podstawie.

Dlatego w projekcie jest element, którego jedynym zadaniem jest **próba
obalenia każdej proponowanej reguły alarmu**. Sprawdza, o ile reguła bije
kalendarz, i przyjmuje pesymistyczny koniec przedziału ufności, czyli pyta nie
„ile wyszło", ale „ile da się jeszcze twierdzić, jeśli akurat mieliśmy
szczęście". Reguła nie ma prawa nikogo obudzić, dopóki tego nie przejdzie.
Dotąd przeszła jedna, dla zagrożenia rakietowego.

Jest jeszcze powód głębszy niż statystyka. To, czy coś przekroczy granicę,
zależy od obrony powietrznej, spadających szczątków, awarii nawigacji i decyzji
przeciwnika. Żadnej z tych rzeczy nie widać w dostępnych danych. Ilość
informacji tego nie zmieni, bo brakuje nie danych, tylko rodzaju danych.

## Co system mówi, a czego odmawia

Mówi: które rejony zachodniej Ukrainy zgłaszają teraz alarm, jakiego typu, jak
daleko są od polskiej granicy, i o której godzinie ten obraz powstał.

Odmawia trzech rzeczy i to są decyzje, nie ograniczenia techniczne:

**Nie podaje prawdopodobieństwa.** Niczego takiego nie liczy.

**Nie mówi, co robić.** Instruują służby państwowe. Ten projekt raportuje.

**Nie podaje jednej liczby kilometrów, tylko przedział.** Zapis „0-46 km"
`[przykład]` znaczy, że najbliższa krawędź obszaru jest gdzieś w tym zakresie.
Jedna liczba sugerowałaby precyzję, której nie ma, a fałszywa precyzja z
przecinkiem dziesiętnym jest gorsza od jawnej niepewności. Odległość policzono
dla 127 obszarów; 5 przedziałów sięga zera, czyli obszar dotyka granicy, a
najbliższy środek obszaru leży 14,2 km od niej.

Jest też czwarta odmowa, mniej oczywista i najważniejsza z nich: **cisza nigdy
nie znaczy „bezpiecznie"**. Jeśli zbieranie danych przestanie działać, strona
napisze „nie wiem, co się dzieje", a nie pokaże pustej mapy. Pusta mapa i
zepsuty system wyglądają identycznie, a znaczą coś przeciwnego, i cały układ
jest zbudowany wokół tego rozróżnienia.

## Skąd wiadomo, że autor nie oszukuje sam siebie

To pytanie, które przy prywatnym projekcie jest ważniejsze od technologii,
więc kilka konkretów zamiast zapewnień.

**Log defektów ma 87 wpisów.** Każdy zawiera, co się zepsuło, dlaczego nikt
tego nie zauważył i jaka to klasa błędu. Wpisy przeciw interesowi projektu też
tam są, łącznie z tym o wyniku 0 na 20 i z tym, w którym dokumentacja
twierdziła, że coś jest sprawdzane, a nie było. Osobno zapisano **31 decyzji
projektowych**, każdą z warunkiem, który by ją otworzył z powrotem.

**Część danych została zapieczętowana, zanim ktokolwiek je przeczytał.**
Odłożone jest 20,01% zebranych wiadomości i nie zostały otwarte. Nie da się
dostroić systemu do dowodów, których się nie widziało; to jedyny sposób, żeby
późniejszy wynik cokolwiek znaczył. Cały korpus ma zapisaną sumę kontrolną i
potwierdzoną ciągłość, więc podmiana albo wycięcie fragmentu jest wykrywalne.

**Każda liczba w dokumentacji ma etykietę pochodzenia:** zmierzone, cudze,
wywnioskowane, założone. Te 57% z akapitu wyżej jest liczbą cudzą i tak jest
oznaczone, łącznie z uwagą, że źródło mogło mieć na myśli inny obszar niż ten
projekt.

**Bramka jest jedna i jest maszynowa.** Jedno polecenie uruchamia 410 testów,
w tym 13 skryptowanych ataków na własne zabezpieczenia; pokrycie kodu wynosi
96,61% przy podłodze 95%, która nigdy nie jest obniżana. Same ataki też są
sprawdzane: 12 z 13 zweryfikowano tak, że celowo psuto chronioną kontrolę i
wymagano, żeby atak to wykrył. Ten jeden bez takiej weryfikacji jest wypisywany
jako niezweryfikowany przy każdym uruchomieniu, zamiast być przemilczany.

## Gdzie to jest teraz, bez upiększeń

Działa: zbieranie danych, rozpoznawanie obszaru z hasztagów, obliczanie
odległości do granicy, raport, plik zasilający stronę internetową i mapę, oraz
sama strona z mapą, uruchomiona publicznie pod adresem tymczasowym. Adres
docelowy jeszcze nie istnieje, a tymczasowy nie nadaje się do rozsyłania.

Kolumnę odległości sprawdzono na trzy sposoby, ale tylko jeden z nich to
niezależne źródło: inna geometria i inna metoda dają trzy punkty kontrolne w
granicy 1,1 km. Drugi przelicza ten sam kontur inaczej uproszczony i daje 0,04
km, czyli testuje arytmetykę, nie źródło. Trzeci mierzy, jak bardzo źródło samo
w sobie może się mylić, o jakiś kilometr, i to jest podłoga, nie potwierdzenie.
`[te trzy liczby pochodzą z przeglądu wydania, nie z bramki]`

Nie działa dobrze: rozpoznawanie **typu** zagrożenia. Znacznik rodzaju niesie
**19,6% wiadomości**, a po połączeniu go ze stanem alarmu zostaje **17,0%**.
Reszta wyświetla się jako „typ nieznany", i to jest uczciwe wyświetlenie, ale
nie jest to dobry wynik i nie jest tak nazywany. To sufit samego kanału, nie
parsera: każde rozszerzenie słownika testowano na pełnym korpusie i zwracało
zero nowych trafień.

Nie zaczęte: rzeczy, które decydują o tym, czy to kiedykolwiek trafi do ludzi.
Nie ma stanowiska prawnego wobec rozsyłania ostrzeżeń osobom postronnym i nie
odbyła się ani jedna rozmowa z kimś, kto miałby je dostawać.

**Nikt nie dostaje dziś żadnego powiadomienia i nie dostanie, dopóki tamte dwie
rzeczy się nie wydarzą.** Publiczna strona nie jest publiczną usługą
ostrzegania i w dokumentacji jest tak nazwana wprost.

Nie ma podanej daty i to jest świadome. Naruszenia zdarzają się kilka razy w
roku, więc żaden miesięczny test nie pokaże, czy system je łapie. To
właściwość zjawiska, nie porażka harmonogramu, a obiecana data byłaby wygodną
fikcją.

## Co by autora zatrzymało

Lista spisana z góry, bo tylko wtedy taka lista cokolwiek znaczy.

Jeśli powstanie polski publiczny kanał danych o alarmach, projekt straci sens i
zostanie zamknięty, a nie przepozycjonowany. Sprawdzono, czy taki kanał już
istnieje: w polskim katalogu otwartych danych przejrzano 1 510 768 zasobów, z
czego 29 dotyczy ostrzegania, a **strumieni czytelnych maszynowo jest zero**.
Wyszukiwanie było zawężone do jednego katalogu i nie jest dowodem, że nic
takiego nie istnieje nigdzie; jest dowodem, że nie znaleziono go tam, gdzie
powinno leżeć.

Jeśli okaże się, że raportowanie po polsku pomaga komuś kierować ogniem, praca
zostanie wstrzymana. To wygląda na mało prawdopodobne, bo dane są publiczne i
po ukraińsku dostępne szybciej, ale prawdopodobieństwo nie jest tu argumentem.

Jeśli osoby, dla których to jest budowane, powiedzą, że tego nie chcą, projekt
się kończy. Nie zostały jeszcze zapytane i to jest obecnie największa dziura.

## Pytania, które warto zadać

Gdyby ktoś chciał to zweryfikować, a nie przyjąć na słowo:

*Co się dzieje, kiedy zbieranie danych padnie w środku ataku?* Odpowiedź ma
brzmieć „strona mówi, że nie wie", a nie „strona wygląda spokojnie". To jest
sprawdzalne w kodzie i w testach.

*Ile z tych liczb pochodzi z pomiaru, a ile z rozsądnego przypuszczenia?* Każda
ma etykietę. Warto sprawdzić kilka losowych.

*Co ten system robi w noc, kiedy nic się nie dzieje?* Ma mówić „żaden zachodni
rejon nie zgłasza alarmu", a nie „bezpiecznie". Różnica nie jest kosmetyczna.

*Czego autor jeszcze nie zmierzył?* Lista jest w repozytorium, ustawiona w trzy
poziomy priorytetu, i jest dłuższa niż lista rzeczy zmierzonych.

*Które liczby w tym dokumencie są pilnowane maszynowo?* Wszystkie zmierzone
pochodzą z `STATUS.json` i rozjazd między nimi a kodem wywraca bramkę. Liczby
oznaczone jako cudze, przykładowe albo pochodzące z przeglądu wydania nie są
pilnowane i są tak podpisane.

---

**TL;DR do przekazania dalej:** MAVO czyta publiczne ukraińskie alarmy
powietrzne i pokazuje po polsku, który przygraniczny rejon jest właśnie pod
alarmem i jak daleko to od granicy; celowo niczego nie przewiduje, bo przy
trzech naruszeniach rocznie żadnej reguły przewidującej nie da się uczciwie
obronić; jest w fazie pre-alfa i nikt jeszcze nie dostaje powiadomień.
