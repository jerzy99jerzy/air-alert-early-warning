# MAVO

**System wczesnego ostrzegania o zagrożeniu z powietrza, budowany po godzinach.
Projekt prywatny, pre-alfa, nikt jeszcze nie dostaje z niego żadnego
powiadomienia.**

Dokument dla czytelnika, który nie pisze kodu.

```
Document:  docs/BRIEF-PL.md, version 2.2
Audience:  a Polish reader without a technical background: a journalist, an
           analyst, a prospective recipient, anyone deciding whether the
           author is careful
Companion: BRIEF (the same document in English), FOUNDATIONS (the same claims
           with provenance labels), METHODOLOGY (the defect log)
Note:      this is the original and the English version follows it. The
           readers this is written for are Polish
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

Z jednego publicznego kanału Telegram, na którym ukraińskie służby ogłaszają
alarmy. Zebrano **61 041 wiadomości ze 118 dni** i to jest cały materiał
dowodowy projektu.

Jedno źródło to poważna słabość i jest w dokumentacji opisana jako taka. Dwa
komercyjne API, które wyglądały na niezależną alternatywę, okazały się czytać
ten sam kanał, więc korzystanie z nich dawałoby złudzenie potwierdzenia bez
potwierdzenia.

Kanał ma jedną cechę, która przesądziła o konstrukcji: **99,3% wiadomości ma
hasztag z nazwą powiatu**, w mianowniku, z podkreśleniami zamiast spacji. To
znaczy, że kanał sam etykietuje swoje wiadomości, a projekt tylko czyta
etykietę. Nie ma tu żadnego uczenia maszynowego ani rozpoznawania nazw w
tekście, bo nie ma czego rozpoznawać.

Pierwsza wersja tego czytnika działała inaczej: szukała nazw obwodów w treści
wiadomości. Sprawdzona na dwudziestu prawdziwych wiadomościach trafiła
**0 razy na 20**. Nie dlatego, że była źle napisana, tylko dlatego, że
zbudowano ją na wyobrażeniu o tym, jak kanał pisze, zamiast na tym, jak pisze
naprawdę. Ten wynik jest w repozytorium zapisany jako defekt z numerem, razem z
wyjaśnieniem, czemu żaden przegląd kodu by go nie znalazł.

## Dlaczego to nie przewiduje przelotu nad granicę

To jest najważniejsza część i jedyna, która wymaga liczb.

Obserwacja, od której projekt się zaczął: każde naruszenie polskiej przestrzeni
w badanym okresie wypadło w noc masowego ataku na zachodnią Ukrainę. Brzmi jak
gotowy predyktor.

Problem: **noce masowych ataków to około 57% dób**. Naruszeń było kilkanaście w
cztery lata, czyli około trzech rocznie.

Zbudujmy z tego najprostszy możliwy system: alarm w każdą noc ataku. Odezwie
się ponad 200 razy w roku i trafi 3 razy. Nie przegapi niczego. I nie powie
nikomu nic, czego nie mówi kalendarz.

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

**Nie podaje jednej liczby kilometrów, tylko przedział.** „0–46 km" znaczy, że
najbliższa krawędź obszaru jest gdzieś w tym zakresie. Jedna liczba
sugerowałaby precyzję, której nie ma, a fałszywa precyzja z przecinkiem
dziesiętnym jest gorsza od jawnej niepewności.

Jest też czwarta odmowa, mniej oczywista i najważniejsza z nich: **cisza nigdy
nie znaczy „bezpiecznie"**. Jeśli zbieranie danych przestanie działać, strona
napisze „nie wiem, co się dzieje", a nie pokaże pustej mapy. Pusta mapa i
zepsuty system wyglądają identycznie, a znaczą coś przeciwnego, i cały układ
jest zbudowany wokół tego rozróżnienia.

## Skąd wiadomo, że autor nie oszukuje sam siebie

To pytanie, które przy prywatnym projekcie jest ważniejsze od technologii,
więc kilka konkretów zamiast zapewnień.

**Log defektów ma 60 wpisów.** Każdy zawiera, co się zepsuło, dlaczego nikt
tego nie zauważył i jaka to klasa błędu. Wpisy przeciw interesowi projektu też
tam są, łącznie z tym o wyniku 0 na 20 i z tym, w którym dokumentacja
twierdziła, że coś jest sprawdzane, a nie było.

**Jest wynik negatywny, zachowany.** Sprawdzano hipotezę, że fazy księżyca mają
związek z atakami dronowymi. Wyszło, że nie mają, i to jest zapisane razem z
liczbami, zamiast po cichu usunięte.

**Część danych została zapieczętowana, zanim ktokolwiek je przeczytał.** Ostatnie
20% zebranych wiadomości jest odłożone i nietknięte. Nie da się dostroić
systemu do dowodów, których się nie widziało - to jedyny sposób, żeby późniejszy
wynik cokolwiek znaczył.

**Każda liczba w dokumentacji ma etykietę pochodzenia:** zmierzone, cudze,
wywnioskowane, założone. Te 57% z akapitu wyżej jest liczbą cudzą i tak jest
oznaczone, łącznie z uwagą, że źródło mogło mieć na myśli inny obszar niż ten
projekt.

## Gdzie to jest teraz, bez upiększeń

Działa: zbieranie danych, rozpoznawanie obszaru z hasztagów, obliczanie
odległości do granicy, raport, plik zasilający stronę internetową i mapę.
Kolumnę odległości sprawdzono na trzy sposoby, ale tylko jeden z nich to
niezależne źródło: inna geometria i inna metoda dają trzy punkty kontrolne w
granicy 1,1 km. Drugi przelicza ten sam kontur inaczej uproszczony i daje 0,04
km, czyli testuje arytmetykę, nie źródło. Trzeci mierzy, jak bardzo źródło samo
w sobie może się mylić, o jakiś kilometr, i to jest podłoga, nie potwierdzenie.

Nie działa dobrze: rozpoznawanie **typu** zagrożenia. Po ostatniej poprawce
system rozpoznaje typ w około 20% alarmów, wcześniej w 13%. Reszta wyświetla
się jako „typ nieznany", i to jest uczciwe wyświetlenie, ale nie jest to dobry
wynik i nie jest tak nazywany.

Nie zaczęte: rzeczy, które decydują o tym, czy to kiedykolwiek trafi do ludzi.
Nie ma stanowiska prawnego wobec rozsyłania ostrzeżeń osobom postronnym i nie
odbyła się ani jedna rozmowa z kimś, kto miałby je dostawać.

**Nikt nie dostaje dziś żadnego powiadomienia i nie dostanie, dopóki tamte dwie
rzeczy się nie wydarzą.**

Nie ma podanej daty i to jest świadome. Naruszenia zdarzają się kilka razy w
roku, więc żaden miesięczny test nie pokaże, czy system je łapie. To
właściwość zjawiska, nie porażka harmonogramu, a obiecana data byłaby wygodną
fikcją.

## Co by autora zatrzymało

Lista spisana z góry, bo tylko wtedy taka lista cokolwiek znaczy.

Jeśli powstanie polski publiczny kanał danych o alarmach, projekt straci sens i
zostanie zamknięty, a nie przepozycjonowany.

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

*Ile z tych liczb pochodzi z pomiaru, a ile z rozsądnego przypuszczenia?*
Każda ma etykietę. Warto sprawdzić kilka losowych.

*Co ten system robi w noc, kiedy nic się nie dzieje?* Ma mówić „żaden zachodni
rejon nie zgłasza alarmu", a nie „bezpiecznie". Różnica nie jest kosmetyczna.

*Czego autor jeszcze nie zmierzył?* Lista jest w repozytorium, ustawiona w trzy
poziomy priorytetu, i jest dłuższa niż lista rzeczy zmierzonych.

---

**TL;DR do przekazania dalej:** MAVO czyta publiczne ukraińskie alarmy
powietrzne i pokazuje po polsku, który przygraniczny rejon jest właśnie pod
alarmem i jak daleko to od granicy; celowo niczego nie przewiduje, bo przy
trzech naruszeniach rocznie żadnej reguły przewidującej nie da się uczciwie
obronić; jest w fazie pre-alfa i nikt jeszcze nie dostaje powiadomień.
