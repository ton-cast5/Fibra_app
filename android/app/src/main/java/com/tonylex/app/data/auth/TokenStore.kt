package com.tonylex.app.data.auth

import android.content.Context
import androidx.security.crypto.EncryptedSharedPreferences
import androidx.security.crypto.MasterKey

class TokenStore(context: Context) {
    private val prefs = EncryptedSharedPreferences.create(
        context,
        "tonylex_secure",
        MasterKey.Builder(context).setKeyScheme(MasterKey.KeyScheme.AES256_GCM).build(),
        EncryptedSharedPreferences.PrefKeyEncryptionScheme.AES256_SIV,
        EncryptedSharedPreferences.PrefValueEncryptionScheme.AES256_GCM,
    )

    var token: String?
        get() = prefs.getString(KEY_TOKEN, null)
        set(value) {
            prefs.edit().putString(KEY_TOKEN, value).apply()
        }

    var username: String?
        get() = prefs.getString(KEY_USER, null)
        set(value) {
            prefs.edit().putString(KEY_USER, value).apply()
        }

    var displayName: String?
        get() = prefs.getString(KEY_NAME, null)
        set(value) {
            prefs.edit().putString(KEY_NAME, value).apply()
        }

    var apiBaseUrl: String?
        get() = prefs.getString(KEY_BASE, null)
        set(value) {
            prefs.edit().putString(KEY_BASE, value).apply()
        }

    fun clear() {
        prefs.edit().clear().apply()
    }

    fun isLoggedIn(): Boolean = !token.isNullOrBlank()

    companion object {
        private const val KEY_TOKEN = "token"
        private const val KEY_USER = "username"
        private const val KEY_NAME = "nombre"
        private const val KEY_BASE = "api_base"
    }
}
