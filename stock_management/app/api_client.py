import httpx
import os
from config import API_URL, HEADERS

class APIClient:
    def __init__(self):
        self.base_url = API_URL
        self.headers = HEADERS

    def get_products(self, search=None):
        params = {}
        if search:
            params["search"] = search
        try:
            r = httpx.get(f"{self.base_url}/products", params=params, headers=self.headers)
            if r.status_code == 200:
                return r.json()
            elif r.status_code == 401:
                print("Error: No autorizado (API_KEY inválida)")
                return None
            else:
                print(f"Error GET products: Status {r.status_code}")
                return None
        except Exception as e:
            print(f"Error de conexión GET products: {e}")
            return None

    def create_product(self, product_data):
        try:
            r = httpx.post(f"{self.base_url}/products", json=product_data, headers=self.headers)
            if r.status_code in [200, 201]:
                return {"success": True, "data": r.json()}
            elif r.status_code == 409:
                return {"success": False, "error": "ALREADY_EXISTS"}
            else:
                print(f"Error POST product: Status {r.status_code} - {r.text}")
                return {"success": False, "error": "SERVER_ERROR"}
        except Exception as e:
            print(f"Error de conexión en create_product: {e}")
            return {"success": False, "error": "CONNECTION_ERROR"}

    def update_product(self, product_id, product_data):
        try:
            r = httpx.put(f"{self.base_url}/products/{product_id}", json=product_data, headers=self.headers)
            if r.status_code == 200:
                return {"success": True, "data": r.json()}
            else:
                return {"success": False, "error": r.text}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def upload_photo(self, product_id, file_name, file_bytes):
        try:
            files = {"file": (file_name, file_bytes)}
            r = httpx.post(f"{self.base_url}/photos/upload/{product_id}", files=files, headers=self.headers)
            return r.json() if r.status_code == 200 else None
        except Exception as e:
            print(f"Error UPLOAD photo: {e}")
            return None

    def delete_product(self, product_id):
        try:
            r = httpx.delete(f"{self.base_url}/products/{product_id}", headers=self.headers)
            return r.status_code == 200
        except Exception as e:
            print(f"Error DELETE product: {e}")
            return False

    def delete_photo(self, photo_id):
        try:
            r = httpx.delete(f"{self.base_url}/photos/{photo_id}", headers=self.headers)
            return r.status_code == 200
        except Exception as e:
            print(f"Error DELETE photo: {e}")
            return False

    def create_movement(self, movement_data):
        try:
            r = httpx.post(f"{self.base_url}/movements", json=movement_data, headers=self.headers)
            if r.status_code == 200:
                return {"success": True, "data": r.json()}
            elif r.status_code == 409:
                return {"success": False, "error": "DUPLICATE_SALES_ID"}
            else:
                return {"success": False, "error": r.text}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def cancel_movement(self, movement_id, reason, is_waste):
        try:
            payload = {"reason": reason, "is_waste": is_waste}
            r = httpx.post(f"{self.base_url}/movements/{movement_id}/cancel", json=payload, headers=self.headers)
            return r.status_code == 200
        except Exception as e:
            print(f"Error cancel_movement: {e}")
            return False

    def get_movements(self):
        try:
            r = httpx.get(f"{self.base_url}/movements", headers=self.headers)
            if r.status_code == 200:
                return r.json()
            else:
                print(f"Error GET movements: Status {r.status_code}")
                return None
        except Exception as e:
            print(f"Error GET movements: {e}")
            return None

    def update_movement_status(self, movement_id, new_status):
        try:
            params = {"new_status": new_status}
            r = httpx.put(f"{self.base_url}/movements/{movement_id}/status", params=params, headers=self.headers)
            return r.status_code == 200
        except Exception as e:
            print(f"Error PUT movement status: {e}")
            return False

    def export_inventory(self, format="csv"):
        try:
            r = httpx.get(f"{self.base_url}/export/inventory", params={"format": format}, headers=self.headers)
            if r.status_code == 200:
                return r.content
            else:
                print(f"Error EXPORT: Status {r.status_code}")
                return None
        except Exception as e:
            print(f"Error EXPORT inventory: {e}")
            return None
