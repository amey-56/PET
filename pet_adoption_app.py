import os
import streamlit as st
import firebase_admin
from firebase_admin import credentials, db
from PIL import Image
import bcrypt

# Streamlit page configuration (must be first Streamlit command)
st.set_page_config(page_title="Pet Adoption Platform 🐾", layout="wide")

# Initialize Firebase
if not firebase_admin._apps:
    cred = credentials.Certificate("/Users/ameynegandhi/Downloads/pet-pro-d4c5f-firebase-adminsdk-56z4m-07cd971e5f.json")  # Replace with your service account key path
    firebase_admin.initialize_app(cred, {
        "databaseURL": "https://pet-pro-d4c5f-default-rtdb.firebaseio.com/"
    })

# Initialize session state
if "logged_in_user" not in st.session_state:
    st.session_state["logged_in_user"] = None

# Helper Functions
def hash_password(password):
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def verify_password(password, hashed):
    return bcrypt.checkpw(password.encode(), hashed.encode())

def save_image(uploaded_file, filename):
    if not os.path.exists("uploads"):
        os.makedirs("uploads")
    file_path = os.path.join("uploads", filename)
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return file_path

def embed_map(location):
    """Embed Google Maps for the given location."""
    st.markdown(
        f"""
        <iframe
            width="100%"
            height="300"
            style="border:0"
            loading="lazy"
            allowfullscreen
            src="https://www.google.com/maps/embed/v1/place?key=AIzaSyAHGImzRjI4lacl54UpAg_I2YxwbR2Y4_Y&q={location}">
        </iframe>
        """,
        unsafe_allow_html=True
    )

def add_comment(pet_id, comment_text):
    """Add a comment to a specific pet."""
    comments_ref = db.reference(f"comments/{pet_id}")
    commenter = st.session_state["logged_in_user"]["username"]
    comments_ref.push({"commenter": commenter, "text": comment_text})

def view_comments(pet_id):
    """Display comments for a specific pet."""
    comments_ref = db.reference(f"comments/{pet_id}").get()
    if comments_ref:
        st.write("💬 **Comments:**")
        for comment in comments_ref.values():
            st.write(f"🔸 **{comment['commenter']}:** {comment['text']}")
    else:
        st.write("🗨️ No comments yet. Be the first to comment!")

# Authentication
def register():
    st.sidebar.subheader("🚀 Register")
    with st.sidebar.form("register_form"):
        full_name = st.text_input("✨ Full Name")
        username = st.text_input("🔑 Username")
        password = st.text_input("🔒 Password", type="password")
        submit = st.form_submit_button("🎉 Register")

        if submit:
            users_ref = db.reference("users")
            if users_ref.child(username).get():
                st.sidebar.error("❌ Username already exists!")
            else:
                hashed_password = hash_password(password)
                users_ref.child(username).set({"full_name": full_name, "password": hashed_password})
                st.sidebar.success("🎊 Registration successful! Please log in.")

def login():
    st.sidebar.subheader("🔓 Login")
    username = st.sidebar.text_input("🔑 Username")
    password = st.sidebar.text_input("🔒 Password", type="password")
    if st.sidebar.button("🚪 Log In"):
        user_ref = db.reference(f"users/{username}").get()
        if user_ref and verify_password(password, user_ref["password"]):
            st.session_state["logged_in_user"] = {"username": username, "full_name": user_ref["full_name"]}
            st.sidebar.success(f"🎉 Welcome, {user_ref['full_name']}!")
            st.experimental_rerun()
        else:
            st.sidebar.error("❌ Invalid credentials!")

# Pet Management
def add_pet():
    st.subheader("🐾 Add Your Pet")
    with st.form("add_pet_form", clear_on_submit=True):
        name = st.text_input("🐶 Pet's Name")
        pet_type = st.selectbox("🦄 Type of Pet", ["Dog", "Cat", "Bird", "Other"])
        age = st.number_input("🎂 Age (in years)", min_value=0.0, step=0.1)
        description = st.text_area("📜 Description")
        location = st.text_input("📍 Location (City/Address)")
        vaccinated = st.radio("💉 Vaccinated?", ["Yes", "No"])
        images = st.file_uploader("📸 Upload up to 3 Pictures", type=["jpg", "jpeg", "png"], accept_multiple_files=True)
        submit = st.form_submit_button("➕ Add Pet")

        if submit:
            image_paths = []
            for i, image in enumerate(images[:3]):  # Limit to 3 images
                filename = f"{name.lower().replace(' ', '_')}_img{i+1}.jpg"
                image_paths.append(save_image(image, filename))
            
            pet_data = {
                "name": name,
                "pet_type": pet_type,
                "age": age,
                "description": description,
                "location": location,
                "vaccinated": vaccinated,
                "image_paths": image_paths,
                "adopted": False,
                "owner": st.session_state["logged_in_user"]["username"]
            }
            db.reference("pets").push(pet_data)
            st.success(f"🎉 Pet '{name}' added successfully!")

def view_pets():
    st.subheader("🐕 Available Pets")
    pets_ref = db.reference("pets").get()
    if not pets_ref:
        st.write("❌ No pets available!")
        return

    for pet_id, pet in pets_ref.items():
        if not pet.get("adopted"):
            st.markdown(
                f"""
                <div style="border: 2px solid #FF6F61; border-radius: 10px; padding: 20px; background-color: #2B2B2B; color: white; margin-bottom: 20px;">
                    <h3>{pet.get('name')} ({pet.get('pet_type')}) - {pet.get('age')} years</h3>
                    <p><strong>📜 Description:</strong> {pet.get('description')}</p>
                    <p><strong>📍 Location:</strong> {pet.get('location')}</p>
                    <p><strong>💉 Vaccinated:</strong> {pet.get('vaccinated')}</p>
                    <p><strong>👤 Owner:</strong> {pet.get('owner')}</p>
                </div>
                """,
                unsafe_allow_html=True
            )

            # Display pet images
            cols = st.columns(3)
            for i, img_path in enumerate(pet.get("image_paths", [])):
                if os.path.exists(img_path):
                    with cols[i % 3]:
                        st.image(img_path, use_column_width=True)

            # Embed map for location
            embed_map(pet.get("location"))

            # Comments
            with st.form(f"comment_form_{pet_id}", clear_on_submit=True):
                comment_text = st.text_input("🗨️ Add a comment", key=f"comment_{pet_id}")
                comment_submit = st.form_submit_button("💬 Comment")
                if comment_submit and comment_text:
                    add_comment(pet_id, comment_text)
                    st.success("✅ Comment added!")
                    st.experimental_rerun()

            view_comments(pet_id)

            # Mark as adopted
            if st.session_state["logged_in_user"]["username"] == pet["owner"]:
                if st.button(f"✅ Mark '{pet.get('name')}' as Adopted", key=f"adopt_{pet_id}"):
                    db.reference(f"pets/{pet_id}").update({"adopted": True})
                    st.success(f"🎉 '{pet.get('name')}' marked as adopted!")
                    st.experimental_rerun()

# Main Application
st.sidebar.title("🚀 Navigation")

if st.session_state["logged_in_user"] is None:
    login()
    register()
else:
    user = st.session_state["logged_in_user"]
    st.sidebar.write(f"👋 Logged in as: **{user['full_name']}**")
    page = st.sidebar.radio("Go to", ["🏠 Home", "➕ Add a Pet", "🚪 Logout"])

    if page == "🏠 Home":
        view_pets()
    elif page == "➕ Add a Pet":
        add_pet()
    elif page == "🚪 Logout":
        st.session_state["logged_in_user"] = None
        st.experimental_rerun()
