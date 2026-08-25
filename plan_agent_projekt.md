# Plan: "AI Agent z ewaluacją" — nowy, mały projekt uzupełniający portfolio

Cel: pokazać dokładnie to, czego nie pokazują RAG_DJANGO i DataLakeProject — agenta
z tool-callingiem, świadomą ewaluację jakości/kosztu/latencji i publiczne, klikalne
demo. Celowo mały scope — kończysz w 2 tygodnie, nie zaczynasz kolejnego
monumentalnego systemu.

Szacowany nakład: 2 tygodnie po godzinach (10-14 wieczorów pracy).

---

## Decyzje projektowe (ustalone z góry, żeby nie tracić czasu na wybór)

- **Framework agenta: LangGraph.** Nie dlatego, że jest technicznie konieczny przy
  3 narzędziach (prosta pętla function-calling by wystarczyła), tylko dlatego że
  "LangGraph" to dosłowne słowo kluczowe, które pojawiało się w ofertach pracy, które
  przeglądaliśmy — warto mieć je w repo i w CV.
- **LLM: Groq**, darmowe, natywnie wspiera tool-use/function-calling. Model:
  `openai/gpt-oss-120b` (Llama 3.3 70B niedostępny na tym koncie Groq — sprawdzone
  przez `client.models.list()`).
  [console.groq.com/docs/tool-use](https://console.groq.com/docs/tool-use/overview)
- **Wyszukiwanie: Tavily** — darmowy tier, 1000 kredytów/miesiąc odnawialnych
  (nie jednorazowo), bez karty. Wystarczy na ~200 sesji demo miesięcznie.
  [coldiq.com/blog/tavily-pricing](https://coldiq.com/blog/tavily-pricing)
- **Kalkulator:** bezpieczna biblioteka do parsowania wyrażeń matematycznych (np.
  `asteval` lub `numexpr`) — **nie** surowy `eval()`, bo to trywialna dziura
  bezpieczeństwa, a "agent z podatnością na code injection" to dokładnie odwrotność
  tego, co chcesz pokazać na rozmowie.
- **Baza wiedzy:** mały, wyselekcjonowany korpus (10-20 dokumentów, np. o Twoim
  własnym CV/projektach albo o jakimś niszowym temacie), embeddingi przez Gemini API
  (spójnie z tym, co ustaliliśmy dla RAG_DJANGO), przechowywane w **DuckDB**
  (rozszerzenie `vss`, indeks HNSW) — jeden plik `.duckdb`, zero zewnętrznej
  infrastruktury. Plik bazy budowany skryptem ingestu i **commitowany do repo**
  (albo odtwarzany przy starcie aplikacji), bo Streamlit Community Cloud ma
  efemeryczny filesystem — nic zapisane w runtime nie przetrwa restartu.
- **Wyniki ewaluacji:** też w DuckDB (osobna tabela/plik `eval/results.duckdb`)
  zamiast CSV — jedna baza, łatwe zapytania SQL do wykresu w README.
- **UI + hosting: Streamlit** (lub Gradio) zamiast pełnego Next.js frontendu —
  celowo prościej niż w RAG_DJANGO, bo to nie jest projekt o budowaniu frontendu,
  tylko o agencie. **Streamlit Community Cloud** hostuje publiczne apki za darmo,
  bezpośrednio z repo GitHub, bez zarządzania serwerem.

---

## Tydzień 1 — Rdzeń agenta

**Dzień 1-2: Szkielet**
- [ ] Repo, `pyproject.toml`/`requirements.txt`, struktura katalogów
      (`agent/`, `tools/`, `eval/`, `tests/`, `app.py`).
- [ ] Klient Groq skonfigurowany, prosty smoke test "hello world" z tool-callingiem.

**Dzień 3: Narzędzia**
- [ ] `tools/search.py` — wrapper na Tavily.
- [ ] `tools/calculator.py` — bezpieczny parser wyrażeń (asteval/numexpr), z obsługą
      błędnych wyrażeń (nie crashuje agenta).
- [ ] `tools/knowledge_base.py` — retrieval z DuckDB (`vss`, HNSW) + embeddingi Gemini.
- [ ] Każde narzędzie ma jasno zdefiniowany JSON schema (opis + parametry) zgodny
      z formatem tool-use Groq/OpenAI.

**Dzień 4: Graf agenta (LangGraph)**
- [ ] Węzły: `reason` (LLM decyduje, czy wywołać narzędzie czy odpowiedzieć) →
      `tool_call` → `observe` → pętla aż do finalnej odpowiedzi (max np. 5 iteracji,
      z twardym limitem, żeby agent nie wpadł w nieskończoną pętlę).
- [ ] Każdy krok loguje: jakie narzędzie, jakie argumenty, jaki wynik — to będzie
      widoczne w demo jako "ślad rozumowania" (bardzo sellable feature: pokazujesz
      nie tylko wynik, ale *jak* agent do niego doszedł).

**Dzień 5: Lokalny harness developerski**
- [ ] Prosty skrypt CLI do zadawania pytań agentowi i podglądu pełnego śladu decyzji
      (przydatne do debugowania i do samego dema).

---

## Tydzień 2 — Testy, ewaluacja, wdrożenie, prezentacja

**Dzień 6-7: Testy + CI**
- [ ] Testy jednostkowe: kalkulator (w tym przypadki brzegowe — dzielenie przez zero,
      nieprawidłowe wyrażenia, próby injection), routing decyzji agenta (zamockowany
      LLM), parsowanie wyników narzędzi.
- [ ] Testy end-to-end: kilka pełnych scenariuszy przez realne API Groq/Tavily —
      **osobny job w CI** (np. uruchamiany ręcznie albo raz dziennie), żeby nie
      zużywać darmowego limitu i nie robić testów niestabilnych (flaky) przy każdym
      pushu.
- [ ] GitHub Actions: `pytest` (testy jednostkowe) na każdy push/PR, zielony badge
      w README.

**Dzień 8-9: Warstwa ewaluacji**
- [ ] Zestaw 15-20 zadań testowych w trzech kategoriach: proste pytania faktograficzne
      (wymaga wyszukiwania), zadania obliczeniowe (wymaga kalkulatora), pytania o
      bazę wiedzy (wymaga retrievalu) — plus kilka wymagających kombinacji narzędzi.
- [ ] Metryki per zadanie: trafność (LLM-as-judge albo exact-match tam, gdzie to
      policzalne, np. wynik kalkulatora), liczba kroków/wywołań narzędzi, koszt
      (tokeny), latencja.
- [ ] Skrypt `eval/run_eval.py` zapisujący wyniki do DuckDB (`eval/results.duckdb`)
      + prosty wykres (matplotlib, dane wyciągnięte zapytaniem SQL) do README —
      analogicznie do tego, co robimy w RAG_DJANGO.

**Dzień 10: UI**
- [ ] Minimalny interfejs Streamlit: pole na pytanie + odpowiedź + rozwijany panel
      "co robił agent" (ślad z Dnia 4).
- [ ] Prosty rate limiting (licznik w `st.session_state` albo zewnętrzny, np. na
      IP) — ochrona limitów Tavily/Groq.

**Dzień 11: Wdrożenie**
- [ ] Streamlit Community Cloud (darmowe, deploy bezpośrednio z GitHub).
- [ ] Sekrety (klucze Groq/Tavily/Gemini) w Streamlit Secrets, nie w repo.
- [ ] Plik `.duckdb` bazy wiedzy zcommitowany do repo (mały, 10-20 dok. — nie
      generujemy go w runtime na efemerycznym filesystemie Streamlit Cloud).
- [ ] Smoke test z obcej sieci/incognito.

**Dzień 12: README**
- [ ] Diagram: narzędzia, przepływ decyzji agenta (graf LangGraph).
- [ ] Sekcja "Decyzje projektowe" — dlaczego LangGraph, dlaczego te narzędzia, jak
      mierzysz jakość (to pokazuje myślenie inżynierskie, nie tylko kod).
- [ ] Tabelka/wykres metryk eval.
- [ ] Link do live demo na górze + 30-60s GIF pokazujący pytanie → ślad decyzji →
      odpowiedź.

**Dzień 13-14: Bufor**
- [ ] Polish, przegląd bezpieczeństwa (brak kluczy w repo, kalkulator nie ma code
      injection), ostateczny smoke test.

---

## Dlaczego ten projekt, a nie kolejny duży system

Masz już dwa projekty pokazujące ciężką infrastrukturę (RAG_DJANGO, DataLakeProject).
Ten ma pokazać coś innego: agentowe rozumowanie z narzędziami, świadomą ewaluację
(nie tylko "działa", ale "wiem jak zmierzyć czy działa dobrze"), i dyscyplinę
inżynierską (testy, CI, bezpieczeństwo) — w mniejszej, w pełni ukończonej formie.
Skończony mały projekt z zielonym CI i działającym demo mówi więcej niż kolejny
świetny, ale nigdy niedokończony w 100% duży system.
