package com.tonylex.app.data.sync

import android.content.Context
import androidx.work.Constraints
import androidx.work.CoroutineWorker
import androidx.work.ExistingWorkPolicy
import androidx.work.NetworkType
import androidx.work.OneTimeWorkRequestBuilder
import androidx.work.WorkManager
import androidx.work.WorkerParameters
import com.tonylex.app.TonylexApp

class SyncWorker(
    appContext: Context,
    params: WorkerParameters,
) : CoroutineWorker(appContext, params) {
    override suspend fun doWork(): Result {
        val app = applicationContext as TonylexApp
        return try {
            app.syncRepository.syncAll()
            Result.success()
        } catch (_: Exception) {
            Result.retry()
        }
    }

    companion object {
        private const val UNIQUE = "tonylex-sync"

        fun enqueue(context: Context) {
            val constraints = Constraints.Builder()
                .setRequiredNetworkType(NetworkType.CONNECTED)
                .build()
            val req = OneTimeWorkRequestBuilder<SyncWorker>()
                .setConstraints(constraints)
                .build()
            WorkManager.getInstance(context).enqueueUniqueWork(
                UNIQUE,
                ExistingWorkPolicy.KEEP,
                req,
            )
        }
    }
}
