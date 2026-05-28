# Política de Contraseñas y Accesos

## Requisitos de contraseña

Todas las contraseñas corporativas deben cumplir los siguientes requisitos:

- **Longitud mínima**: 12 caracteres.
- **Debe incluir**: al menos una mayúscula, una minúscula, un número y un carácter especial (`!@#$%^&*`).
- **No puede incluir**: tu nombre de usuario, nombre real, o las últimas 10 contraseñas usadas.
- **Vigencia**: 90 días. El sistema te avisa 15 días antes de que expire.

---

## Resetear la contraseña

### Olvidé mi contraseña y no puedo iniciar sesión

1. Ingresá a `portal.empresa.com/reset-password` desde cualquier dispositivo (no necesitás estar en la VPN).
2. Ingresá tu email corporativo.
3. Recibirás un email con un link de reset válido por 30 minutos.
4. Seguí el link y creá una nueva contraseña que cumpla los requisitos.

Si no recibís el email en 5 minutos, revisá la carpeta de spam. Si tampoco está ahí, contactá a soporte IT — puede ser que tu email esté mal configurado en el sistema.

---

### Mi contraseña expiró y no puedo entrar a nada

Si la contraseña expiró, el sistema te redirige automáticamente al portal de cambio de contraseña al intentar iniciar sesión. Seguí los pasos en pantalla.

Si el sistema no te redirige y simplemente rechaza el login, usá el portal de reset: `portal.empresa.com/reset-password`.

---

### Mi cuenta está bloqueada

Las cuentas se bloquean automáticamente después de **5 intentos fallidos consecutivos**. No podés desbloquearla vos mismo — necesitás contactar a soporte IT.

Para desbloquear tu cuenta:
- Enviá un email a `soporte-it@empresa.com` con el asunto "Desbloqueo de cuenta" e indicá tu usuario.
- O llamá al interno 4400 (soporte IT) en horario de oficina (9:00 a 18:00, lunes a viernes).

El desbloqueo tarda entre 15 y 30 minutos en horario hábil.

---

## Autenticación de dos factores (MFA)

### ¿Qué es MFA y por qué es obligatorio?

MFA (Multi-Factor Authentication) agrega una segunda capa de seguridad: además de tu contraseña, necesitás un código de 6 dígitos que cambia cada 30 segundos. Esto protege tu cuenta incluso si alguien obtiene tu contraseña.

**MFA es obligatorio para**:
- Acceso a la VPN.
- Acceso al ERP y sistemas financieros.
- Acceso a repositorios de código.
- Roles con permisos de administrador.

---

### ¿Cómo configuro MFA por primera vez?

1. Descargá una app autenticadora: **Google Authenticator**, **Microsoft Authenticator** o **Authy** (cualquiera funciona).
2. Ingresá a `portal.empresa.com/mfa-setup`.
3. Escaneá el código QR con la app.
4. Ingresá el código de 6 dígitos que muestra la app para confirmar la configuración.
5. Guardá los **códigos de recuperación** que te muestra el sistema — son de un solo uso y te permiten entrar si perdés el teléfono.

---

### Perdí mi teléfono y no puedo generar el código MFA

**Si tenés los códigos de recuperación**: usá uno de ellos en lugar del código MFA. Cada código funciona una sola vez.

**Si no tenés los códigos de recuperación**: contactá a soporte IT en persona (necesitamos verificar tu identidad presencialmente o por videollamada con documento). No podemos resetear el MFA por email por razones de seguridad.

---

### El código MFA no funciona aunque lo ingreso correctamente

La causa más común es que el reloj de tu teléfono no está sincronizado. Los códigos TOTP son válidos solo por 30 segundos y dependen de la hora exacta.

**Solución**:
- **Android**: Configuración → Sistema → Fecha y hora → activá "Fecha y hora automáticas".
- **iPhone**: Configuración → General → Fecha y hora → activá "Establecer automáticamente".

Si el problema persiste después de sincronizar el reloj, contactá a soporte IT.

---

## Gestión de accesos

### ¿Cómo solicito acceso a un sistema nuevo?

1. Ingresá a `portal.empresa.com/accesos`.
2. Buscá el sistema al que necesitás acceso.
3. Completá la justificación del negocio.
4. La solicitud va a tu manager para aprobación.
5. Una vez aprobada, el equipo de IT provisiona el acceso en 1-2 días hábiles.

---

### ¿Cómo reporto que alguien tiene accesos que no debería tener?

Enviá un email a `seguridad@empresa.com` con el asunto "Reporte de acceso indebido". Incluí el nombre del usuario, el sistema y por qué creés que el acceso es incorrecto. El equipo de seguridad investiga en 24 horas.

---

### Me fui de vacaciones y al volver no puedo entrar

Si estuviste ausente más de 30 días, tu cuenta puede haber sido suspendida automáticamente por política de seguridad. Contactá a soporte IT para reactivarla — necesitarás la aprobación de tu manager.

---

## Buenas prácticas

- **Nunca compartas tu contraseña** con nadie, incluyendo soporte IT. Soporte nunca te va a pedir tu contraseña.
- **No uses la misma contraseña** en sistemas corporativos y personales.
- **Usá un gestor de contraseñas** (la empresa tiene licencias de 1Password disponibles — solicitala en `portal.empresa.com/software`).
- **Bloqueá tu pantalla** cuando te alejés de tu computadora (Windows: `Win + L`, Mac: `Cmd + Ctrl + Q`).
- **Reportá inmediatamente** si sospechás que tu cuenta fue comprometida: `seguridad@empresa.com`.
