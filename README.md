# Batadrez

Variante de ajedrez para dos jugadores en el mismo computador. Cada bando esconde un **civil** entre sus nueve piezas; gana quien capture el civil rival. No hay jaque ni jaque mate.

Interfaz hecha con **pygame**. El motor de reglas, relojes, puntuación, perfiles y niveles es independiente de la interfaz y se prueba con **pytest**.

## Requisitos

- Python 3.11 o superior
- pygame
- pytest (para las pruebas)

## Instalación y ejecución

En Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
python main.py
```

En Linux o macOS:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python main.py
```

La ventana se puede redimensionar; el contenido se escala manteniendo la proporción.

## Cómo se juega

1. En **Perfiles**, crea al menos dos perfiles. Cada perfil guarda nombre, puntos y bloqueo de Compota de Manzana.
2. En **Jugar**, elige un perfil para el Jugador 1 y otro para el Jugador 2.
3. Los colores se asignan al azar. Las blancas preparan primero y mueven primero.
4. **Pantalla de relevo:** cada jugador prepara en secreto su bando cuando le toca. El otro jugador no debe mirar.
5. En la preparación, haz clic en una pieza del set y luego en una casilla de tus dos filas iniciales. Puedes mover una pieza ya colocada haciendo clic sobre ella y luego sobre el destino. El clic derecho retira una pieza.
6. Para elegir el civil, pulsa **Elegir civil** y haz clic en una de tus piezas colocadas. La interfaz de preparación lo muestra con un punto dorado, pero durante la partida no se muestra nunca.
7. Confirma las nueve piezas y el civil. Cuando ambos jugadores hayan confirmado, comienza la partida con las posiciones reveladas y los civiles ocultos.
8. Durante la partida: clic en una pieza propia y clic en una casilla resaltada. El clic derecho cancela la selección.

Todos los controles de juego son con el mouse. El teclado solo se usa para escribir nombres de perfil.

## Reglas

- Tablero de 8x8.
- Cada jugador tiene 1 Rey, 1 Dama, 1 Torre, 2 Alfiles, 2 Caballos y 2 Peones.
- Todas las piezas se mueven y capturan como en ajedrez. Las piezas son públicas; solo el civil es secreto.
- No existen enroque, captura al paso, coronación, jaque ni jaque mate.
- El Rey es una pieza más: puede ser capturado y la partida continúa.
- El peón avanza una casilla y captura en diagonal hacia delante. Si llega a su última fila, queda inmóvil.
- Al capturar una pieza se anuncia si **era el civil** o **no era el civil**. Si era el civil, la partida termina de inmediato.
- Al terminar se revelan los dos civiles.
- Cada jugador tiene 4:00. El reloj corre solo durante su turno.
- Si el reloj de un jugador llega a 0, la partida termina en empate con penalización de -3 puntos para ese jugador y 0 para el otro. No se gana por tiempo.
- **Minuto de la partida:** suma del tiempo consumido por ambos relojes.
- **Ahogado:** el jugador al que le toca mover no tiene movimientos legales. Empate con 0 puntos para ambos.
- **Repetición:** la misma posición, con el mismo turno, aparece por tercera vez. Empate con 0 puntos para ambos.
- **Abandono:** el jugador que abandona pierde y recibe los puntos de derrota correspondientes al minuto actual.

## Puntuación por partida

| Duración total | Ganar | Perder |
|---|---:|---:|
| Hasta 2:00 inclusive | +10 | -10 |
| 2:01 a 5:00 | +7 | -7 |
| 5:01 en adelante | +4 | -4 |

- Empate por tiempo agotado: -3 para quien se quedó sin tiempo, 0 para el otro.
- Empates por ahogado o repetición: 0 para ambos.

Los cambios se aplican a los puntos acumulados del perfil al terminar la partida.

## Niveles

| Nivel | Puntos |
|---|---:|
| Semilla | 0 a 64 |
| Árbol | 65 a 144 |
| Fruta | 145 a 215 |
| Manzana | 216 a 900 |
| Compota de Manzana | 901 o más |

- Los puntos acumulados nunca bajan de 0.
- Al llegar a Compota de Manzana, el nivel queda bloqueado y no desciende aunque se pierdan puntos después.
- Los demás niveles sí pueden bajar si los puntos disminuyen.
- La interfaz muestra nivel, puntos y cuánto falta para el siguiente nivel. El resultado avisa cuando alguien sube de nivel.

## Perfiles y persistencia

Los perfiles se guardan en `profiles.json`, en la raíz del proyecto. El archivo se escribe de forma atómica.

Si `profiles.json` está dañado o tiene un formato inválido:

