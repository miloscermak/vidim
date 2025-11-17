# Co vidím? - Analyzátor fotografií

## 📋 Popis aplikace

**vidim** je webová aplikace postavená na frameworku Streamlit, která využívá umělou inteligenci Claude AI k analýze a popisu fotografií. Aplikace dokáže zpracovat různé formáty obrázků včetně HEIC formátu z iPhonů a poskytnout detailní popis toho, co je na fotografii zachyceno.

## ✨ Klíčové funkce

- **📸 Nahrávání fotografií** - Podporuje formáty: JPG, JPEG, PNG, HEIC
- **🔄 Automatická rotace** - Správně zobrazí fotografie podle EXIF orientace
- **🤖 AI Analýza** - Využívá Claude Sonnet 4.5 model pro detailní popis obsahu fotografie
- **📱 Podpora HEIC** - Plná podpora formátu HEIC z Apple zařízení
- **🖼️ Náhled** - Zobrazení náhledu nahrané fotografie před analýzou

## 🛠️ Technologie

- **Streamlit** - Webový framework pro rychlé vytvoření UI
- **Anthropic Claude API** - AI model pro analýzu obrázků (Claude Sonnet 4.5)
- **Pillow (PIL)** - Zpracování obrázků
- **pillow-heif** - Podpora HEIC/HEIF formátů
- **python-dotenv** - Správa environment proměnných

## 📦 Instalace

1. Naklonujte repozitář:
```bash
git clone <repository-url>
cd vidim
```

2. Nainstalujte závislosti:
```bash
pip install -r requirements.txt
```

3. Nastavte API klíč pro Anthropic Claude:
   - Vytvořte soubor `.env` v kořenovém adresáři
   - Přidejte váš API klíč:
     ```
     ANTHROPIC_API_KEY=your_api_key_here
     ```
   - Nebo nastavte jako Streamlit secret v `.streamlit/secrets.toml`

## 🚀 Spuštění aplikace

```bash
streamlit run streamlit_app.py
```

Aplikace se otevře v prohlížeči na adrese `http://localhost:8501`

## 📖 Jak to funguje

1. **Nahrání fotografie** - Uživatel nahraje fotografii přes file uploader
2. **Zpracování obrázku**:
   - Aplikace detekuje formát obrázku
   - V případě HEIC formátu ho konvertuje na JPEG
   - Načte EXIF metadata a upraví orientaci pokud je potřeba
3. **AI Analýza**:
   - Obrázek se zakóduje do Base64 formátu
   - Odešle se dotaz na Claude API s fotografií
   - Claude AI analyzuje obsah fotografie a vrátí detailní popis
4. **Zobrazení výsledku** - Aplikace zobrazí textový popis toho, co Claude AI na fotografii rozpoznal

## 🔑 Potřebné API klíče

Pro funkčnost aplikace potřebujete:
- **Anthropic API klíč** - Získejte na [console.anthropic.com](https://console.anthropic.com)

## 📝 Struktura projektu

```
vidim/
├── streamlit_app.py     # Hlavní aplikační soubor
├── requirements.txt      # Python závislosti
├── .env                 # Environment proměnné (neverzováno)
└── README.md            # Tento soubor
```

## 🔒 Bezpečnost

- API klíče nikdy necommitujte do repozitáře
- Používejte `.env` soubor nebo Streamlit secrets pro citlivé údaje
- Ujistěte se, že máte `.env` v `.gitignore`

## 🐛 Řešení problémů

### Chyba: "Není nastaven API klíč"
- Zkontrolujte, že máte správně nastavený `ANTHROPIC_API_KEY` v `.env` souboru nebo Streamlit secrets

### Problém s HEIC obrázky
- Ujistěte se, že máte nainstalovanou knihovnu `pillow-heif`
- Na některých systémech může být potřeba dodatečné systémové knihovny

## 📄 Licence

[Přidejte licenci podle vašeho výběru]

## 👤 Autor

[Přidejte informace o autorovi]
