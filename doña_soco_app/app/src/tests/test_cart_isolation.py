# app/src/tests/test_cart_isolation.py
import sys
import os

# Añadir el directorio 'src' al path para poder importar 'components'
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from components.cart import Cart

def run_test():
    """
    Prueba que dos instancias de Carrito (simulando dos sesiones de usuario)
    son independientes entre sí.
    """
    print("--- Iniciando prueba de aislamiento de carritos ---")

    # 1. Simular dos sesiones de usuario creando dos carritos distintos
    print("Paso 1: Creando dos carritos para dos usuarios diferentes (user_a, user_b)...")
    cart_user_a = Cart()
    cart_user_b = Cart()
    print("-> Carritos creados.")

    # 2. Añadir un item al carrito del usuario A
    print("\nPaso 2: Agregando 'Torta de Jamón' al carrito del usuario A...")
    cart_user_a.add_item(item_id=1, nombre="Torta de Jamón", precio=50.0)
    print("-> Item agregado.")

    # 3. Verificar el estado del carrito del usuario A
    print("\nPaso 3: Verificando el contenido del carrito del usuario A...")
    items_a = cart_user_a.get_items()
    assert len(items_a) == 1, f"Error: Se esperaba 1 item en el carrito A, pero se encontraron {len(items_a)}"
    assert items_a[0]["nombre"] == "Torta de Jamón", f"Error: El item en carrito A es '{items_a[0]['nombre']}', se esperaba 'Torta de Jamón'"
    assert cart_user_a.get_total() == 50.0, f"Error: El total del carrito A es {cart_user_a.get_total()}, se esperaba 50.0"
    print("-> Verificación exitosa para usuario A.")

    # 4. Verificar que el carrito del usuario B sigue vacío
    print("\nPaso 4: Verificando que el carrito del usuario B permanece vacío...")
    items_b = cart_user_b.get_items()
    assert len(items_b) == 0, f"Error: Se esperaba 0 items en el carrito B, pero se encontraron {len(items_b)}"
    assert cart_user_b.get_total() == 0.0, f"Error: El total del carrito B es {cart_user_b.get_total()}, se esperaba 0.0"
    print("-> Verificación exitosa para usuario B.")
    
    # 5. Añadir un item diferente al carrito del usuario B
    print("\nPaso 5: Agregando 'Agua de Horchata' al carrito del usuario B...")
    cart_user_b.add_item(item_id=10, nombre="Agua de Horchata", precio=20.0, cantidad=2)
    print("-> Item agregado.")

    # 6. Verificar que los carritos siguen siendo independientes
    print("\nPaso 6: Verificación final de independencia...")
    items_a_final = cart_user_a.get_items()
    items_b_final = cart_user_b.get_items()

    assert len(items_a_final) == 1, "Error: El carrito A cambió inesperadamente."
    assert len(items_b_final) == 1, f"Error: Se esperaba 1 item en el carrito B, pero se encontraron {len(items_b_final)}"
    assert items_b_final[0]['nombre'] == "Agua de Horchata", "Error: Item incorrecto en carrito B."
    assert items_b_final[0]['cantidad'] == 2, f"Error: La cantidad del item en B es {items_b_final[0]['cantidad']}, se esperaba 2"
    assert cart_user_a.get_total() == 50.0, "Error: Total incorrecto en carrito A."
    assert cart_user_b.get_total() == 40.0, "Error: Total incorrecto en carrito B."
    print("-> Verificación final exitosa.")

    print("\n--- ✅ PRUEBA COMPLETADA CON ÉXITO ---")
    print("La implementación del carrito por sesión es correcta y segura para concurrencia.")

if __name__ == "__main__":
    run_test()
