package com.tonylex.app.data.remote

import com.squareup.moshi.Moshi
import com.squareup.moshi.kotlin.reflect.KotlinJsonAdapterFactory
import com.tonylex.app.BuildConfig
import com.tonylex.app.data.auth.TokenStore
import okhttp3.Interceptor
import okhttp3.OkHttpClient
import okhttp3.logging.HttpLoggingInterceptor
import retrofit2.Retrofit
import retrofit2.converter.moshi.MoshiConverterFactory
import java.util.concurrent.TimeUnit

object NetworkModule {
    fun createApi(tokenStore: TokenStore): ApiService {
        val auth = Interceptor { chain ->
            val builder = chain.request().newBuilder()
            tokenStore.token?.let { builder.header("Authorization", "Bearer $it") }
            chain.proceed(builder.build())
        }
        val logging = HttpLoggingInterceptor().apply {
            level = HttpLoggingInterceptor.Level.BASIC
        }
        val client = OkHttpClient.Builder()
            .addInterceptor(auth)
            .addInterceptor(logging)
            .connectTimeout(30, TimeUnit.SECONDS)
            .readTimeout(60, TimeUnit.SECONDS)
            .build()

        val moshi = Moshi.Builder()
            .add(KotlinJsonAdapterFactory())
            .build()

        val base = (tokenStore.apiBaseUrl ?: BuildConfig.API_BASE_URL).let {
            if (it.endsWith("/")) it else "$it/"
        }

        return Retrofit.Builder()
            .baseUrl(base)
            .client(client)
            .addConverterFactory(MoshiConverterFactory.create(moshi))
            .build()
            .create(ApiService::class.java)
    }
}
