import streamlit as st
import requests
import base64
import os
from dotenv import load_dotenv
from PIL import Image
from PIL.ExifTags import TAGS
import exifread
from datetime import datetime
from pillow_heif import register_heif_opener
import io

# Načtení proměnných prostředí
load_dotenv()

# Získání API klíče buď z .env nebo ze Streamlit secrets
API_KEY = st.secrets["ANTHROPIC_API_KEY"] if "ANTHROPIC_API_KEY" in st.secrets else os.getenv("ANTHROPIC_API_KEY")
if not API_KEY:
    st.error("Není nastaven API klíč pro Anthropic Claude")
    st.stop()

API_URL = "https://api.anthropic.com/v1/messages"

# Registrace HEIF/HEIC handleru
register_heif_opener()

# Konfigurace stránky
st.set_page_config(
    page_title="Analyzátor jídla",
    layout="centered"
)

# Nadpis
st.title("Co vidím?")

# Upload souboru
uploaded_file = st.file_uploader("Nahrajte fotografii", type=['jpg', 'jpeg', 'png', 'heic', 'HEIC'])

def get_image_metadata(image_file, file_type=None):
    """Funkce pro získání metadat z obrázku"""
    metadata = {}
    
    try:
        # Načtení souboru jako bytes
        image_bytes = image_file.read()
        image_file.seek(0)
        
        if file_type == 'image/heic':
            try:
                from pillow_heif import register_heif_opener, HeifImageFile
                register_heif_opener()
                
                heif_image = HeifImageFile(io.BytesIO(image_bytes))
                
                if 'exif' in heif_image.info:
                    from PIL import ExifTags
                    exif_data = heif_image.getexif()
                    
                    if exif_data:
                        for tag_id in exif_data:
                            tag = ExifTags.TAGS.get(tag_id, tag_id)
                            value = exif_data[tag_id]
                            
                            # Zpracování data
                            if tag == 'DateTime':
                                try:
                                    date_obj = datetime.strptime(str(value), '%Y:%m:%d %H:%M:%S')
                                    metadata['Datum pořízení'] = date_obj.strftime('%d.%m.%Y %H:%M:%S')
                                except Exception as e:
                                    pass
                            
                            # Zpracování GPS
                            if tag == 'GPSInfo':
                                try:
                                    gps_info = value
                                    lat = [float(x)/float(y) for x, y in gps_info[2]]
                                    lon = [float(x)/float(y) for x, y in gps_info[4]]
                                    
                                    lat = lat[0] + lat[1]/60 + lat[2]/3600
                                    lon = lon[0] + lon[1]/60 + lon[2]/3600
                                    
                                    if gps_info[1] == 'S': lat = -lat
                                    if gps_info[3] == 'W': lon = -lon
                                    
                                    metadata['GPS souřadnice'] = f"{lat:.6f}, {lon:.6f}"
                                    metadata['Mapa'] = f"https://www.google.com/maps?q={lat},{lon}"
                                except Exception as e:
                                    pass
                            
                            # Přidání informace o zařízení
                            if tag == 'Model':
                                metadata['Zařízení'] = str(value)
                
            except Exception as e:
                st.error(f"Chyba při čtení HEIC metadat: {str(e)}")
            
    except Exception as e:
        st.error(f"Chyba při čtení metadat: {str(e)}")
    
    return metadata

def convert_to_degrees(value):
    """Pomocná funkce pro převod GPS souřadnic"""
    d = float(value.values[0].num) / float(value.values[0].den)
    m = float(value.values[1].num) / float(value.values[1].den)
    s = float(value.values[2].num) / float(value.values[2].den)
    return d + (m / 60.0) + (s / 3600.0)

