# Copia de legado (no modificar sin revisión)

Copia del repo personal `gtorres777/backups` (Gustavo Torres, ex integrante), commit `b5b3192ae49ea95c3f607e7ae1146f81a42152b1` (rama `master`), tomada el 2026-09-29.
Existe para que la `jenkins-sharedlib` no ejecute código de una cuenta personal externa: los procesos clonan esta copia.

- Es **pública** porque los pods la clonan sin credenciales; el contenido ya era público en la cuenta original.
- Se copió **sin historial**: el historial original contenía una contraseña (vieja, ya no vigente).
- Cambio respecto del original: se quitó `--acl public-read` de las subidas a S3 (el bucket ya ignora ACLs públicas).
- Responsable: Fernando. Referencia: tarea Odoo 77333.
