[Deutsch](README.de.md) · [English](README.md) · **Polski**

# HEIKO W600 dla Home Assistant

**Vibe-coded:** Projekt powstał z pomocą asystentów programowania opartych na AI. Automatyczne testy nie zastępują fachowej oceny ani sprawdzenia działania z rzeczywistą pompą ciepła.

To **niestandardowa integracja Home Assistant**, a nie dodatek Supervisor. Odbiera dane TCP z modułu W600, udostępnia pomiary i pełny katalog ustawień referencyjnych oraz opcjonalnie przekazuje połączenie do MyHeatPump. Nie wymaga osobnego procesu serwera ani logowania do konta chmurowego.

**Wydanie: 0.6.0.** Rzeczywista komunikacja i wybrane operacje zapisu zostały potwierdzone na jednej pompie HEIKO Thermal 9 z W600: odczyt aktualnych pomiarów, zmiana trybu z potwierdzeniem przez ponowny odczyt ustawień i późniejsza reakcja pompy. Nie oznacza to sprawdzenia wszystkich parametrów ani osobnego testu sprzętowego pakietu 0.6.0. Katalog pochodzi z adaptera HEIKO dla ioBroker i nie jest listą zgodności certyfikowaną przez producenta. Inne sterowniki i wersje oprogramowania mogą nie obsługiwać wszystkich parametrów. [Szczegóły testów i ograniczenia — po angielsku](docs/verification.md).

## Szybki start i instalacja

### Dodaj repozytorium w HACS

Repozytorium jest publiczne i można je dodać jako repozytorium niestandardowe. HACS musi być wcześniej zainstalowany. **Instalacja przez HACS nie została jeszcze przetestowana.** Zweryfikowany pakiet i ręczny sposób instalacji opisano poniżej.

