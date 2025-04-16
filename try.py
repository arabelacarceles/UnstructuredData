import base64
from pymongo import MongoClient
from PIL import Image
from io import BytesIO
import matplotlib.pyplot as plt

# Conexión a MongoDB
client = MongoClient("mongodb+srv://arabelacarceles:MongoTest123@cluster0.0wssh1x.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")  # Cambia si usas otro host/puerto
db = client["media_impact_db"]
collection = db["clubs"]

# Buscar un club (ej. Manchester City)
club = collection.find_one({"club_name": "Arsenal FC"})

# Decodificar y mostrar la imagen
if club and "logo_base64" in club:
    logo_data = base64.b64decode(club["logo_base64"])
    image = Image.open(BytesIO(logo_data))
    
    plt.imshow(image)
    plt.axis('off')
    plt.title("Manchester City Logo")
    plt.show()
else:
    print("Logo not found in the document.")
