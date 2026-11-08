package com.tonylex.app.data

import com.tonylex.app.data.auth.TokenStore
import com.tonylex.app.data.local.AsistenciaEntity
import com.tonylex.app.data.local.ClienteEntity
import com.tonylex.app.data.local.NatEntity
import com.tonylex.app.data.local.PotenciaEntity
import com.tonylex.app.data.local.TonylexDao
import com.tonylex.app.data.remote.ApiService
import com.tonylex.app.data.remote.LoginRequest
import com.tonylex.app.data.sync.SyncRepository
import com.tonylex.app.data.sync.SyncWorker
import android.content.Context
import kotlinx.coroutines.flow.Flow

class Repository(
    private val context: Context,
    private val dao: TonylexDao,
    private val api: ApiService,
    private val tokenStore: TokenStore,
    private val sync: SyncRepository,
) {
    fun nats(): Flow<List<NatEntity>> = dao.observeNats()
    fun clientes(): Flow<List<ClienteEntity>> = dao.observeClientes()
    fun potencias(): Flow<List<PotenciaEntity>> = dao.observePotencias()
    fun asistencias(): Flow<List<AsistenciaEntity>> = dao.observeAsistencias()
    fun outboxCount(): Flow<Int> = dao.observeOutboxCount()
    fun napModels() = dao.observeNapModels()
    fun trabajadores() = dao.observeTrabajadores()
    fun documentos() = dao.observeDocumentos()

    suspend fun login(username: String, password: String, baseUrl: String?) {
        if (!baseUrl.isNullOrBlank()) {
            tokenStore.apiBaseUrl = baseUrl.trim()
        }
        val response = api.login(LoginRequest(username.trim().lowercase(), password))
        tokenStore.token = response.token
        tokenStore.username = response.user.username
        tokenStore.displayName = response.user.nombre
        sync.syncAll()
    }

    fun logout() {
        tokenStore.clear()
    }

    suspend fun refresh() {
        sync.syncAll()
    }

    suspend fun saveNatLocal(nombre: String, region: String?, puertos: Int, lat: Double?, lon: Double?) {
        val tempId = -((System.currentTimeMillis() % Int.MAX_VALUE).toInt())
        val entity = NatEntity(
            id = tempId,
            nombre = nombre,
            latitud = lat,
            longitud = lon,
            descripcion = null,
            region = region,
            puertosTotal = puertos,
            hiloConexion = null,
            napModelId = null,
            tipoCaja = "distribucion",
            localOnly = true,
        )
        dao.upsertNat(entity)
        sync.enqueue(
            "nat", "create", null,
            mapOf(
                "nombre" to nombre,
                "region" to region,
                "puertos_total" to puertos,
                "latitud" to lat,
                "longitud" to lon,
            ),
        )
        SyncWorker.enqueue(context)
    }

    suspend fun deleteNat(id: Int) {
        dao.deleteNat(id)
        if (id > 0) {
            sync.enqueue("nat", "delete", id, emptyMap())
            SyncWorker.enqueue(context)
        }
    }

    suspend fun saveClienteLocal(
        nombre: String,
        direccion: String,
        natId: Int,
        plan: String?,
        contacto: String?,
    ) {
        val tempId = -((System.currentTimeMillis() % Int.MAX_VALUE).toInt())
        dao.upsertCliente(
            ClienteEntity(
                id = tempId,
                nombre = nombre,
                direccion = direccion,
                plan = plan,
                contacto = contacto,
                ip = null,
                servicio = null,
                activo = true,
                natId = natId,
                localOnly = true,
            ),
        )
        sync.enqueue(
            "cliente", "create", null,
            mapOf(
                "nombre" to nombre,
                "direccion" to direccion,
                "nat_id" to natId,
                "plan" to plan,
                "contacto" to contacto,
                "activo" to true,
            ),
        )
        SyncWorker.enqueue(context)
    }

    suspend fun deleteCliente(id: Int) {
        dao.deleteCliente(id)
        if (id > 0) {
            sync.enqueue("cliente", "delete", id, emptyMap())
            SyncWorker.enqueue(context)
        }
    }

    suspend fun savePotenciaLocal(
        clienteId: Int,
        napId: Int?,
        entrada: Double,
        salida: Double,
        tecnico: String?,
    ) {
        val tempId = -((System.currentTimeMillis() % Int.MAX_VALUE).toInt())
        dao.upsertPotencia(
            PotenciaEntity(
                id = tempId,
                fecha = null,
                clienteId = clienteId,
                napId = napId,
                potenciaEntrada = entrada,
                potenciaSalida = salida,
                perdida = kotlin.math.abs(salida - entrada),
                estado = "normal",
                observaciones = null,
                tecnico = tecnico,
                equipoMedicion = null,
                localOnly = true,
            ),
        )
        sync.enqueue(
            "potencia", "create", null,
            mapOf(
                "cliente_id" to clienteId,
                "nap_id" to napId,
                "potencia_entrada" to entrada,
                "potencia_salida" to salida,
                "tecnico" to tecnico,
            ),
        )
        SyncWorker.enqueue(context)
    }

    suspend fun saveAsistenciaLocal(trabajadorId: Int, tipo: String) {
        val tempId = -((System.currentTimeMillis() % Int.MAX_VALUE).toInt())
        dao.upsertAsistencia(
            AsistenciaEntity(tempId, trabajadorId, tipo, null, localOnly = true),
        )
        sync.enqueue(
            "asistencia", "create", null,
            mapOf("trabajador_id" to trabajadorId, "tipo" to tipo),
        )
        SyncWorker.enqueue(context)
    }

    suspend fun dashboardCounts(): Triple<Int, Int, Int> =
        Triple(dao.countNats(), dao.countClientesActivos(), dao.countPotencias())
}
