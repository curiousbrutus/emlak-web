"""Social media sharing utilities."""

import streamlit as st
import qrcode
import base64
from io import BytesIO
from urllib.parse import quote
import os
from typing import Dict, Optional

def generate_qr_code(url: str, box_size: int = 10) -> str:
    """
    Generate QR code for a URL.
    
    Args:
        url: URL to encode in QR code
        box_size: QR code box size
        
    Returns:
        Base64 encoded image
    """
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=box_size,
        border=4,
    )
    qr.add_data(url)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    
    return img_str

def get_social_share_buttons(url: str, title: str, description: str = None) -> Dict[str, str]:
    """
    Generate HTML for social media sharing buttons.
    
    Args:
        url: URL to share
        title: Content title
        description: Content description
        
    Returns:
        Dictionary with HTML for each platform
    """
    encoded_url = quote(url)
    encoded_title = quote(title)
    encoded_description = quote(description or title)
    
    buttons = {
        "whatsapp": f"""
        <a href="https://api.whatsapp.com/send?text={encoded_title}%20{encoded_url}" 
           target="_blank" style="text-decoration:none;">
            <div style="background-color:#25D366;color:white;padding:8px 12px;
                       border-radius:4px;display:inline-flex;align-items:center;">
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16">
                    <path d="M13.601 2.326A7.854 7.854 0 0 0 7.994 0C3.627 0 .068 3.558.064 7.926c0 1.399.366 2.76 1.057 3.965L0 16l4.204-1.102a7.933 7.933 0 0 0 3.79.965h.004c4.368 0 7.926-3.558 7.93-7.93A7.898 7.898 0 0 0 13.6 2.326zM7.994 14.521a6.573 6.573 0 0 1-3.356-.92l-.24-.144-2.494.654.666-2.433-.156-.251a6.56 6.56 0 0 1-1.007-3.505c0-3.626 2.957-6.584 6.591-6.584a6.56 6.56 0 0 1 4.66 1.931a6.557 6.557 0 0 1 1.928 4.66c-.004 3.639-2.961 6.592-6.592 6.592zm3.615-4.934c-.197-.099-1.17-.578-1.353-.646-.182-.065-.315-.099-.445.099-.133.197-.513.646-.627.775-.114.133-.232.148-.43.05-.197-.1-.836-.308-1.592-.985-.59-.525-.985-1.175-1.103-1.372-.114-.198-.011-.304.088-.403.087-.088.197-.232.296-.346.1-.114.133-.198.198-.33.065-.134.034-.248-.015-.347-.05-.099-.445-1.076-.612-1.47-.16-.389-.323-.335-.445-.34-.114-.007-.247-.007-.38-.007a.729.729 0 0 0-.529.247c-.182.198-.691.677-.691 1.654c0 .977.71 1.916.81 2.049.098.133 1.394 2.132 3.383 2.992.47.205.84.326 1.129.418.475.152.904.129 1.246.08.38-.058 1.171-.48 1.338-.943.164-.464.164-.86.114-.943-.049-.084-.182-.133-.38-.232z"/>
                </svg>
                &nbsp;WhatsApp
            </div>
        </a>
        """,
        
        "telegram": f"""
        <a href="https://t.me/share/url?url={encoded_url}&text={encoded_title}" 
           target="_blank" style="text-decoration:none;">
            <div style="background-color:#0088cc;color:white;padding:8px 12px;
                       border-radius:4px;display:inline-flex;align-items:center;">
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16">
                    <path d="M16 8A8 8 0 1 1 0 8a8 8 0 0 1 16 0zM8.287 5.906c-.778.324-2.334.994-4.666 2.01-.378.15-.577.298-.595.442-.03.243.275.339.69.47l.175.055c.408.133.958.288 1.243.294.26.006.549-.1.868-.32 2.179-1.471 3.304-2.214 3.374-2.23.05-.012.12-.026.166.016.047.041.042.12.037.141-.03.129-1.227 1.241-1.846 1.817-.193.18-.33.307-.358.336a8.154 8.154 0 0 1-.188.186c-.38.366-.664.64.015 1.088.327.216.589.393.85.571.284.194.568.387.936.629.093.06.183.125.27.187.331.236.63.448.997.414.214-.02.435-.22.547-.82.265-1.417.786-4.486.906-5.751a1.426 1.426 0 0 0-.013-.315.337.337 0 0 0-.114-.217.526.526 0 0 0-.31-.093c-.3.005-.763.166-2.984 1.09z"/>
                </svg>
                &nbsp;Telegram
            </div>
        </a>
        """,
        
        "facebook": f"""
        <a href="https://www.facebook.com/sharer/sharer.php?u={encoded_url}" 
           target="_blank" style="text-decoration:none;">
            <div style="background-color:#3b5998;color:white;padding:8px 12px;
                       border-radius:4px;display:inline-flex;align-items:center;">
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16">
                    <path d="M16 8.049c0-4.446-3.582-8.05-8-8.05C3.58 0-.002 3.603-.002 8.05c0 4.017 2.926 7.347 6.75 7.951v-5.625h-2.03V8.05H6.75V6.275c0-2.017 1.195-3.131 3.022-3.131.876 0 1.791.157 1.791.157v1.98h-1.009c-.993 0-1.303.621-1.303 1.258v1.51h2.218l-.354 2.326H9.25V16c3.824-.604 6.75-3.934 6.75-7.951z"/>
                </svg>
                &nbsp;Facebook
            </div>
        </a>
        """,
        
        "twitter": f"""
        <a href="https://twitter.com/intent/tweet?text={encoded_title}&url={encoded_url}" 
           target="_blank" style="text-decoration:none;">
            <div style="background-color:#1DA1F2;color:white;padding:8px 12px;
                       border-radius:4px;display:inline-flex;align-items:center;">
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16">
                    <path d="M5.026 15c6.038 0 9.341-5.003 9.341-9.334 0-.14 0-.282-.006-.422A6.685 6.685 0 0 0 16 3.542a6.658 6.658 0 0 1-1.889.518 3.301 3.301 0 0 0 1.447-1.817 6.533 6.533 0 0 1-2.087.793A3.286 3.286 0 0 0 7.875 6.03a9.325 9.325 0 0 1-6.767-3.429 3.289 3.289 0 0 0 1.018 4.382A3.323 3.323 0 0 1 .64 6.575v.045a3.288 3.288 0 0 0 2.632 3.218 3.203 3.203 0 0 1-.865.115 3.23 3.23 0 0 1-.614-.057 3.283 3.283 0 0 0 3.067 2.277A6.588 6.588 0 0 1 .78 13.58a6.32 6.32 0 0 1-.78-.045A9.344 9.344 0 0 0 5.026 15z"/>
                </svg>
                &nbsp;Twitter
            </div>
        </a>
        """,
    }
    
    return buttons

