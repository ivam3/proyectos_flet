# 🚀 Colección de Proyectos con Flet (Python)

Bienvenido a **Proyectos Flet**. Este repositorio actúa como un portafolio centralizado y un espacio de desarrollo para diversas aplicaciones multiplataforma (Móvil, Web y Escritorio) construidas utilizando **Python** y el framework **Flet**.

El objetivo de este repositorio es demostrar la versatilidad de Flet para crear soluciones de software modernas, escalables y visualmente atractivas, abarcando desde sistemas de gestión comercial hasta herramientas de utilidad.

---

## 📂 Proyectos Incluidos

Actualmente, el repositorio alberga los siguientes proyectos:

### 1. 🍽️ Sistema Integral de Pedidos para Restaurantes (White Label)
Una solución completa "Full-Stack" para la gestión de pedidos de comida. Este proyecto nació como una solución personalizada para **"Antojitos Doña Soco"** y ha evolucionado hacia una plantilla de **Marca Blanca (White Label)**, lista para ser implementada en cualquier negocio de comida.

**Características Principales:**
*   **Arquitectura Híbrida:** Frontend en Flet + Backend en FastAPI (SQLite/SQLAlchemy).
*   **Multiplataforma:** Funciona como App Android (APK), Aplicación Web y Software de Escritorio.
*   **Panel de Cliente:** Menú interactivo, carrito de compras persistente, seguimiento de pedidos en tiempo real y descarga de comprobantes PDF.
*   **Panel Administrativo:** Gestión CRUD de menú (con imágenes), actualización de estados de pedidos, configuración del negocio y reportes (CSV/Excel).
*   **Modo Offline/Online:** Detección inteligente de plataforma para manejo de archivos (compatible con Termux/Android).

**Personalización:**
Este proyecto incluye archivos de configuración centralizados (`config.py`) que permiten cambiar el nombre del negocio, horarios y datos de contacto instantáneamente, adaptándose a cualquier marca.

---

## 🔮 Proyectos Futuros
Este repositorio se actualizará periódicamente con nuevas aplicaciones enfocadas en:
*   [ ] Dashboards de análisis de datos.
*   [ ] Herramientas de productividad personal (To-Do, Notas).
*   [ ] Sistemas de punto de venta (POS).
*   [ ] Integraciones con Inteligencia Artificial.

---

## 🛠️ Tecnologías Utilizadas

El stack tecnológico principal de los proyectos en este repositorio incluye:

*   **Lenguaje:** Python 3.10+
*   **Frontend:** [Flet](https://flet.dev/) (Basado en Flutter).
*   **Backend:** FastAPI & Uvicorn.
*   **Base de Datos:** SQLite (Nativo), SQLAlchemy (ORM).
*   **Utilidades:** Pydantic, HTTPX, FPDF, OpenPyXL.

---

## 🚀 Instalación y Configuración General

Para ejecutar cualquiera de los proyectos contenidos aquí, necesitarás tener Python instalado.

1.  **Clonar el repositorio:**
    ```bash
    git clone https://github.com/TU_USUARIO/proyectos_flet.git
    cd proyectos_flet
    ```

2.  **Crear un entorno virtual (Recomendado):**
    ```bash
    python -m venv venv
    # En Windows:
    venv\Scripts\activate
    # En Mac/Linux/Termux:
    source venv/bin/activate
    ```

3.  **Instalar dependencias:**
    Navega a la carpeta del proyecto específico e instala los requisitos:
    ```bash
    pip install -r requirements.txt
    ```

---

## ▶️ Ejecución del Proyecto: Restaurante

Este proyecto requiere ejecutar el Backend y el Frontend simultáneamente.

**1. Iniciar el Backend (Servidor API):**
```bash
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**2. Iniciar la App Flet (Interfaz):**
En una nueva terminal:
```bash
# Desde la raíz de la carpeta del proyecto
# APP WEB/DESKTOP
flet run app/ --web -p 8080 --host 0.0.0.0
```

### 📱 Generación de APK
Si deseas generar el instalador para Android, utiliza una terminal en **Windows o Linux** con Flet instalado y ejecuta:
```bash
flet build apk --module-name main
```
*Nota: Este proceso requiere tener configurado el entorno de desarrollo de Flutter y Android SDK.*

### ⚙️ Personalización (Marca Blanca)
Para adaptar la app a otro negocio, edita los siguientes archivos:
*   `app/src/config.py`: Cambia `APP_NAME` y `COMPANY_NAME`.
*   `backend/config.py`: Cambia el nombre del proyecto en el backend.
*   Ingresa al Panel de Admin (clave por defecto: `zz`) -> Configuración para ajustar horarios, métodos de pago y contacto.

---

## 🤝 Contribución
¡Las contribuciones son bienvenidas! Si tienes una idea para una nueva app en Flet o mejoras para las existentes:
1.  Haz un Fork del repositorio.
2.  Crea una rama (`git checkout -b feature/nueva-app`).
3.  Haz tus cambios y commit.
4.  Abre un Pull Request.

---

## 📄 Licencia
Este repositorio se distribuye bajo la licencia MIT. Eres libre de usar este código para proyectos personales o comerciales.
