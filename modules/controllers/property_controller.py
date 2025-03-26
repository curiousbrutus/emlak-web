import streamlit as st
from modules.text.text_generation import generate_property_description
from modules.geo.geo_utils import get_nearby_places
from modules.ai.vertex_services import VertexAIService

class PropertyController:
    """Controller for property details and text generation"""
    
    def __init__(self):
        self.vertex_service = VertexAIService()
    
    def show(self):
        """Show property details form and handle text generation"""
        st.header("Emlak Bilgileri")
        
        # Save form inputs to session state
        property_type = st.selectbox(
            "Emlak Tipi:",
            ["Daire", "Villa", "Müstakil Ev", "Arsa", "Ticari", "Diğer"],
            key="property_type"
        )
        
        col1, col2 = st.columns(2)
        
        with col1:
            rooms = st.number_input("Oda Sayısı:", min_value=0, max_value=20, value=3, key="rooms")
            bathrooms = st.number_input("Banyo Sayısı:", min_value=0, max_value=10, value=1, key="bathrooms")
            area = st.number_input("Metrekare:", min_value=1, value=120, key="area")

        with col2:
            price = st.number_input("Fiyat (TL):", min_value=0, value=1500000, key="price")
            year_built = st.number_input(
                "Yapım Yılı:", 
                min_value=1900, 
                max_value=2025, 
                value=2010,
                key="year_built"
            )

        special_features = st.text_area(
            "Özel Özellikler:",
            placeholder="Örnek: Deniz manzarası, yüzme havuzu, güvenlik, otopark vb.",
            key="special_features"
        )

        # Create property data dictionary
        property_data = {
            "property_type": st.session_state.get("property_type", ""),
            "rooms": st.session_state.get("rooms", 0),
            "bathrooms": st.session_state.get("bathrooms", 0),
            "area": st.session_state.get("area", 0),
            "price": st.session_state.get("price", 0),
            "year_built": st.session_state.get("year_built", 0),
            "special_features": st.session_state.get("special_features", ""),
            "address": st.session_state.get("property_location", {}).get("formatted_address", "")
        }

        # Get nearby places if location is available
        nearby_places = None
        if "property_location" in st.session_state:
            location = st.session_state["property_location"]
            
            include_nearby = st.checkbox("Yakın Çevre Bilgilerini Ekle", value=True)
            if include_nearby:
                with st.spinner("Yakın çevre analizi yapılıyor..."):
                    nearby_places = get_nearby_places(
                        location["lat"],
                        location["lng"],
                        radius=1000
                    )

        # Text generation button
        if st.button("Emlak Metni Oluştur", type="primary"):
            with st.spinner("Metin oluşturuluyor..."):
                try:
                    generated_text = self._generate_description(property_data)
                    if generated_text:
                        st.session_state["property_text"] = generated_text
                        st.success("Metin başarıyla oluşturuldu!")
                        st.markdown("### Oluşturulan Metin:")
                        st.write(generated_text)

                        # Allow editing
                        edited_text = st.text_area(
                            "Metni Düzenleyin (isteğe bağlı):", 
                            value=generated_text, 
                            height=200
                        )
                        if edited_text != generated_text:
                            st.session_state["property_text"] = edited_text
                    else:
                        st.error("Metin oluşturulamadı. Lütfen tüm gerekli bilgileri doldurun.")
                except Exception as e:
                    st.error(f"Metin oluşturma hatası: {str(e)}")

    def _generate_description(self, property_data):
        """Generate property description using Vertex AI"""
        try:
            description = self.vertex_service.generate_property_description(property_data)
            if description:
                return description
            else:
                # Fall back to local generation if Vertex AI fails
                return generate_property_description(property_data)
        except Exception as e:
            st.error(f"Vertex AI error: {e}")
            return generate_property_description(property_data)
