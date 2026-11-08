package com.tonylex.app.data.local

import androidx.room.Entity
import androidx.room.PrimaryKey

@Entity(tableName = "nap_models")
data class NapModelEntity(
    @PrimaryKey val id: Int,
    val nombre: String,
    val tipoCaja: String?,
    val capacidadMax: Int?,
    val imagenUrl: String?,
)

@Entity(tableName = "nats")
data class NatEntity(
    @PrimaryKey val id: Int,
    val nombre: String,
    val latitud: Double?,
    val longitud: Double?,
    val descripcion: String?,
    val region: String?,
    val puertosTotal: Int,
    val hiloConexion: String?,
    val napModelId: Int?,
    val tipoCaja: String?,
    val localOnly: Boolean = false,
)

@Entity(tableName = "clientes")
data class ClienteEntity(
    @PrimaryKey val id: Int,
    val nombre: String,
    val direccion: String,
    val plan: String?,
    val contacto: String?,
    val ip: String?,
    val servicio: String?,
    val activo: Boolean,
    val natId: Int,
    val localOnly: Boolean = false,
)

@Entity(tableName = "potencias")
data class PotenciaEntity(
    @PrimaryKey val id: Int,
    val fecha: String?,
    val clienteId: Int,
    val napId: Int?,
    val potenciaEntrada: Double,
    val potenciaSalida: Double,
    val perdida: Double?,
    val estado: String?,
    val observaciones: String?,
    val tecnico: String?,
    val equipoMedicion: String?,
    val localOnly: Boolean = false,
)

@Entity(tableName = "trabajadores")
data class TrabajadorEntity(
    @PrimaryKey val id: Int,
    val nombreCompleto: String,
    val activo: Boolean,
)

@Entity(tableName = "asistencias")
data class AsistenciaEntity(
    @PrimaryKey val id: Int,
    val trabajadorId: Int,
    val tipo: String,
    val fechaHora: String?,
    val localOnly: Boolean = false,
)

@Entity(tableName = "documentos")
data class DocumentoEntity(
    @PrimaryKey val id: Int,
    val nombre: String,
    val nombreOriginal: String?,
    val extension: String?,
    val tamano: Int?,
    val categoria: String?,
    val urlStorage: String?,
    val fechaSubida: String?,
)

@Entity(tableName = "outbox")
data class OutboxEntity(
    @PrimaryKey(autoGenerate = true) val id: Long = 0,
    val clientId: String,
    val entity: String,
    val op: String,
    val remoteId: Int?,
    val payloadJson: String,
    val createdAt: Long = System.currentTimeMillis(),
)

@Entity(tableName = "sync_meta")
data class SyncMetaEntity(
    @PrimaryKey val key: String,
    val value: String,
)