def show_qr_code_with_download(url: str, title: str = "QR Kod") -> None:
    """
    Display QR code with download button.
    
    Args:
        url: URL to encode in QR code
        title: Title to display above QR code
    """
    qr_img = generate_qr_code(url)
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.markdown(f"## {title}")
        st.markdown(f"""
        <img src="data:image/png;base64,{qr_img}" width="200"/>
        """, unsafe_allow_html=True)
        
        # Download button
        qr_data = f"data:image/png;base64,{qr_img}"
        download_button_str = f"""
        <a href="{qr_data}" download="qr_code.png">
            <button style="background-color:#4CAF50;color:white;padding:8px 16px;
                           border:none;border-radius:4px;cursor:pointer;">
                İndir
            </button>
        </a>
        """
        st.markdown(download_button_str, unsafe_allow_html=True)
    
    with col2:
        st.info(
            "Bu QR kodu tarayarak videoyu mobil cihazlarda izleyebilir veya paylaşabilirsiniz. "
            "QR kodunu indirip basılı materyallerde kullanabilirsiniz."
        )

def show_share_buttons(url: str, title: str, description: Optional[str] = None) -> None:
    """
    Display social share buttons in a Streamlit app.
    
    Args:
        url: URL to share
        title: Content title
        description: Content description
    """
    st.markdown("### Paylaş")
    
    buttons = get_social_share_buttons(url, title, description)
    
    # Display buttons in columns
    cols = st.columns(4)
    for i, (platform, button_html) in enumerate(buttons.items()):
        with cols[i % 4]:
            st.markdown(button_html, unsafe_allow_html=True)
    
    # Display share link
    st.text_input("Doğrudan Link:", value=url, help="Bu linki kopyalayıp paylaşabilirsiniz")
