package com.tonylex.app.data.local

import android.content.Context
import androidx.room.Database
import androidx.room.Room
import androidx.room.RoomDatabase

@Database(
    entities = [
        NapModelEntity::class,
        NatEntity::class,
        ClienteEntity::class,
        PotenciaEntity::class,
        TrabajadorEntity::class,
        AsistenciaEntity::class,
        DocumentoEntity::class,
        OutboxEntity::class,
        SyncMetaEntity::class,
    ],
    version = 1,
    exportSchema = false,
)
abstract class AppDatabase : RoomDatabase() {
    abstract fun dao(): TonylexDao

    companion object {
        @Volatile private var instance: AppDatabase? = null

        fun get(context: Context): AppDatabase =
            instance ?: synchronized(this) {
                instance ?: Room.databaseBuilder(
                    context.applicationContext,
                    AppDatabase::class.java,
                    "tonylex.db",
                ).fallbackToDestructiveMigration().build().also { instance = it }
            }
    }
}
