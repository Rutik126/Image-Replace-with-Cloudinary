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

# Load environment variables from .env file
load_dotenv()

# Configure Cloudinary using environment variables
cloudinary.config(
    cloud_name=os.getenv("CLOUD_NAME"),
    api_key=os.getenv("API_KEY"),
    api_secret=os.getenv("API_SECRET"),
    secure=True
)

# Streamlit app for replacing items using Cloudinary's Gen Fill
st.title("Image Replace with Cloudinary's Gen Fill")

# Upload image
uploaded_file = st.file_uploader("Upload an image", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    # Generate a unique filename to avoid caching issues
    unique_filename = f"temp_image_{uuid.uuid4().hex}.jpg"

    # Save uploaded file temporarily
    with open(unique_filename, "wb") as f:
        f.write(uploaded_file.getbuffer())

    # Display uploaded image
    st.image(unique_filename, caption="Uploaded Image", use_column_width=True)

    # Input fields for replacing items
    item_to_replace = st.text_input("Item to Replace", "sweater")
    replace_with = st.text_input("Replace With", "leather jacket with pockets")

    # Generate button for replacement
    if st.button("Replace Item"):
        # Upload the image to Cloudinary with a unique public ID
        public_id = f"replace-image-{uuid.uuid4().hex}"
        upload_result = cloudinary.uploader.upload(unique_filename, public_id=public_id)

        # Generate the replacement image URL
        replacement_effect = f"gen_replace:from_{item_to_replace};to_{replace_with}"
        replaced_image_url, _ = cloudinary_url(
            public_id,
            effect=replacement_effect
        )

        # Load images
        original_image = Image.open(unique_filename)

        # Fetch the transformed image from the generated URL
        response = requests.get(replaced_image_url)

        # Check for response status
        if response.status_code == 200:
            transformed_image = Image.open(io.BytesIO(response.content))

            # Display images
            st.subheader("Compare Images")
            col1, col2 = st.columns([1, 1])

            with col1:
                st.image(original_image, caption="Original Image", use_column_width=True)

            with col2:
                st.image(transformed_image, caption="Transformed Image", use_column_width=True)
        else:
            st.error("Failed to fetch the transformed image. Please check your parameters and try again.")

    # Clean up the temporary file
    os.remove(unique_filename)