def process_image(uploaded_file):
    """Funkce pro zpracování různých formátů obrázků"""
    try:
        if uploaded_file.type in ['image/heic', 'image/heif']:
            # Načtení HEIC souboru
            temp_bytes = uploaded_file.getvalue()
            image = Image.open(io.BytesIO(temp_bytes))
        else:
            image = Image.open(uploaded_file)

        # Kontrola a aplikace orientace z EXIF
        try:
            if hasattr(image, '_getexif'):
                exif = image._getexif()
                if exif is not None:
                    orientation = exif.get(274)  # 274 je tag pro orientaci
                    if orientation is not None:
                        # Rotace podle EXIF orientace
                        if orientation == 3:
                            image = image.rotate(180, expand=True)
                        elif orientation == 6:
                            image = image.rotate(270, expand=True)
                        elif orientation == 8:
                            image = image.rotate(90, expand=True)

        except Exception as e:
            st.warning(f"Nelze určit orientaci obrázku: {str(e)}")

        # Konverze do JPEG pro další zpracování
        with io.BytesIO() as bio:
            # Zachování EXIF dat při ukládání
            if 'exif' in image.info:
                image.save(bio, format='JPEG', exif=image.info['exif'])
            else:
                image.save(bio, format='JPEG')
            return bio.getvalue()

    except Exception as e:
        st.error(f"Chyba při zpracování obrázku: {str(e)}")
        return None

if uploaded_file is not None:
    try:
        # Zpracování obrázku
        image_data = process_image(uploaded_file)
        
        # Zobrazení náhledu
        image = Image.open(io.BytesIO(image_data))
        st.image(image, caption="Náhled obrázku", use_container_width=True)
        
        # Získání metadat
        image_bytes = io.BytesIO(uploaded_file.getvalue())
        metadata = get_image_metadata(image_bytes, uploaded_file.type)
        
        # Zobrazení metadat - pouze jednou a přehledně
        if metadata:
            st.subheader("📸 Údaje o fotografii")
            cols = st.columns(2)
            
            if 'Datum pořízení' in metadata:
                with cols[0]:
                    st.write(f"📅 Pořízeno: {metadata['Datum pořízení']}")
            
            if 'Zařízení' in metadata:
                with cols[1]:
                    st.write(f"📱 Zařízení: {metadata['Zařízení']}")
            
            if 'GPS souřadnice' in metadata:
                st.write(f"📍 Lokace: {metadata['GPS souřadnice']}")
                st.write(f"🗺️ [Zobrazit na mapě]({metadata['Mapa']})")
        
        # Odstraníme všechny debugovací výpisy
        
        # Tlačítko pro analýzu
        if st.button("Chci si přečíst popisek"):
            with st.spinner('Probíhá analýza...'):
                base64_image = base64.b64encode(image_data).decode("utf-8")
                
                prompt = """Prohlédni si pozorně následující fotografii: <image> {{IMAGE}} </image> Tvým úkolem je identifikovat nejzajímavější nebo nejpozoruhodnější prvek na této fotografii. Může to být osoba, předmět, událost, detail nebo cokoliv jiného, co tě zaujme jako nejvíce pozoruhodné. Poté napiš krátký popisek tohoto prvku. Popisek by měl mít následující vlastnosti: - Délka přibližně tři až čtyři věty - Zaměření na to, co činí tento prvek tak zajímavým nebo pozoruhodným - Poskytnutí relevantních detailů, které podporují tvůj výběr jako nejzajímavějšího prvku Pamatuj, že cílem je najít a popsat to opravdu nejpozoruhodnější na celé fotografii. Nesnaž se popsat celou scénu, ale soustřeď se na ten jeden aspekt, který nejvíce vyniká svou zajímavostí nebo neobvyklostí. Svůj popisek napiš v českém jazyce. Začni zajímavě a novinářsky, ne frází typu :"Nejzajímavějším prvkem na fotce ..." a podobně. Začni čtiově, klidně i provokativně. Piš elegantně a chytře.
                """

                try:
                    headers = {
                        "x-api-key": API_KEY,
                        "anthropic-version": "2023-06-01",
                        "content-type": "application/json"
                    }

                    data = {
                        "model": "claude-3-5-sonnet-20241022",
                        "max_tokens": 5000,
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
                                            "media_type": uploaded_file.type if not uploaded_file.type.startswith('image/heic') else "image/jpeg",
                                            "data": base64_image
                                        }
                                    }
                                ]
                            }
                        ]
                    }

                    response = requests.post(API_URL, headers=headers, json=data)
                    
                    if response.status_code == 200:
                        result = response.json()
                        st.success("Analýza dokončena!")
                        st.write(result['content'][0]['text'])
                    else:
                        st.error(f"Chyba API: {response.status_code} - {response.text}")
                    
                except Exception as e:
                    st.error(f"Došlo k chybě při analýze: {str(e)}")

    except Exception as e:
        st.error(f"Chyba při zpracování obrázku: {str(e)}") 
