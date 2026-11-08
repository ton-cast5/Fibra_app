package com.tonylex.app.data.remote

import com.squareup.moshi.Json
import com.squareup.moshi.JsonClass

@JsonClass(generateAdapter = true)
data class LoginRequest(val username: String, val password: String)

@JsonClass(generateAdapter = true)
data class LoginResponse(
    val token: String,
    val user: ApiUser,
)

@JsonClass(generateAdapter = true)
data class ApiUser(
    val id: Int,
    val username: String,
    val nombre: String,
)

@JsonClass(generateAdapter = true)
data class NapModelDto(
    val id: Int,
    val nombre: String,
    @Json(name = "tipo_caja") val tipoCaja: String? = null,
    @Json(name = "capacidad_max") val capacidadMax: Int? = null,
    @Json(name = "imagen_url") val imagenUrl: String? = null,
)

@JsonClass(generateAdapter = true)
data class NatDto(
    val id: Int,
    val nombre: String,
    val latitud: Double? = null,
    val longitud: Double? = null,
    val descripcion: String? = null,
    val region: String? = null,
    @Json(name = "puertos_total") val puertosTotal: Int = 8,
    @Json(name = "hilo_conexion") val hiloConexion: String? = null,
    @Json(name = "nap_model_id") val napModelId: Int? = null,
    @Json(name = "tipo_caja") val tipoCaja: String? = null,
)

@JsonClass(generateAdapter = true)
data class ClienteDto(
    val id: Int,
    val nombre: String,
    val direccion: String,
    val plan: String? = null,
    val contacto: String? = null,
    val ip: String? = null,
    val servicio: String? = null,
    val activo: Boolean = true,
    @Json(name = "nat_id") val natId: Int,
)

@JsonClass(generateAdapter = true)
data class PotenciaDto(
    val id: Int,
    val fecha: String? = null,
    @Json(name = "cliente_id") val clienteId: Int,
    @Json(name = "nap_id") val napId: Int? = null,
    @Json(name = "potencia_entrada") val potenciaEntrada: Double,
    @Json(name = "potencia_salida") val potenciaSalida: Double,
    val perdida: Double? = null,
    val estado: String? = null,
    val observaciones: String? = null,
    val tecnico: String? = null,
    @Json(name = "equipo_medicion") val equipoMedicion: String? = null,
)

@JsonClass(generateAdapter = true)
data class TrabajadorDto(
    val id: Int,
    @Json(name = "nombre_completo") val nombreCompleto: String,
    val activo: Boolean = true,
)

@JsonClass(generateAdapter = true)
data class AsistenciaDto(
    val id: Int,
    @Json(name = "trabajador_id") val trabajadorId: Int,
    val tipo: String,
    @Json(name = "fecha_hora") val fechaHora: String? = null,
)

@JsonClass(generateAdapter = true)
data class DocumentoDto(
    val id: Int,
    val nombre: String,
    @Json(name = "nombre_original") val nombreOriginal: String? = null,
    val extension: String? = null,
    val tamano: Int? = null,
    val categoria: String? = null,
    @Json(name = "url_storage") val urlStorage: String? = null,
    @Json(name = "fecha_subida") val fechaSubida: String? = null,
)

@JsonClass(generateAdapter = true)
data class DataWrap<T>(val data: List<T>)

@JsonClass(generateAdapter = true)
data class ResumenDto(
    @Json(name = "total_nats") val totalNats: Int = 0,
    @Json(name = "total_clientes") val totalClientes: Int = 0,
    @Json(name = "clientes_activos") val clientesActivos: Int = 0,
    @Json(name = "total_potencias") val totalPotencias: Int = 0,
    @Json(name = "server_time") val serverTime: String? = null,
)

@JsonClass(generateAdapter = true)
data class SyncPullResponse(
    @Json(name = "server_time") val serverTime: String? = null,
    @Json(name = "nap_models") val napModels: List<NapModelDto> = emptyList(),
    val nats: List<NatDto> = emptyList(),
    val clientes: List<ClienteDto> = emptyList(),
    val potencias: List<PotenciaDto> = emptyList(),
    val trabajadores: List<TrabajadorDto> = emptyList(),
    val asistencias: List<AsistenciaDto> = emptyList(),
    val documentos: List<DocumentoDto> = emptyList(),
)

@JsonClass(generateAdapter = true)
data class SyncPushResult(
    @Json(name = "client_id") val clientId: String? = null,
    val ok: Boolean = false,
    val id: Int? = null,
    val error: String? = null,
)

@JsonClass(generateAdapter = true)
data class SyncPushResponse(
    val ok: Boolean = false,
    @Json(name = "server_time") val serverTime: String? = null,
    val results: List<SyncPushResult> = emptyList(),
)
