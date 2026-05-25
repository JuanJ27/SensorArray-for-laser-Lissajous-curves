# Storyline de presentacion: detectabilidad de flashes

## Mensaje central

El montaje actual ya permite defender una historia experimental coherente sobre detectabilidad de destellos LED, diferenciando claramente entre lo que aporta la webcam y lo que aporta el canal analogico OP598.

## Hilo narrativo sugerido

1. **Pregunta experimental**
   - Queremos saber si la cadena de medicion actual detecta destellos cortos de forma reproducible.
   - El LED rojo se usa como analogia controlada de detectabilidad, no como sustituto completo de una curva de Lissajous real.

2. **Por que no alcanza con la webcam sola**
   - La webcam da evidencia visual y detectabilidad gruesa.
   - Su respuesta depende de exposicion, FPS real y duracion del pulso.
   - No debe venderse como instrumentacion temporal rapida.

3. **Que agrega el OP598**
   - Entrega una medicion analogica directa del canal iluminado.
   - Permite discutir saturacion, amplitud y ancho efectivo del pulso reconstruido.
   - Sigue estando limitado por ADC y overhead de MicroPython.

4. **Por que el flujo dual importa**
   - Ya no solo preguntamos "se vio o no se vio".
   - Podemos medir coincidencia entre pulsos comandados, respuesta OP598 y deteccion webcam.
   - Eso abre la puerta a una validacion cruzada mas fuerte.

5. **Cierre honesto**
   - Hoy el sistema demuestra detectabilidad y coincidencia experimental offline.
   - Aun falta cerrar mejor cobertura estadistica y temporizacion fina antes de reclamar comportamiento equivalente a instrumentacion rapida.

## Apoyos visuales recomendados

- `notebooks/flash_detection_presentation_analysis.ipynb`
- `data/derived/presentation/notebook/webcam_detectability_vs_duty.png`
- `data/derived/presentation/notebook/webcam_duration_exposure_summary.png`
- `data/derived/presentation/notebook/op598_saturation_and_width.png`
- `data/derived/presentation/notebook/dual_coincidence_and_coverage.png`

## Frases de defensa utiles

- "La webcam nos sirve para detectabilidad macroscópica, no para resolver microdinámica del pulso."
- "El OP598 mejora la lectura analógica, pero en esta etapa todavía está condicionado por la cadena de adquisición en MicroPython."
- "La parte más fuerte del material actual es que ya podemos cuantificar coincidencia entre canales con una pipeline reproducible offline."
