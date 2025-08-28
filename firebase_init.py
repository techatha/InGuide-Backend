import os
import firebase_admin
from firebase_admin import credentials, storage, firestore

# Initialize (needs to happen in each process)
if not firebase_admin._apps:
    cred = credentials.Certificate("serviceAccountKey.json")
    firebase_admin.initialize_app(cred, {'storageBucket': 'inguide-se953499.appspot.com'})

# Print only once (in the reloader's main process)
if os.environ.get("WERKZEUG_RUN_MAIN") == "true":
    print("Firebase Admin SDK initialized successfully!")

db = firestore.client()
bucket = storage.bucket()