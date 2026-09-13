# Neon Brick Breaker

Juego táctil en Kivy para Android. Versión 0.2 con diez niveles diseñados a mano,
tres vidas, dificultad progresiva, ladrillos de hasta tres golpes y récord local.

## Controles

- Tocá **Jugar** y luego el campo para lanzar la bola.
- Deslizá el dedo para mover la paleta. El punto del rebote cambia la dirección.
- Atrapá `+` para multibola (hasta cinco bolas) y `<>` para ampliar la paleta durante 12 segundos.
- Los puntos dentro de cada ladrillo indican los golpes restantes.
- El botón de pausa o Atrás pausa la partida. Al volver de otra app queda en pausa.
- Completar un nivel recupera una vida, hasta un máximo de tres.
- Tras el décimo nivel aparece la victoria; no se repite automáticamente el tablero.

## Desarrollo

Instalá Kivy y ejecutá `python main.py`. Las reglas están separadas en `game.py`:

```sh
python -m unittest discover -s tests -v
```

El flujo de GitHub Actions ejecuta las pruebas y genera el APK con Buildozer en Linux.
Descargá el artefacto `NeonBrickBreaker-APK`, extraé el ZIP e instalá el APK que contiene.
La compilación usa la revisión de python-for-android con el arreglo de pip, NDK 28c
y Java 17. El mínimo configurado es Android 12 y se incluyen ARM de 32 y 64 bits.
