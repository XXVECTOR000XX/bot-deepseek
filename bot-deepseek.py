import time
import ctypes
import keyboard
import os
import sys
import pyperclip
import pygetwindow as gw
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import tkinter as tk
import tkthread

# ---------- Estado global ----------
ventana_hwnd = None
driver = None
ejecucion = True
popup_after_id = None

root = tk.Tk()
root.withdraw()
popup = tk.Toplevel() # Message tool

popup.overrideredirect(True)
popup.wm_attributes("-toolwindow", True)
popup.wm_attributes("-alpha", 0.4)
popup.wm_attributes("-topmost", True)
popup.geometry("300x40+0+" + str( root.winfo_screenheight() - 40 - 40 ) ) # Ancho x Alto + Posición X + Posición Y

popup.configure(bg="white")
popup.withdraw()

etiqueta = tk.Label(
    popup, 
    text= " ",
    bg="white",
    font=("Arial", 10),
    justify="left",
    anchor="w"
)
etiqueta.pack(expand=True, padx=20, pady=2, anchor="w")

# ---------- 1. Iniciar el navegador (requiere login manual) ----------
def iniciar_navegador():
    global driver
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    
    # --- NUEVO: Ruta para guardar el perfil de forma persistente ---
    # Esto crea una carpeta 'perfil_deepseek' junto a tu script
    ruta_perfil = os.path.join(os.getcwd(), "perfil_navegador")
    options.add_argument(f"--user-data-dir={ruta_perfil}")
    # -------------------------------------------------------------

    driver = webdriver.Chrome(options=options)
    driver.get("https://chat.deepseek.com")
    
    # Ya no necesitas el input() si la sesión persiste, 
    # pero puedes dejarlo la primera vez para asegurar el login.
    print("Si es la primera vez, inicia sesión manualmente. Si ya tienes sesión, se cargará automáticamente.")
    # input("Pulsa Enter para continuar...") 

# ---------- 2. Ctrl+G: ocultar/mostrar la ventana ----------
def alternar_ventana():
    global ventana_hwnd
    if ventana_hwnd is None:
        ventanas = gw.getWindowsWithTitle("DeepSeek")
        if not ventanas:
            print("No se encontró la ventana de DeepSeek")
            return
        ventana_hwnd = ventanas[0]._hWnd

    visible = ctypes.windll.user32.IsWindowVisible(ventana_hwnd)
    if visible:
        ctypes.windll.user32.ShowWindow(ventana_hwnd, 0)   # SW_HIDE
        print("Ventana ocultada")
    else:
        ctypes.windll.user32.ShowWindow(ventana_hwnd, 5)   # SW_SHOW
        ctypes.windll.user32.SetForegroundWindow(ventana_hwnd)
        print("Ventana mostrada")

# ---------- 3. Ctrl+R: copiar la última respuesta al portapapeles ----------
def copiar_ultima_respuesta():
    # try:
        # ⚠️ Estos selectores debes ajustarlos según la página real
        respuestas = driver.find_elements(By.CSS_SELECTOR, "[class*='ds-assistant-message-main-content']")
        if not respuestas:
            print("No se encontró contenido de respuesta")
            return
        texto = respuestas[-1].text
        set_text_popup(texto)
        pyperclip.copy(texto)
        print(f"Última respuesta copiada ({len(texto)} caracteres)")
    # except Exception as e:
    #     print(f"Error al copiar: {e}")
        

# ---------- 4. Ctrl+M: enviar el contenido del portapapeles ----------
def enviar_pregunta():
    try:
        texto = pyperclip.paste()
        if not texto.strip():
            print("El portapapeles está vacío")
            return

        # ⚠️ Estos selectores debes ajustarlos según la página real
        caja = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "textarea, [contenteditable='true']"))
        )
        caja.click()
        caja.send_keys(texto)
        time.sleep(0.3)
        caja.send_keys(Keys.RETURN)
        print(f"Enviado: {texto[:50]}...")
    except Exception as e:
        print(f"Error al enviar: {e}")

def  set_text_popup(text):
    @tkthread.called_on_main
    def actualizar_popup(text):
        global popup_after_id
        etiqueta.config(text= text)
            
        # Asegurar que la ventana se muestre al frente
        if popup_after_id:
            popup.after_cancel(popup_after_id)
            popup_after_id = None

        popup.deiconify()
        popup.lift()
        
        popup_after_id = popup.after(3000, popup.withdraw)


    actualizar_popup(text[:50])



def salir():
    global ejecucion
    ejecucion = False

    if driver:
        driver.quit()
    keyboard.unhook_all()
    
    # Detener el mainloop de Tkinter antes de salir
    if root:
        root.quit()   # o root.destroy() si quieres cerrar la ventana ya

    sys.exit(0)

# ---------- Programa principal ----------
if __name__ == "__main__":
    iniciar_navegador()

    keyboard.add_hotkey('ctrl+<', alternar_ventana)
    keyboard.add_hotkey('alt gr + comma', copiar_ultima_respuesta)
    keyboard.add_hotkey('alt gr + m', enviar_pregunta)
    keyboard.add_hotkey('ctrl+q', salir)

    print("Atajos registrados: Ctrl+< ocultar/mostrar | Alt Gr+, copiar última respuesta | Alt Gr+M enviar portapapeles | Ctrl+Q salir")

    try:
        while ejecucion:
            root.update()
            time.sleep(0.01)  
    except SystemExit:
        pass
    finally:
        if driver:
            driver.quit()
            sys.exit(0)