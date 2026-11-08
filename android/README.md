# TONYLEX Android

App nativa Kotlin + Jetpack Compose con Room (offline), outbox FIFO, WorkManager y Retrofit hacia `/api/v1`.

## Abrir en Android Studio

1. Abre la carpeta `android/` como proyecto.
2. En `app/build.gradle.kts` o en el login, configura `API_BASE_URL` (tu servidor Flask/Vercel).
3. Sync Gradle y ejecuta en dispositivo/emulador (minSdk 26).

## Flujo offline

- Login requiere red (emite token Bearer).
- Datos se guardan en Room; mutaciones CRUD van a la tabla `outbox`.
- Con red, `SyncWorker` hace push → pull contra `/api/v1/sync/*`.

## Módulos UI

Inicio, Cajas NAP, Clientes, Mapa (OSMDroid), Potencias, Asistencias, Documentos (metadatos).
