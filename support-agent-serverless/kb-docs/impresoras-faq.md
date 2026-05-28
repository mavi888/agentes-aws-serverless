# FAQ — Impresoras y Escáneres

## Impresoras disponibles en la oficina

La empresa cuenta con las siguientes impresoras en red:

- `IMPR-PISO1-A`: Piso 1 — Ala A (junto a cocina). HP LaserJet Pro M404. Blanco y negro.
- `IMPR-PISO1-B`: Piso 1 — Ala B (sala de reuniones). Canon imageRUNNER 2630. Blanco y negro.
- `IMPR-PISO2`: Piso 2 — Centro. HP Color LaserJet M454. Color.
- `IMPR-GERENCIA`: Piso 3 — Gerencia. Xerox VersaLink C405. Color. Requiere autorización del jefe de área.
- `ESCANER-PISO1`: Piso 1 — Recepción. Epson WorkForce ES-500W. Solo escaneo.

Para imprimir en color usá `IMPR-PISO2` o `IMPR-GERENCIA`.

---

## Instalación de impresoras

### ¿Cómo instalo una impresora en mi computadora?

**Windows**:
1. Abrí **Configuración** → **Dispositivos** → **Impresoras y escáneres**.
2. Hacé clic en **Agregar una impresora o escáner**.
3. Si no aparece automáticamente, hacé clic en **La impresora que quiero no está en la lista**.
4. Seleccioná **Seleccionar una impresora compartida por nombre** e ingresá: `\\servidor-impresion\IMPR-PISO1-A` (reemplazá con el nombre de la impresora que necesitás).
5. Instalá los drivers si se solicitan — Windows los descarga automáticamente.

**Mac**:
1. Abrí **Preferencias del Sistema** → **Impresoras y escáneres**.
2. Hacé clic en **+** para agregar.
3. En la pestaña **Windows**, buscá el servidor `servidor-impresion` y seleccioná la impresora.
4. Si no aparece, usá **IP** e ingresá la dirección IP de la impresora (consultá la tabla de arriba o pedila a soporte).

**Nota**: Necesitás estar conectado a la red corporativa o a la VPN para instalar impresoras en red.

---

## Problemas comunes

### La impresora no imprime — el trabajo queda en cola

**Pasos a seguir**:
1. Verificá que la impresora esté encendida y sin luces de error (roja o naranja).
2. En Windows, abrí **Dispositivos e impresoras**, hacé doble clic en la impresora y cancelá todos los trabajos pendientes.
3. Reiniciá el servicio de cola de impresión:
   - Abrí el **Administrador de tareas** → pestaña **Servicios**.
   - Buscá **Spooler**, hacé clic derecho → **Reiniciar**.
4. Volvé a intentar imprimir.

Si el problema persiste, reiniciá la impresora físicamente (apagala, esperá 30 segundos, encendela).

---

### Error "Impresora sin conexión" (Printer offline)

**Causa más común**: La impresora perdió conexión con el servidor o está en modo de ahorro de energía.

**Pasos a seguir**:
1. Verificá que la impresora esté encendida — algunas entran en modo sleep y tardan unos segundos en responder.
2. En Windows, abrí **Dispositivos e impresoras**, hacé clic derecho en la impresora → **Ver qué se está imprimiendo**.
3. En el menú **Impresora**, desmarcá **Usar impresora sin conexión** si está marcado.
4. Si sigue sin funcionar, eliminá la impresora y volvé a instalarla siguiendo los pasos de instalación.

---

### La impresora imprime páginas en blanco

**Causas posibles**:
- Cartucho de tóner vacío o mal insertado.
- Archivo de impresión corrupto.
- Driver desactualizado.

**Pasos a seguir**:
1. Verificá el nivel de tóner desde el panel de la impresora o desde el software de la impresora en tu PC.
2. Cancelá el trabajo actual y volvé a enviar el documento.
3. Probá imprimir una página de prueba: **Dispositivos e impresoras** → clic derecho → **Propiedades de impresora** → **Imprimir página de prueba**.
4. Si la página de prueba también sale en blanco, el problema es de hardware — contactá a soporte para reemplazar el tóner.

---

### La impresión sale cortada o con texto ilegible

**Causa más común**: El tamaño de página del documento no coincide con el papel cargado en la impresora.

**Pasos a seguir**:
1. Verificá que el papel en la impresora sea A4 (el estándar de la empresa).
2. En el diálogo de impresión, asegurate de seleccionar **A4** como tamaño de página.
3. Si imprimís desde PDF, en Adobe Reader desactivá la opción **Ajustar al área imprimible** y seleccioná **Tamaño real**.

---

### La impresora pide un PIN o código

Las impresoras `IMPR-PISO2` e `IMPR-GERENCIA` tienen habilitada la **impresión segura** — el trabajo se retiene hasta que ingresás tu PIN en el panel de la impresora.

- Tu PIN de impresión es los **últimos 4 dígitos de tu legajo**.
- Si no sabés tu legajo, consultá en RRHH o en el portal `portal.empresa.com/mi-perfil`.
- Si olvidaste tu PIN, contactá a soporte IT para resetearlo.

---

## Escáner

### ¿Cómo escaneo un documento?

1. Colocá el documento en el escáner `ESCANER-PISO1` (Piso 1 — Recepción).
2. En el panel del escáner, seleccioná **Escanear a email** o **Escanear a carpeta**.
3. **Escanear a email**: ingresá tu email corporativo y el documento llegará en PDF en minutos.
4. **Escanear a carpeta**: el documento se guarda en `\\servidor-archivos\Escaneos\<tu-usuario>`.

Para escanear desde tu PC, instalá el software **Epson Scan 2** disponible en `portal.empresa.com/downloads/escaner`.

---

## Solicitud de tóner o papel

Cuando el tóner esté bajo o se acabe el papel, abrí un ticket en el sistema de soporte o enviá un email a soporte-it@empresa.com con:
- Nombre de la impresora (ej: `IMPR-PISO1-A`)
- Tipo de consumible necesario (tóner negro, papel A4, etc.)

El reabastecimiento tarda entre 24 y 48 horas hábiles.

---

## Contacto de soporte

Si ninguno de los pasos anteriores resuelve el problema:
- **Email**: soporte-it@empresa.com
- **Interno**: 4500 (soporte IT), horario de oficina 9:00 a 18:00, lunes a viernes
- **Portal de tickets**: portal.empresa.com/soporte
