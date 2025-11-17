"""
Co vidím? - Analyzátor fotografií pomocí Claude AI

Tato aplikace umožňuje nahrát fotografii a pomocí Claude AI získat detailní
popis toho, co je na obrázku zachyceno. Podporuje různé formáty včetně HEIC z iPhonů.
"""

import streamlit as st
import requests
import base64
import os
from dotenv import load_dotenv
from PIL import Image
from pillow_heif import register_heif_opener
import io

# ====================================
# KONFIGURACE A INICIALIZACE
# ====================================

# Načtení proměnných prostředí ze souboru .env
load_dotenv()

# Získání API klíče buď z .env nebo ze Streamlit secrets
# Streamlit secrets mají přednost (pro deployment na Streamlit Cloud)
API_KEY = st.secrets["ANTHROPIC_API_KEY"] if "ANTHROPIC_API_KEY" in st.secrets else os.getenv("ANTHROPIC_API_KEY")
if not API_KEY:
    st.error("Není nastaven API klíč pro Anthropic Claude")
    st.stop()

# Endpoint pro Anthropic Claude API
API_URL = "https://api.anthropic.com/v1/messages"

# Registrace HEIF/HEIC handleru pro podporu Apple formátů obrázků
register_heif_opener()

# ====================================
# UŽIVATELSKÉ ROZHRANÍ
# ====================================

# Konfigurace stránky
st.set_page_config(
    page_title="Analyzátor jídla",
    layout="centered"
)

# Hlavní nadpis aplikace
st.title("Co vidím?")

# Widget pro nahrání souboru - podporuje běžné formáty + HEIC z iPhonů
uploaded_file = st.file_uploader("Nahrajte fotografii", type=['jpg', 'jpeg', 'png', 'heic', 'HEIC'])

# ====================================
# FUNKCE PRO ZPRACOVÁNÍ OBRÁZKŮ
# ====================================

def process_image(uploaded_file):
    """
    Zpracuje nahraný obrázek a připraví ho pro analýzu.

    Funkce zajišťuje:
    1. Podporu různých formátů včetně HEIC
    2. Správnou orientaci podle EXIF metadat
    3. Konverzi do JPEG formátu pro odesílání do API

    Args:
        uploaded_file: Nahraný soubor ze Streamlit file_uploader

    Returns:
        bytes: JPEG data obrázku nebo None při chybě
    """
    try:
        # HEIC/HEIF formáty vyžadují speciální zpracování
        if uploaded_file.type in ['image/heic', 'image/heif']:
            temp_bytes = uploaded_file.getvalue()
            image = Image.open(io.BytesIO(temp_bytes))
        else:
            # Standardní formáty (JPG, PNG)
            image = Image.open(uploaded_file)

        # Kontrola a aplikace správné orientace z EXIF metadat
        # Mnoho fotoaparátů a telefonů ukládá orientaci do EXIF místo fyzické rotace pixelů
        try:
            if hasattr(image, '_getexif'):
                exif = image._getexif()
                if exif is not None:
                    # Tag 274 obsahuje informaci o orientaci
                    orientation = exif.get(274)
                    if orientation is not None:
                        # Rotace obrázku podle EXIF hodnoty:
                        if orientation == 3:    # 180° rotace
                            image = image.rotate(180, expand=True)
                        elif orientation == 6:  # 270° rotace (90° proti směru hodin)
                            image = image.rotate(270, expand=True)
                        elif orientation == 8:  # 90° rotace (90° po směru hodin)
                            image = image.rotate(90, expand=True)

        except Exception as e:
            st.warning(f"Nelze určit orientaci obrázku: {str(e)}")

        # Konverze finálního obrázku do JPEG formátu pro odesílání do API
        with io.BytesIO() as bio:
            # Pokud je to možné, zachováme EXIF metadata
            if 'exif' in image.info:
                image.save(bio, format='JPEG', exif=image.info['exif'])
            else:
                image.save(bio, format='JPEG')
            return bio.getvalue()

    except Exception as e:
        st.error(f"Chyba při zpracování obrázku: {str(e)}")
        return None

# ====================================
# HLAVNÍ LOGIKA APLIKACE
# ====================================

if uploaded_file is not None:
    try:
        # Zpracování nahraného obrázku (rotace, konverze formátu)
        image_data = process_image(uploaded_file)

        # Zobrazení náhledu zpracovaného obrázku
        image = Image.open(io.BytesIO(image_data))
        st.image(image, caption="Náhled obrázku", use_container_width=True)

        # Tlačítko pro spuštění AI analýzy
        if st.button("Chci si přečíst popisek"):
            with st.spinner('Probíhá analýza...'):
                # Převod obrázku do Base64 formátu pro odeslání do API
                base64_image = base64.b64encode(image_data).decode("utf-8")

                # Prompt pro Claude AI - instrukce pro analýzu obrázku
                prompt = """Prohlédni si pozorně následující fotografii: <image> {{IMAGE}} </image> Tvým úkolem je identifikovat nejzajímavější nebo nejpozoruhodnější prvek na této foto[...]
                """

                try:
                    # Hlavičky požadavku pro Anthropic API
                    headers = {
                        "x-api-key": API_KEY,
                        "anthropic-version": "2023-06-01",
                        "content-type": "application/json"
                    }

                    # Tělo požadavku s obrázkem a promptem
                    data = {
                        "model": "claude-3-5-sonnet-20240620",  # Claude 3.5 Sonnet model
                        "max_tokens": 5000,  # Maximální délka odpovědi
                        "messages": [
                            {
                                "role": "user",
                                "content": [
                                    {
                                        "type": "text",
                                        "text": prompt
                                    },
                                    {
                                        "type": "image",
                                        "source": {
                                            "type": "base64",
                                            # Pro HEIC soubory používáme JPEG media type (už jsou konvertované)
                                            "media_type": uploaded_file.type if not uploaded_file.type.startswith('image/heic') else "image/jpeg",
                                            "data": base64_image
                                        }
                                    }
                                ]
                            }
                        ]
                    }

                    # Odeslání požadavku na Claude API
                    response = requests.post(API_URL, headers=headers, json=data)

                    # Zpracování odpovědi
                    if response.status_code == 200:
                        result = response.json()
                        st.success("Analýza dokončena!")
                        # Zobrazení textu z odpovědi Claude AI
                        st.write(result['content'][0]['text'])
                    else:
                        st.error(f"Chyba API: {response.status_code} - {response.text}")

                except Exception as e:
                    st.error(f"Došlo k chybě při analýze: {str(e)}")

    except Exception as e:
        st.error(f"Chyba při zpracování obrázku: {str(e)}")
