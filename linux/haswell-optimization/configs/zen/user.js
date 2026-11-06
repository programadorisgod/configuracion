// =============================================================================
// Optimizaciones de Alto Rendimiento para Zen Browser (Intel Haswell i5-4590S / HD 4600)
// =============================================================================

// 1. Aceleración de Video por Hardware (VA-API en Intel HD 4600)
user_pref("media.ffmpeg.vaapi.enabled", true);
user_pref("media.hardware-video-decoding.enabled", true);
user_pref("media.hardware-video-decoding.force-enabled", false); // Permite decodificación DRM Widevine sin colgar el pipeline
user_pref("media.rdd-ffmpeg.enabled", false); // Desactiva el proceso RDD para evitar deadlocks/congelamientos en Intel Haswell
user_pref("media.rdd-process.enabled", false);
user_pref("gfx.webrender.all", true);

// 2. Google Meet y Discord: Forzar H.264 por Hardware en WebRTC
// Delega la codificación y decodificación de llamadas al chip QuickSync de la GPU
user_pref("media.webrtc.hw.h264.enabled", true);
user_pref("media.navigator.mediadatadecoder_h264_enabled", true);
user_pref("media.peerconnection.video.vp9_enabled", false);

// 3. Soporte de Medios y Compatibilidad MSE (Prime Video, Netflix, YouTube)
// Mantiene activos los formatos estándar para evitar fallos en carruseles y previews de cards
user_pref("media.mediasource.vp9.enabled", true);

// 4. Juegos con WebGPU y WebGL en Intel Haswell (saltar lista de bloqueo de Mesa)
user_pref("dom.webgpu.enabled", true);
user_pref("gfx.webgpu.ignore-blocklist", true);
user_pref("webgl.force-enabled", true);

// 5. Optimización de Procesos de Pestañas y Memoria (8 GB RAM / 4 núcleos)
user_pref("dom.ipc.processCount", 4);
user_pref("dom.ipc.processCount.webIsolated", 2);
user_pref("browser.tabs.unloadOnLowMemory", false); // Evita que la pestaña activa de streaming se congele

// 6. UI y Popups accesibles (permite interacción y clics de ratón en cuadros de diálogo)
user_pref("accessibility.force_disabled", 0);

// 7. Soporte DRM Widevine (Amazon Prime Video, Netflix, Spotify Web)
user_pref("media.eme.enabled", true);
user_pref("media.gmp-widevinecdm.enabled", true);
user_pref("media.gmp-widevinecdm.visible", true);
