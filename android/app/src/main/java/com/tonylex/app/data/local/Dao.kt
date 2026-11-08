package com.tonylex.app.data.local

import androidx.room.Dao
import androidx.room.Insert
import androidx.room.OnConflictStrategy
import androidx.room.Query
import kotlinx.coroutines.flow.Flow

@Dao
interface TonylexDao {
    @Query("SELECT * FROM nats ORDER BY nombre")
    fun observeNats(): Flow<List<NatEntity>>

    @Query("SELECT * FROM nats ORDER BY nombre")
    suspend fun getNats(): List<NatEntity>

    @Query("SELECT * FROM clientes ORDER BY nombre")
    fun observeClientes(): Flow<List<ClienteEntity>>

    @Query("SELECT * FROM clientes ORDER BY nombre")
    suspend fun getClientes(): List<ClienteEntity>

    @Query("SELECT * FROM potencias ORDER BY fecha DESC")
    fun observePotencias(): Flow<List<PotenciaEntity>>

    @Query("SELECT * FROM nap_models ORDER BY nombre")
    fun observeNapModels(): Flow<List<NapModelEntity>>

    @Query("SELECT * FROM trabajadores ORDER BY nombreCompleto")
    fun observeTrabajadores(): Flow<List<TrabajadorEntity>>

    @Query("SELECT * FROM asistencias ORDER BY fechaHora DESC")
    fun observeAsistencias(): Flow<List<AsistenciaEntity>>

    @Query("SELECT * FROM documentos ORDER BY fechaSubida DESC")
    fun observeDocumentos(): Flow<List<DocumentoEntity>>

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun upsertNats(items: List<NatEntity>)

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun upsertClientes(items: List<ClienteEntity>)

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun upsertPotencias(items: List<PotenciaEntity>)

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun upsertNapModels(items: List<NapModelEntity>)

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun upsertTrabajadores(items: List<TrabajadorEntity>)

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun upsertAsistencias(items: List<AsistenciaEntity>)

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun upsertDocumentos(items: List<DocumentoEntity>)

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun upsertNat(item: NatEntity)

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun upsertCliente(item: ClienteEntity)

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun upsertPotencia(item: PotenciaEntity)

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun upsertAsistencia(item: AsistenciaEntity)

    @Query("DELETE FROM nats WHERE id = :id")
    suspend fun deleteNat(id: Int)

    @Query("DELETE FROM clientes WHERE id = :id")
    suspend fun deleteCliente(id: Int)

    @Query("DELETE FROM potencias WHERE id = :id")
    suspend fun deletePotencia(id: Int)

    @Query("DELETE FROM asistencias WHERE id = :id")
    suspend fun deleteAsistencia(id: Int)

    @Insert
    suspend fun enqueue(outbox: OutboxEntity): Long

    @Query("SELECT * FROM outbox ORDER BY createdAt ASC")
    suspend fun pendingOutbox(): List<OutboxEntity>

    @Query("DELETE FROM outbox WHERE id = :id")
    suspend fun deleteOutbox(id: Long)

    @Query("SELECT COUNT(*) FROM outbox")
    fun observeOutboxCount(): Flow<Int>

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun putMeta(meta: SyncMetaEntity)

    @Query("SELECT value FROM sync_meta WHERE key = :key LIMIT 1")
    suspend fun getMeta(key: String): String?

    @Query("SELECT COUNT(*) FROM clientes WHERE activo = 1")
    suspend fun countClientesActivos(): Int

    @Query("SELECT COUNT(*) FROM nats")
    suspend fun countNats(): Int

    @Query("SELECT COUNT(*) FROM clientes")
    suspend fun countClientes(): Int

    @Query("SELECT COUNT(*) FROM potencias")
    suspend fun countPotencias(): Int
}
