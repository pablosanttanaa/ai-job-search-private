# Git en este proyecto: cuenta PERSONAL

En este equipo, git y VS Code tienen la sesión iniciada con la cuenta **corporativa**
(GitHub `Pablo-Orbalia`, `psantana@orbalia.es`). Este proyecto es personal y debe
publicarse **solo** en la cuenta personal (GitHub `pablosanttanaa`).

## Identidad
- `git config user.name "Pablo Santana"`
- `git config user.email "pablosnta14@hotmail.com"` (config local del repo)
- GitHub asigna cada commit a una cuenta según el **correo del autor**, no según quién hace el push.

## Sin marca de agua
- Ningún commit lleva `Co-Authored-By: Claude` ni otra atribución a Claude o Anthropic.
  Esta regla prevalece sobre la atribución por defecto de Claude Code.

## Remotos
- `personal` → `https://pablosanttanaa@github.com/pablosanttanaa/ai-job-search-private.git`
  (el usuario delante del dominio evita que git use la credencial corporativa).
- `origin` (Pablo-Orbalia) y `upstream` (MadsLorentzen): no se modifican ni se hace push a ellos.

## Historial heredado
- Los commits del proyecto original (`MadsLorentzen/ai-job-search`, MIT) conservan a sus
  autores reales y sus mensajes. **No** se reescriben con `--reset-author`.
- Solo se corrigen los commits propios (posteriores a `0f6480d`).

## Comprobaciones antes de cada push (sobre los commits propios, `0f6480d..HEAD`)
- `git log 0f6480d..HEAD --format='%h %an <%ae> | committer: %ce | %s'` → todo `pablosnta14@hotmail.com`
- `git log 0f6480d..HEAD --format=%B | grep -ic co-authored` → `0`
- `git log --all --format='%ae %ce' | grep -c orbalia` → `0`
- Sin archivos sensibles versionados:
  `git ls-files | grep -iE '(^|/)\.env($|\.)|\.key$|\.pem$|id_rsa|\.db$|\.sqlite3?$'` → vacío.
  Si aparece alguno: `git rm --cached`, añadirlo a `.gitignore` y avisar antes de seguir.

## Push
- `git push -u personal <rama actual>`
- Si falla con 403 "denied to Pablo-Orbalia": **parar y avisar**. Pablo tiene que iniciar sesión
  con la cuenta personal en la ventana del navegador. No intentar rodearlo.
- Después: `git ls-remote personal` y comprobar que el hash remoto coincide con `git rev-parse HEAD`.

## Si un commit propio sale mal
- Correo corporativo o `Co-Authored-By` en commits propios: reescribir solo esos con
  `git rebase -r 0f6480d --exec 'git log -1 --format=%B | grep -iv "^co-authored-by:" | git commit --amend --no-verify -F - --reset-author --cleanup=strip'`
- Si ya se había hecho push, el push corregido necesita `--force-with-lease` y hay que
  confirmarlo antes con Pablo.
