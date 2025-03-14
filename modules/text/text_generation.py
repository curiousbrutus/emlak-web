"""Text generation functions using Google's Gemini model."""

import streamlit as st
import google.generativeai as genai

def generate_property_description(property_data, nearby_places=None):
    """
    Generate a property description using Gemini API.
    
    Args:
        property_data: Dictionary with property information
        nearby_places: List of nearby places of interest
        
    Returns:
        Generated property description or None if failed
    """
    if not st.session_state.get("GEMINI_API_KEY"):
        st.error("Gemini API anahtarı gereklidir!")
        return None
    
    try:
        # Configure Gemini API
        genai.configure(api_key=st.session_state["GEMINI_API_KEY"])
        model = genai.GenerativeModel('gemini-1.5-pro-latest')
        
        nearby_text = ""
        if nearby_places and len(nearby_places) > 0:
            nearby_text = "Yakın çevrede bulunan önemli noktalar:\n"
            for place in sorted(nearby_places, key=lambda x: x['distance'])[:7]:  # Sort by distance and limit
                nearby_text += f"- {place['name']} ({place['type'].replace('_', ' ')}) - {place['distance']} metre\n"
        
        prompt = f"""
        Aşağıdaki bilgilere dayanarak Türkçe dilinde bir emlak ilanı metni oluştur.
        Metin profesyonel, çekici ve bilgilendirici olmalıdır.
        Metin normal bir hızda okunduğunda yaklaşık 45-60 saniye sürmeli (maksimum 600 karakter).
        
        Adres: {property_data['address']}
        Emlak Tipi: {property_data['property_type']}
        Oda Sayısı: {property_data['rooms']}
        Banyo Sayısı: {property_data['bathrooms']}
        Alan: {property_data['area']} m²
        Fiyat: {property_data['price']:,} TL
        Yapım Yılı: {property_data['year_built']}
        Özel Özellikler: {property_data['special_features']}
        
        {nearby_text}
        
        Mevcut Açıklama: {property_data['description']}
        
        Çevredeki alanlardan, konum avantajlarından ve emlağın değerini artıran özelliklerden bahset.
        Lütfen sadece metni döndür, başka açıklama ekleme.
        """
        
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        st.error(f"Metin oluşturma hatası: {str(e)}")
        return None
