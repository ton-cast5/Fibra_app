package com.tonylex.app.data.sync

import com.tonylex.app.data.local.AsistenciaEntity
import com.tonylex.app.data.local.ClienteEntity
import com.tonylex.app.data.local.DocumentoEntity
import com.tonylex.app.data.local.NapModelEntity
import com.tonylex.app.data.local.NatEntity
import com.tonylex.app.data.local.OutboxEntity
import com.tonylex.app.data.local.PotenciaEntity
import com.tonylex.app.data.local.SyncMetaEntity
import com.tonylex.app.data.local.TonylexDao
import com.tonylex.app.data.local.TrabajadorEntity
import com.tonylex.app.data.remote.ApiService
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.RequestBody.Companion.toRequestBody
import org.json.JSONArray
import org.json.JSONObject
import java.util.UUID

class SyncRepository(
    private val dao: TonylexDao,
    private val api: ApiService,
) {

    suspend fun pull() {
        val since = dao.getMeta(KEY_LAST_PULL)
        val remote = api.syncPull(since)
        dao.upsertNapModels(remote.napModels.map {
            NapModelEntity(it.id, it.nombre, it.tipoCaja, it.capacidadMax, it.imagenUrl)
        })
        dao.upsertNats(remote.nats.map {
            NatEntity(
                it.id, it.nombre, it.latitud, it.longitud, it.descripcion, it.region,
                it.puertosTotal, it.hiloConexion, it.napModelId, it.tipoCaja, localOnly = false,
            )
        })
        dao.upsertClientes(remote.clientes.map {
            ClienteEntity(
                it.id, it.nombre, it.direccion, it.plan, it.contacto, it.ip, it.servicio,
                it.activo, it.natId, localOnly = false,
            )
        })
        dao.upsertPotencias(remote.potencias.map {
            PotenciaEntity(
                it.id, it.fecha, it.clienteId, it.napId, it.potenciaEntrada, it.potenciaSalida,
                it.perdida, it.estado, it.observaciones, it.tecnico, it.equipoMedicion, false,
            )
        })
        dao.upsertTrabajadores(remote.trabajadores.map {
            TrabajadorEntity(it.id, it.nombreCompleto, it.activo)
        })
        dao.upsertAsistencias(remote.asistencias.map {
            AsistenciaEntity(it.id, it.trabajadorId, it.tipo, it.fechaHora, false)
        })
        dao.upsertDocumentos(remote.documentos.map {
            DocumentoEntity(
                it.id, it.nombre, it.nombreOriginal, it.extension, it.tamano,
                it.categoria, it.urlStorage, it.fechaSubida,
            )
        })
        remote.serverTime?.let { dao.putMeta(SyncMetaEntity(KEY_LAST_PULL, it)) }
    }

    suspend fun push(): Boolean {
        val pending = dao.pendingOutbox()
        if (pending.isEmpty()) return true
        val arr = JSONArray()
        pending.forEach { row ->
            val dataObj = runCatching { JSONObject(row.payloadJson) }.getOrElse { JSONObject() }
            val mut = JSONObject()
                .put("client_id", row.clientId)
                .put("entity", row.entity)
                .put("op", row.op)
            if (row.remoteId != null) mut.put("remote_id", row.remoteId)
            mut.put("data", dataObj)
            arr.put(mut)
        }
        val body = JSONObject().put("mutations", arr).toString()
            .toRequestBody("application/json".toMediaType())
        val response = api.syncPush(body)
        if (!response.ok) return false
        pending.forEach { dao.deleteOutbox(it.id) }
        response.serverTime?.let { dao.putMeta(SyncMetaEntity(KEY_LAST_PULL, it)) }
        return true
    }

    suspend fun syncAll() {
        push()
        pull()
    }

    suspend fun enqueue(entity: String, op: String, remoteId: Int?, data: Map<String, Any?>) {
        val obj = JSONObject()
        data.forEach { (k, v) ->
            when (v) {
                null -> obj.put(k, JSONObject.NULL)
                else -> obj.put(k, v)
            }
        }
        val json = obj.toString()
        dao.enqueue(
            OutboxEntity(
                clientId = UUID.randomUUID().toString(),
                entity = entity,
                op = op,
                remoteId = remoteId,
                payloadJson = json,
            ),
        )
    }

    companion object {
        const val KEY_LAST_PULL = "last_pull"
    }
}
