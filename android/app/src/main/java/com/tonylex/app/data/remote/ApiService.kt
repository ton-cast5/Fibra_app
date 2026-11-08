package com.tonylex.app.data.remote

import okhttp3.RequestBody
import retrofit2.http.Body
import retrofit2.http.DELETE
import retrofit2.http.GET
import retrofit2.http.POST
import retrofit2.http.PUT
import retrofit2.http.Path
import retrofit2.http.Query

interface ApiService {
    @POST("api/v1/auth/login")
    suspend fun login(@Body body: LoginRequest): LoginResponse

    @GET("api/v1/auth/me")
    suspend fun me(): ApiUser

    @GET("api/v1/resumen")
    suspend fun resumen(): ResumenDto

    @GET("api/v1/nats")
    suspend fun nats(): DataWrap<NatDto>

    @POST("api/v1/nats")
    suspend fun createNat(@Body body: Map<String, @JvmSuppressWildcards Any?>): NatDto

    @PUT("api/v1/nats/{id}")
    suspend fun updateNat(@Path("id") id: Int, @Body body: Map<String, @JvmSuppressWildcards Any?>): NatDto

    @DELETE("api/v1/nats/{id}")
    suspend fun deleteNat(@Path("id") id: Int)

    @GET("api/v1/clientes")
    suspend fun clientes(): DataWrap<ClienteDto>

    @POST("api/v1/clientes")
    suspend fun createCliente(@Body body: Map<String, @JvmSuppressWildcards Any?>): ClienteDto

    @PUT("api/v1/clientes/{id}")
    suspend fun updateCliente(@Path("id") id: Int, @Body body: Map<String, @JvmSuppressWildcards Any?>): ClienteDto

    @DELETE("api/v1/clientes/{id}")
    suspend fun deleteCliente(@Path("id") id: Int)

    @GET("api/v1/potencias")
    suspend fun potencias(): DataWrap<PotenciaDto>

    @POST("api/v1/potencias")
    suspend fun createPotencia(@Body body: Map<String, @JvmSuppressWildcards Any?>): PotenciaDto

    @GET("api/v1/asistencias")
    suspend fun asistencias(): DataWrap<AsistenciaDto>

    @POST("api/v1/asistencias")
    suspend fun createAsistencia(@Body body: Map<String, @JvmSuppressWildcards Any?>): AsistenciaDto

    @GET("api/v1/documentos")
    suspend fun documentos(): DataWrap<DocumentoDto>

    @GET("api/v1/sync/pull")
    suspend fun syncPull(@Query("updated_since") updatedSince: String? = null): SyncPullResponse

    @POST("api/v1/sync/push")
    suspend fun syncPush(@Body body: RequestBody): SyncPushResponse
}
