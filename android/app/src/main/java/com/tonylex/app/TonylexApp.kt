package com.tonylex.app

import android.app.Application
import com.tonylex.app.data.Repository
import com.tonylex.app.data.auth.TokenStore
import com.tonylex.app.data.local.AppDatabase
import com.tonylex.app.data.remote.NetworkModule
import com.tonylex.app.data.sync.SyncRepository
import com.tonylex.app.data.sync.SyncWorker

class TonylexApp : Application() {
    lateinit var tokenStore: TokenStore
        private set
    lateinit var repository: Repository
        private set
    lateinit var syncRepository: SyncRepository
        private set

    override fun onCreate() {
        super.onCreate()
        tokenStore = TokenStore(this)
        rebuildGraph()
        if (tokenStore.isLoggedIn()) {
            SyncWorker.enqueue(this)
        }
    }

    fun rebuildGraph() {
        val db = AppDatabase.get(this)
        val api = NetworkModule.createApi(tokenStore)
        syncRepository = SyncRepository(db.dao(), api)
        repository = Repository(this, db.dao(), api, tokenStore, syncRepository)
    }
}
