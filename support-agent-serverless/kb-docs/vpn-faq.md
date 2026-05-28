# FAQ — VPN Corporativa

## ¿Qué es la VPN corporativa y para qué sirve?

La VPN (Virtual Private Network) corporativa permite conectarte de forma segura a la red interna de la empresa desde cualquier lugar. Es obligatoria para acceder a sistemas internos como el ERP, el servidor de archivos compartidos y las bases de datos de producción.

---

## Problemas de conexión

### No puedo conectarme a la VPN desde casa

**Síntomas**: El cliente VPN muestra error "Connection timed out" o "Unable to reach server".

**Pasos a seguir**:
1. Verificá que tenés conexión a internet (probá abrir una página web).
2. Reiniciá el cliente VPN: cerralo completamente y volvé a abrirlo.
3. Verificá que estás usando el servidor correcto: `vpn.empresa.com` (no `vpn2` ni variantes antiguas).
4. Desactivá temporalmente el firewall o antivirus y volvé a intentar.
5. Si usás Windows, ejecutá el cliente como administrador.
6. Reiniciá el router/módem de tu casa.

Si ninguno de estos pasos funciona, escalá al nivel 2 con el mensaje de error exacto.

---

### La VPN se conecta pero no puedo acceder a los sistemas internos

**Síntomas**: El cliente VPN muestra "Connected" pero no podés abrir el ERP ni el servidor de archivos.

**Pasos a seguir**:
1. Verificá que el ícono de la VPN en la barra de tareas muestra el candado cerrado (verde).
2. Probá hacer ping al servidor interno: `ping 10.0.1.1` desde la terminal.
3. Cerrá y volvé a abrir el cliente VPN.
4. Reiniciá tu computadora con la VPN desconectada, luego volvé a conectarte.

Si el ping falla, el problema puede ser de routing. Escalá al nivel 2.

---

### La VPN se desconecta sola cada cierto tiempo

**Causa más común**: Configuración de ahorro de energía en Windows/Mac que suspende el adaptador de red.

**Solución en Windows**:
1. Abrí el Administrador de dispositivos.
2. Buscá tu adaptador de red, hacé clic derecho → Propiedades.
3. En la pestaña "Administración de energía", desmarcá "Permitir que el equipo apague este dispositivo para ahorrar energía".

**Solución en Mac**:
1. Preferencias del Sistema → Batería → desmarcá "Activar el modo de suspensión cuando la pantalla esté apagada".

---

### Error "Authentication failed" al conectarme

**Causas posibles**:
- Contraseña expirada (las contraseñas expiran cada 90 días).
- Usuario bloqueado por intentos fallidos (se bloquea después de 5 intentos).
- MFA no configurado o token incorrecto.

**Pasos a seguir**:
1. Intentá iniciar sesión en el portal web `portal.empresa.com` para verificar si tu cuenta está activa.
2. Si la contraseña expiró, podés cambiarla desde el portal web sin necesidad de estar en la VPN.
3. Si el usuario está bloqueado, contactá a soporte — no podés desbloquearlo vos mismo.
4. Para problemas de MFA, verificá que el reloj de tu teléfono esté sincronizado (los tokens TOTP son sensibles al tiempo).

---

## Configuración inicial

### ¿Cómo instalo el cliente VPN por primera vez?

1. Descargá el instalador desde el portal interno: `portal.empresa.com/downloads/vpn`.
2. Ejecutá el instalador con permisos de administrador.
3. Al abrir el cliente, ingresá el servidor: `vpn.empresa.com`.
4. Usá tus credenciales corporativas (el mismo usuario y contraseña que usás para el email).
5. Si tu cuenta tiene MFA habilitado (obligatorio para roles con acceso a producción), ingresá el código de 6 dígitos de tu app autenticadora.

**Sistemas operativos soportados**: Windows 10/11, macOS 12+, Ubuntu 20.04+.

---

### ¿Puedo usar la VPN desde mi celular?

Sí. Descargá la app **GlobalProtect** (iOS o Android) desde la tienda de aplicaciones. Configurá el servidor `vpn.empresa.com` y usá tus credenciales corporativas.

---

## Preguntas frecuentes

### ¿Necesito la VPN para usar el email corporativo?

No. El email (Outlook/Gmail corporativo) funciona sin VPN. La VPN es necesaria para acceder al ERP, servidor de archivos, bases de datos internas y sistemas de desarrollo.

### ¿Puedo tener la VPN conectada todo el día?

Sí, es lo recomendado si trabajás desde casa. No afecta el rendimiento de tu conexión a internet para uso normal.

### ¿Qué hago si olvidé mi contraseña de VPN?

La contraseña de VPN es la misma que tu contraseña corporativa. Podés resetearla desde `portal.empresa.com/reset-password` sin necesidad de contactar a soporte.

### ¿La VPN funciona desde el extranjero?

Sí, desde cualquier país. Si tenés problemas de latencia alta, probá conectarte al servidor regional más cercano (consultá la lista en `portal.empresa.com/vpn-servers`).
