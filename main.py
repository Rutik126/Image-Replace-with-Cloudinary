# main.py
import streamlit as st
import cloudinary
import cloudinary.uploader
from cloudinary.utils import cloudinary_url
from PIL import Image
import requests
import io
import uuid
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure Cloudinary
cloudinary.config(
    cloud_name=os.getenv("CLOUD_NAME"),
    api_key=os.getenv("API_KEY"),
    api_secret=os.getenv("API_SECRET"),
    secure=True
)

# App title and description
st.title("🖼️ AI-Powered Image Editor")
st.markdown("""
Replace objects in your images using AI. Perfect for e-commerce, marketing, and content creation.
""")

# Custom styles mapped to Cloudinary's supported style parameters
CUSTOM_STYLES = {
    "Realistic": None,  # No style parameter needed for realistic
    "Ghibli Style": "anime",
    "Arcane Style": "arcane",
    "Photorealistic Real Estate Render": "realistic",
    "LoRA-AnimeFusion": "anime",
    "Cyberpunk Tokyo Neon": "cyberpunk",
    "Luxury Interior AI Render": "luxury",
    "AI Fashion Editorial Style": "fashion",
    "Dark Fantasy Realism": "darkfantasy",
    "Pixel Art Generator Trend": "pixel",
    "Synthwave Grid Style": "synthwave"
}

# Sidebar for advanced options
with st.sidebar:
    st.header("Advanced Settings")
    quality = st.slider("Output Quality", 50, 100, 90)
    resolution = st.selectbox("Output Resolution", ["auto", "500", "1000", "2000"])
    format = st.selectbox("Output Format", ["auto", "jpg", "png", "webp"])

# Main app
uploaded_file = st.file_uploader("Upload an image", type=["jpg", "jpeg", "png", "webp"])

if uploaded_file is not None:
    # Generate unique IDs
    unique_filename = f"temp_{uuid.uuid4().hex}.jpg"
    public_id = f"edit_{uuid.uuid4().hex}"

    # Save and display original
    with open(unique_filename, "wb") as f:
        f.write(uploaded_file.getbuffer())
    
    col1, col2 = st.columns(2)
    with col1:
        st.image(unique_filename, caption="Original Image", use_container_width=True)

    # Replacement options
    with col2:
        with st.form("replacement_form"):
            item_to_replace = st.text_input("Item to replace", "sweater")
            replace_with = st.text_input("Replace with", "leather jacket")
            prompt_style = st.selectbox("Style", list(CUSTOM_STYLES.keys()))
            additional_prompt = st.text_input("Additional Style Details (optional)", "")
            submit_button = st.form_submit_button("Generate Replacement")

    if submit_button:
        with st.spinner("Generating your image..."):
            try:
                # Upload to Cloudinary
                upload_result = cloudinary.uploader.upload(
                    unique_filename,
                    public_id=public_id,
                    quality=quality
                )

                # Core gen_replace effect
                effect = f"gen_replace:from_{item_to_replace};to_{replace_with}"

                # Prepare transformation list
                transformation = {
                    "effect": effect,
                    "quality": quality
                }

                # Add style as separate layer if applicable
                transformation_layers = []

                if CUSTOM_STYLES[prompt_style]:
                    transformation_layers.append({"effect": f"style:{CUSTOM_STYLES[prompt_style]}"})

                # Add additional prompt if provided
                if additional_prompt:
                    transformation_layers.append({"effect": f"prompt:{additional_prompt.replace(' ', '_')}"})

                # Add main gen_replace transformation as final layer
                transformation_layers.append(transformation)


                # Generate URL with transformations
                transformed_url, _ = cloudinary_url(
                    public_id,
                    transformation=transformation_layers,
                    width=resolution if resolution != "auto" else None,
                    format=format if format != "auto" else None
                )


                # Fetch and display result
                response = requests.get(transformed_url)
                if response.status_code == 200:
                    transformed_img = Image.open(io.BytesIO(response.content))
                    st.image(transformed_img, caption="Transformed Image", use_container_width=True)
                    
                    # Download button
                    buf = io.BytesIO()
                    transformed_img.save(buf, format="JPEG" if format == "auto" else format.upper())
                    byte_im = buf.getvalue()
                    st.download_button(
                        label="Download Image",
                        data=byte_im,
                        file_name=f"transformed_{public_id}.{format if format != 'auto' else 'jpg'}",
                        mime="image/jpeg"
                    )
                else:
                    st.error(f"Transformation failed (Status Code: {response.status_code}). Please try different parameters.")
                    st.text(f"Debug - Transformation URL: {transformed_url}")

            except Exception as e:
                st.error(f"An error occurred: {str(e)}")
            finally:
                # Clean up
                if os.path.exists(unique_filename):
                    os.remove(unique_filename)