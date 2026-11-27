package ru.homepharmacy

import android.app.Application
import ru.homepharmacy.data.Api
import ru.homepharmacy.data.TokenStore
import ru.homepharmacy.data.createApi

// Общие объекты приложения: хранилище токена и клиент API
class App : Application() {
    lateinit var tokenStore: TokenStore
    lateinit var api: Api

    override fun onCreate() {
        super.onCreate()
        tokenStore = TokenStore(this)
        api = createApi(BuildConfig.API_URL, tokenStore)
    }
}
