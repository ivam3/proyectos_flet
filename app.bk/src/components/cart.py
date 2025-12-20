from typing import List, Dict

class Cart:
    def __init__(self):
        # Estructura interna: lista de dicts {id, nombre, precio, cantidad}
        self.items: List[Dict] = []

    def get_items(self) -> List[Dict]:
        return self.items

    def add_item(self, item_id: int, nombre: str, precio: float, imagen: str = None, cantidad: int = 1, is_configurable: bool = False):
        # Si ya existe el item, aumentamos cantidad
        for it in self.items:
            if it["id"] == item_id:
                it["cantidad"] += cantidad
                # Update configurable status just in case
                it["is_configurable"] = is_configurable
                return
        self.items.append({
            "id": item_id, 
            "nombre": nombre, 
            "precio": float(precio), 
            "cantidad": cantidad, 
            "imagen": imagen,
            "is_configurable": is_configurable,
            "details": "" 
        })

    def remove_item_at(self, index: int):
        if 0 <= index < len(self.items):
            self.items.pop(index)

    def remove_item_by_id(self, item_id: int):
        for i, it in enumerate(self.items):
            if it["id"] == item_id:
                self.items.pop(i)
                break

    def update_quantity(self, item_id: int, cantidad: int):
        for it in self.items:
            if it["id"] == item_id:
                if cantidad <= 0:
                    self.items.remove(it)
                else:
                    it["cantidad"] = cantidad
                break

    def clear_cart(self):
        self.items.clear()

    def get_total(self) -> float:
        return sum(it["precio"] * it["cantidad"] for it in self.items)
