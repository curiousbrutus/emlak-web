import streamlit as st

class PropertyForm:
    """Property details form component"""
    
    def show(self):
        """Display and handle the property form"""
        col1, col2 = st.columns(2)
        
        with col1:
            property_type = st.selectbox(
                "Emlak Tipi:",
                ["Daire", "Villa", "Müstakil Ev", "Arsa", "Ticari", "Diğer"]
            )
            rooms = st.number_input("Oda Sayısı:", min_value=0, max_value=20, value=3)
            bathrooms = st.number_input("Banyo Sayısı:", min_value=0, max_value=10, value=1)
            
        with col2:
            area = st.number_input("Metrekare:", min_value=1, value=120)
            price = st.number_input("Fiyat (TL):", min_value=0, value=1500000)
            year_built = st.number_input(
                "Yapım Yılı:",
                min_value=1900,
                max_value=2025,
                value=2010
            )
            
        special_features = st.text_area(
            "Özel Özellikler:",
            placeholder="Örnek: Deniz manzarası, yüzme havuzu, güvenlik, otopark vb.",
            height=100
        )
        
        return {
            "type": property_type,
            "rooms": rooms,
            "bathrooms": bathrooms,
            "area": area,
            "price": price,
            "year_built": year_built,
            "special_features": special_features,
            "address": st.session_state["property_location"]["formatted_address"]
        }
