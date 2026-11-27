package ru.homepharmacy.data

import android.content.Context
import androidx.datastore.preferences.core.edit
import androidx.datastore.preferences.core.stringPreferencesKey
import androidx.datastore.preferences.preferencesDataStore
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.runBlocking

private val Context.dataStore by preferencesDataStore(name = "session")
private val TOKEN = stringPreferencesKey("token")

// Хранит токен между запусками. Копия в памяти нужна, чтобы быстро добавлять его к запросам.
class TokenStore(private val context: Context) {
    private val current = MutableStateFlow(runBlocking { context.dataStore.data.first()[TOKEN] })
    val token: StateFlow<String?> = current

    suspend fun save(value: String) {
        context.dataStore.edit { it[TOKEN] = value }
        current.value = value
    }

    suspend fun clear() {
        context.dataStore.edit { it.remove(TOKEN) }
        current.value = null
    }
}
