
import tkinter as tk
from tkinter import ttk, messagebox
import requests
from PIL import Image, ImageTk  # For activity images
import io

# API Keys (Replace with your actual keys)
GOOGLE_PLACES_API_KEY = ""
TICKETMASTER_API_KEY = "5PCboFnz3SOHAQMavvP2cqEOloDYh8MQ"
CARBON_INTERFACE_API_KEY = "QcsqZqNgk2pMGCeON7kjKw"

# Constants
ASPECT_RATIO = (19.5, 9)  # iPhone 16 ratio
WINDOW_WIDTH = 450
WINDOW_HEIGHT = int(WINDOW_WIDTH * ASPECT_RATIO[0] / ASPECT_RATIO[1])

class SustainableActivityApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Sustainable Activity Generator")
        self.root.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")

        # Frame for scrollable activities
        self.frame = ttk.Frame(root)
        self.frame.pack(fill=tk.BOTH, expand=True)

        # Scrollable canvas
        self.canvas = tk.Canvas(self.frame)
        self.scrollbar = ttk.Scrollbar(self.frame, orient=tk.VERTICAL, command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)

        self.scrollable_frame.bind(
            "<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.window = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Search and filter options
        self.search_bar = ttk.Entry(root, width=50)
        self.search_bar.pack(pady=10)
        self.search_button = ttk.Button(root, text="Find Activities", command=self.fetch_activities)
        self.search_button.pack()

    def fetch_activities(self):
        query = self.search_bar.get()
        if not query:
            messagebox.showwarning("Input Error", "Please enter an activity or location.")
            return
        
        activities = self.get_google_places(query) + self.get_ticketmaster_events(query)
        self.display_activities(activities)

    def get_google_places(self, query):
        url = f"https://maps.googleapis.com/maps/api/place/textsearch/json?query={query}&key={GOOGLE_PLACES_API_KEY}"
        response = requests.get(url).json()
        places = []
        
        for result in response.get("results", []):
            places.append({
                "name": result.get("name"),
                "location": result.get("formatted_address"),
                "image": result.get("photos", [{}])[0].get("photo_reference"),
                "sustainability": self.get_carbon_footprint()
            })
        
        return places

    def get_ticketmaster_events(self, query):
        url = f"https://app.ticketmaster.com/discovery/v2/events.json?keyword={query}&apikey={TICKETMASTER_API_KEY}"
        response = requests.get(url).json()
        events = []

        if "_embedded" in response:
            for event in response["_embedded"]["events"]:
                events.append({
                    "name": event.get("name"),
                    "location": event.get("_embedded", {}).get("venues", [{}])[0].get("name", "Unknown Location"),
                    "image": event.get("images", [{}])[0].get("url"),
                    "sustainability": self.get_carbon_footprint()
                })
        
        return events

    def get_carbon_footprint(self):
        url = "https://www.carboninterface.com/api/v1/estimates"
        headers = {"Authorization": f"Bearer {CARBON_INTERFACE_API_KEY}", "Content-Type": "application/json"}
        data = {"type": "electricity", "electricity_unit": "kwh", "electricity_value": 10, "country": "US"}  # Example request
        response = requests.post(url, json=data, headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            return result.get("data", {}).get("attributes", {}).get("carbon_kg", "Unknown")
        else:
            return "Error"

    def display_activities(self, activities):
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        for activity in activities:
            frame = ttk.Frame(self.scrollable_frame, padding=10)
            frame.pack(fill=tk.X, expand=True, pady=5)
            
            # Activity Image
            img_label = tk.Label(frame)
            img_label.pack(side=tk.LEFT, padx=10)
            if activity["image"]:
                self.load_image(activity["image"], img_label)
            
            # Activity Details
            text = f"{activity['name']}\n{activity['location']}\nCarbon: {activity['sustainability']} kg CO2"
            label = ttk.Label(frame, text=text, justify=tk.LEFT)
            label.pack(side=tk.LEFT)

    def load_image(self, image_url, label):
        try:
            response = requests.get(image_url)
            img_data = Image.open(io.BytesIO(response.content))
            img_data = img_data.resize((80, 80))  # Resize for UI consistency
            img = ImageTk.PhotoImage(img_data)
            label.config(image=img)
            label.image = img
        except Exception as e:
            print("Image Load Error:", e)

if __name__ == "__main__":
    root = tk.Tk()
    app = SustainableActivityApp(root)
    root.mainloop()