- se crea una copia de seguridad llamada `profiles.corrupt-FECHA.json`;
- la aplicación arranca sin perfiles y muestra un aviso;
- se puede empezar de cero creando perfiles nuevos.

Borrar un perfil elimina también sus puntos de forma permanente.

## Configuración

Todas las constantes configurables están en `game/constants.py`:

- `BOARD_SIZE`, `SET_SIZE` y `PIECE_COUNTS`: tamaño del tablero y composición del set.
- `WHITE_HOME_ROWS` y `BLACK_HOME_ROWS`: filas iniciales.
- `PAWN_CAN_MOVE_TWO`: por defecto `False`. Si se activa, un peón que no se haya movido puede avanzar dos casillas si el camino está libre. El estado de movimiento se conserva para la detección de repeticiones.
- `CIVIL_CAN_BE_PAWN`: por defecto `True`.
- `CLOCK_START_SECONDS`: 240 segundos por jugador.
- `SCORE_BRACKET_LIMITS_SECONDS`, `WIN_POINTS_BY_BRACKET`, `LOSS_POINTS_BY_BRACKET`: rangos y puntos.
- `TIMEOUT_PENALTY`: penalización por tiempo agotado.
- `LEVEL_DEFINITIONS`, `COMPOTA_THRESHOLD`, `COMPOTA_LEVEL_NAME`: umbrales de niveles.
- `POINTS_NEVER_BELOW_ZERO` y `COMPOTA_PREVENTS_DESCENT`: supuestos de progresión.
- `PROFILES_FILE` y `MAX_PROFILE_NAME_LENGTH`: persistencia y nombres.

Si se cambia `PIECE_COUNTS`, hay que ajustar también `SET_SIZE` para que coincida con la suma de piezas.

## Supuestos y decisiones

- Los colores se sortean al comenzar cada partida (incluida una revancha).
- Las blancas preparan primero, para que el orden de preparación coincida con el primer turno.
- En la preparación, las filas iniciales se muestran siempre desde el punto de vista de las blancas: las negras usan las dos filas superiores y las blancas las dos inferiores.
- El reloj sigue corriendo mientras se abre el panel de reglas o la confirmación de abandono. Se indica en el panel de reglas.
- Al agotarse el tiempo, la partida termina inmediatamente en empate con penalización.
- El abandono lo realiza el jugador al que le toca mover en ese momento.
- La repetición compara posiciones completas más el turno. Como no hay enroque ni captura al paso, no hay otros derechos especiales que registrar. Si se activa el avance doble de peón, también se registra si el peón ya se movió.
- No hay oferta de tablas, rendición desde el menú ni pausa manual.
- Los nombres de perfil no distinguen mayúsculas de minúsculas para evitar duplicados.
- Los textos de la interfaz están en español; los identificadores y comentarios de código siguen el estilo indicado en el proyecto.

## Arquitectura

```text
main.py                  Punto de entrada
game/
  constants.py            Reglas y valores configurables
  pieces.py               Piezas, colores e identificadores
  setup.py                Validación de la preparación secreta
  board.py                Tablero y movimientos
  match.py                Turnos, relojes, finales y puntuación
  levels.py               Cálculo de niveles
  profiles.py             Perfiles y persistencia JSON
ui/
  app.py                  Ventana, navegación y bucle principal
  theme.py                Colores, fuentes y dibujo común
  menu.py                 Menú principal
  profiles.py             Alta, baja y estado de perfiles
  lobby.py                Selección de los dos jugadores
  relay.py                Pantalla de relevo
  setup.py                Preparación secreta con tablero
  match.py                Partida, relojes y anuncios
  result.py               Resultado y revelación de civiles
  ranking.py              Ranking
tests/
  test_pieces.py          Movimientos y capturas de todas las piezas
  test_civil.py           Civil secreto y fin de partida
  test_match.py           Relojes, rangos, tiempo, ahogado y repetición
  test_levels.py          Umbrales, Compota, JSON y corrupción
  test_ui_smoke.py        Humo de las pantallas en modo sin ventana
```

El paquete `game/` no importa pygame.

## Pruebas

```powershell
python -m pytest -q
```

Resultado esperado: **50 pruebas superadas**. La prueba de interfaz usa el controlador `dummy` de SDL, por lo que no abre una ventana.

También se puede verificar la sintaxis con:

```powershell
python -m compileall -q game ui main.py
```

## Fases de desarrollo

1. Motor de tablero, piezas, movimientos y capturas.
2. Civil secreto y final por captura.
3. Relojes, puntuación, tiempo agotado, ahogado y repetición.
4. Perfiles, niveles, umbrales y persistencia JSON.
5. Interfaz pygame completa con menú, perfiles, relevo, preparación, partida, resultado y ranking.
6. Pulido final, manejo del JSON dañado y documentación.