[![Otwórz repozytorium w HACS](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=Zorax24&repository=home-assistant-heiko&category=integration)

Możesz też dodać adres ręcznie:

1. Otwórz **HACS → ⋮ → Repozytoria niestandardowe**.
2. Wklej `https://github.com/Zorax24/home-assistant-heiko`, wybierz kategorię **Integracja** i dodaj repozytorium.
3. Otwórz **HEIKO W600**, pobierz integrację i uruchom ponownie Home Assistant.
4. Otwórz **Ustawienia → Urządzenia i usługi → Dodaj integrację → HEIKO W600**.

Nie dodawaj repozytorium dodatków Supervisor. Ten sposób nie wymaga obecności projektu na domyślnej liście HACS, ale rzeczywisty test instalacji przez HACS pozostaje do wykonania.

### Instalacja bez HACS — trzy kroki

Najpierw utwórz kopię zapasową Home Assistant. Przy aktualizacji zachowaj również poprzedni folder integracji.

1. [Pobierz instalacyjny plik ZIP](https://github.com/Zorax24/home-assistant-heiko/releases/download/v0.6.0/heiko_w600-ha-0.6.0.zip) i rozpakuj go.
2. Skopiuj zawarty w nim folder `custom_components/heiko_w600` do `/config/custom_components/` na urządzeniu z Home Assistant.
3. Uruchom ponownie Home Assistant, a następnie kliknij [Dodaj HEIKO W600](https://my.home-assistant.io/redirect/config_flow_start/?domain=heiko_w600) lub otwórz **Ustawienia → Urządzenia i usługi → Dodaj integrację**.

Plik manifestu powinien znajdować się pod ścieżką `/config/custom_components/heiko_w600/manifest.json`. Niektóre edytory nazywają katalog `/config` jako `/homeassistant`. Użyj instalacyjnego ZIP z wydania, a nie archiwum kodu źródłowego GitHub. Suma kontrolna znajduje się w [wydaniach](https://github.com/Zorax24/home-assistant-heiko/releases).

## Połączenie z pompą ciepła

Wymagania: Home Assistant od wersji 2026.9.4 (testowano z 2026.9.4), W600 korzystający z referencyjnego protokołu TCP oraz działające połączenie LAN lub VPN. Instalacja ZIP wymaga dostępu do katalogu konfiguracji HA.

1. Podczas konfiguracji integracji pozostaw adres nasłuchiwania `0.0.0.0` i port TCP `8899`, jeżeli port jest wolny. Świadomie wybierz, czy chcesz przekazywać dane do MyHeatPump.
2. W istniejącej konfiguracji klienta TCP modułu W600 ustaw **adres Home Assistant osiągalny z sieci LAN lub VPN modułu** oraz port `8899` albo inny wybrany port. Przed zmianą zapisz poprzedni adres i port docelowy W600.
3. Poczekaj na aktualne pomiary i ustawienia, następnie utwórz panel zgodnie z instrukcją poniżej.

To **W600 nawiązuje połączenie z Home Assistant**. Adres `0.0.0.0` służy do nasłuchiwania i nigdy nie jest adresem docelowym W600. Port interfejsu WWW HA `8123` obsługuje inną usługę. **Nie udostępniaj portu nasłuchiwania w internecie.** Referencyjny adres producenta to `www.myheatpump.com:18899`; można go zmienić w konfiguracji integracji. [Szczegóły sieci, W600, Docker i VPN — po angielsku](docs/network.md).

Elementy sterowania są dostępne dopiero po odebraniu aktualnych, zweryfikowanych ustawień. Samo połączenie TCP nie dowodzi poprawnego odbioru danych.

## Języki

Konfiguracja, opcje, nazwy encji, wartości wyboru, komunikaty, akcje i eksport panelu są dostępne po polsku, niemiecku i angielsku. Home Assistant używa języka systemowego do domyślnych nazw encji. Własne nazwy użytkownika pozostają zachowane. Eksport panelu obsługuje `pl`, `de` i `en`; bez wskazania języka używa języka systemowego HA, a dla innych języków angielskiego. Istniejące panele mają stałe napisy i nie są automatycznie zastępowane. Tłumaczenia korzystają z [oficjalnego mechanizmu Home Assistant](https://developers.home-assistant.io/docs/internationalization/custom_integration/).

## Funkcje i codzienna obsługa

- Temperatury zasilania, powrotu, zewnętrzna i ciepłej wody, stany sprężarki i pomp oraz inne przypisane pomiary. Nieznane, nieprawidłowe i nieaktualne odczyty nie są zastępowane wymyślonymi wartościami.
- **128 nazwanych parametrów**, w tym **125 elementów umożliwiających zapis** i trzy wartości wersji tylko do odczytu. Liczba encji może zależeć od ustawień rejestru i nie jest gwarancją zgodności urządzenia.
- Ustawienia codzienne: włączanie i wyłączanie, tryb pracy, zadana temperatura pomieszczenia i ciepłej wody oraz przesunięcie krzywej grzewczej.
- Widok **Wszystkie ustawienia** obejmuje również parametry serwisowe i ochronne. Mogą wpływać na ochronę przed zamarzaniem, obciążenia elektryczne, dezynfekcję ciepłej wody, zawory, pompy i suszenie jastrychu. Przed zmianą skonsultuj się z wykwalifikowanym serwisantem. Zakres z katalogu nie dowodzi, że każda wartość jest bezpieczna dla Twojej instalacji.
- Akcje żądania pomiarów i ustawień wysyłają zapytania odczytu; nie zmieniają parametrów.
- Zapisy wykonywane są kolejno i wymagają aktualnych ustawień. Żądana wartość jest potwierdzana dopiero przez nową, zgodną ramkę ustawień CMD02. Przekroczenie czasu oznacza **nieznany wynik po stronie urządzenia**: przed ponowieniem sprawdź aktualną wartość.
- Kontrola CRC i identyfikacji, kontrola wieku danych, ograniczona obsługa ramek, ponowne połączenia i diagnostyka ograniczająca ujawnianie danych prywatnych.

Tryby i wartości wyboru pochodzą z katalogu; ich faktyczna dostępność zależy od sterownika. Integracja nie jest termostatem typu `climate` i nie oblicza COP ani sum energii.

Stany pomp i sprężarki to **Włączone/Wyłączone**. **Niedostępne** oznacza brak aktualnego poprawnego odczytu, a nie wyłączenie urządzenia. Przełączniki funkcji i zezwoleń określają możliwość pracy; nie potwierdzają, że pompa lub ogrzewanie właśnie pracują.

## Utwórz własny panel

1. Otwórz **Narzędzia deweloperskie → Akcje**; nazwa i położenie tego obszaru mogą zależeć od wersji HA.
2. Wybierz akcję generowania panelu pompy ciepła: `heiko_w600.export_dashboard`.
3. Wybierz język `pl`. W trybie YAML użyj:

   ```yaml
   action: heiko_w600.export_dashboard
   data:
     language: pl
   ```

4. Wykonaj akcję i skopiuj YAML **z wnętrza pola odpowiedzi `yaml`**. Pomiń zewnętrzną linię tego pola i usuń dodatkowe wcięcie dwóch spacji.
5. W **Ustawienia → Panele** utwórz **nowy pusty panel**. Przejdź do edycji, otwórz menu panelu i edytor konfiguracji YAML, wklej zawartość i zapisz.

Eksport korzysta z rzeczywistych encji w Twoim rejestrze, również po zmianie ich identyfikatorów. Pomija wyłączone encje i zachowuje własne nazwy. **Sam nie zapisuje ani nie nadpisuje żadnego panelu.** Tworzy trzy widoki: Przegląd, Wszystkie ustawienia oraz Pomiary i diagnostyka. Krótkie etykiety nie powtarzają stale nazwy urządzenia. Aby zmienić język lub zastosować nowe etykiety po aktualizacji, wykonaj ponowny eksport; istniejące napisy są statyczne.

## Włączanie i wyłączanie przekazywania do MyHeatPump

Przełącznik przekazywania do MyHeatPump jest dostępny w panelu i wśród encji konfiguracyjnych integracji, nawet przed połączeniem W600. Wybrany stan jest zapisywany i pozostaje po restartach oraz zmianach opcji.

- **Włączone:** cały strumień bajtów TCP z W600 trafia do skonfigurowanego serwera producenta. Odpowiedzi i polecenia producenta wracają do urządzenia. Strumień może zawierać identyfikatory urządzenia, pomiary, stany pracy i ustawienia. Polecenia producenta mogą zmieniać pracę pompy. Integracja nie dodaje danych logowania do konta, nie filtruje poszczególnych pól i nie szyfruje referencyjnego transportu TCP.
- **Wyłączone:** integracja zamyka istniejące połączenie z producentem i nie otwiera kolejnego. Poprawne lokalne ramki CMD01/CMD02 otrzymują lokalne potwierdzenia CMD03/CMD04. Zaimplementowano lokalne odczyty, zapytania i zapisy z aktualnym potwierdzeniem odczytem. Funkcje zdalne MyHeatPump przestają otrzymywać ten strumień. Wyłączenie nie usuwa danych zapisanych wcześniej u producenta. Rzeczywiste zachowanie urządzenia w tym trybie nie zostało potwierdzone dla tego wydania.

Zmiana przełącznika sama nie ustawia parametru pompy i zachowuje połączenie W600. Istniejące instalacje zachowują zapisany stan. Gdy stan ze starszej wersji nie istnieje, domyślnie przyjmowane jest **włączenie**, zgodnie z wersją 0.4.0. Zapisany wybór nie jest zmieniany bez wiedzy użytkownika.

## Aktualizacje, kopie zapasowe i powrót do poprzedniej wersji

Przed aktualizacją wykonaj kopię HA, wyeksportuj własne panele i zachowaj poprzedni folder integracji. Przeczytaj [historię zmian](CHANGELOG.md), zwłaszcza zmiany stanów używanych w automatyzacjach od 0.5.1. Zastąp tylko cały folder `/config/custom_components/heiko_w600` nową wersją i uruchom ponownie HA. Przy zwykłej aktualizacji nie usuwaj i nie dodawaj ponownie integracji: domena, identyfikatory konfiguracji i unikalne identyfikatory encji pozostają zachowane.

Aby wrócić do poprzedniej wersji, przywróć wcześniejszy folder integracji oraz, jeśli potrzeba, panel, a następnie uruchom ponownie HA. Jeśli trzeba także cofnąć zmiany konfiguracji, przywróć kopię zapasową HA.

## Usuwanie integracji

Jeśli W600 korzysta z serwera tej integracji, najpierw przywróć mu działający adres docelowy. Usuń integrację w **Urządzenia i usługi**, usuń folder jej komponentu i uruchom ponownie HA. Usuń odwołania do encji z paneli i automatyzacji. Usunięcie integracji nie cofa parametrów pompy i nie usuwa danych z serwerów producenta.

## Rozwiązywanie problemów

| Objaw | Co sprawdzić |
|---|---|
| Oczekiwanie na pompę | Adres docelowy klienta TCP W600, osiągalność przez LAN/VPN, zgodność portów i reguły zapory. |
| Serwer nasłuchujący nie uruchamia się | Zajęty port, adres nasłuchiwania nieobecny na komputerze HA lub brak uprawnień. Wybierz wolny port i ustaw ten sam w W600. |
| Brak pomiarów / niedostępne | Samo połączenie TCP nie wystarcza. Potrzebne są aktualne, poprawnie adresowane ramki CMD01 i CMD02. Sprawdź wiek danych i liczniki. |
| Chmura niedostępna | Adres serwera i możliwość nawiązania wychodzącego połączenia TCP. Lokalna sesja W600 pozostaje otwarta, ale przy włączonym przekazywaniu lokalne automatyczne potwierdzenia nie zastępują chmury. |
| Zapis niepotwierdzony | Sprawdź aktualne ustawienia. Nie ponawiaj stale zapisu ani nie zakładaj, że wartość w urządzeniu pozostała bez zmian. |
| Brak integracji po skopiowaniu | Dokładna ścieżka folderu, pełna zawartość pakietu i logi HA. Uruchom ponownie HA i odśwież pamięć podręczną przeglądarki. |

## Diagnostyka i zgłoszenia

Podaj wersję HA, wersję integracji i znane informacje o modelu, sterowniku lub oprogramowaniu bez identyfikatorów prywatnego urządzenia. W menu integracji pobierz diagnostykę. Eksport pomija skonfigurowane adresy i porty, identyfikatory konta i urządzenia, surowe ramki oraz rzeczywiste temperatury i wartości ustawień. Zawiera wersję oprogramowania, wiek i liczniki danych oraz stany połączenia i chmury.

Przejrzyj każdy załącznik przed udostępnieniem. Nie publikuj haseł, tokenów, surowego ruchu sieciowego, zrzutów ekranu z prywatnymi danymi ani pełnych numerów seryjnych i adresów MAC.

## Testy, HACS i licencja

Pakiet 0.6.0 przeszedł 63 automatyczne testy jednostkowe i symulacyjne, testy w izolowanym Home Assistant Core 2026.9.4, kontrolę struktury archiwum oraz lokalną kontrolę danych prywatnych. Testy obejmują trzy języki, eksport panelu, zapisywanie opcji chmury i błędy zajętego portu. To nie jest dodatkowy test wszystkich funkcji na fizycznej pompie. [Dokładny zakres i ograniczenia — po angielsku](docs/verification.md).

**Obsługiwany sposób instalacji to ręczna instalacja ZIP.** Repozytorium zawiera `hacs.json` i ma strukturę zgodną z [wymaganiami HACS dla integracji](https://www.hacs.dev/docs/publish/integration/). **Instalacja przez HACS nie została zweryfikowana.** Projekt nie został dodany do domyślnej listy HACS ani Home Assistant Brands. Same metadane i poprawny test Hassfest nie potwierdzają instalacji przez HACS.

Licencja MIT: [LICENSE](LICENSE). [Informacje o pochodzeniu kodu](THIRD_PARTY_NOTICES.md) opisują referencyjny adapter ioBroker. Projekt jest niezależny od producenta i nie deklaruje certyfikacji urządzeń. Dla programistów: [powtarzalny proces budowania i testy — po angielsku](docs/development.md).
