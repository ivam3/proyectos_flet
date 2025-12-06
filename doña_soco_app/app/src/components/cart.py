# src/components/cart.py
from typing import List, Dict

# Estructura interna: lista de dicts {id, nombre, precio, cantidad}
_carrito: List[Dict] = []

def get_items() -> List[Dict]:
    return _carrito

def add_item(item_id: int, nombre: str, precio: float, cantidad: int = 1):
    # Si ya existe el item, aumentamos cantidad
    for it in _carrito:
        if it["id"] == item_id:
            it["cantidad"] += cantidad
            return
    _carrito.append({"id": item_id, "nombre": nombre, "precio": float(precio), "cantidad": cantidad})

def remove_item_at(index: int):
    if 0 <= index < len(_carrito):
        _carrito.pop(index)

def remove_item_by_id(item_id: int):
    for i, it in enumerate(_carrito):
        if it["id"] == item_id:
            _carrito.pop(i)
            break

def update_quantity(item_id: int, cantidad: int):
    for it in _carrito:
        if it["id"] == item_id:
            if cantidad <= 0:
                _carrito.remove(it)
            else:
                it["cantidad"] = cantidad
            break

def clear_cart():
    _carrito.clear()

def get_total() -> float:
    return sum(it["precio"] * it["cantidad"] for it in _carrito)
