# Configurar Actualización Automática en Raspberry Pi

## Paso 1: Dar permisos sudo sin contraseña para reiniciar servicio

Desde la Raspberry Pi (por SSH), ejecuta:

```bash
sudo visudo
```

Al final del archivo, agrega esta línea:

```
ocalab ALL=(ALL) NOPASSWD: /bin/systemctl restart engastado.service
```

**Cómo guardar en visudo:**
1. Presiona `Ctrl + X`
2. Presiona `Y` (yes)
3. Presiona `Enter`

---

## Paso 2: Verificar que funciona

Prueba ejecutar sin contraseña:

```bash
sudo systemctl restart engastado.service
```

Si no pide contraseña, ¡está configurado correctamente!

---

## Cómo usar la actualización automática

### Desde el navegador (en la Raspberry o desde cualquier PC en la red):

1. Ve a: `http://192.168.1.108:5000/admin`
2. Baja hasta la sección **"🔄 Actualización del Sistema"**
3. Click en **"🔍 Comprobar Actualizaciones"** para ver si hay cambios
4. Si hay actualizaciones, click en **"⬇️ Actualizar Ahora"**
5. La app se actualizará y reiniciará automáticamente

---

## Flujo de trabajo completo

### En tu PC (desarrollo):
1. Haces cambios en el código
2. Guardas todo
3. Ejecutas: `git add . && git commit -m "cambios" && git push origin main`

### En la Raspberry (desde el navegador):
1. Abres el panel de Admin
2. Click en "Comprobar Actualizaciones"
3. Click en "Actualizar Ahora"
4. ¡Listo! La app se actualiza sola

---

## Comandos útiles para depuración

Ver logs del servicio:
```bash
journalctl -u engastado.service -f
```

Ver estado del servicio:
```bash
sudo systemctl status engastado.service
```

Actualizar manualmente desde terminal:
```bash
cd ~/PROYECTO-ENGASTADO1
git pull origin main
sudo systemctl restart engastado.service
```
