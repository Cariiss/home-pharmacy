package ru.homepharmacy

import android.Manifest
import android.content.pm.PackageManager
import android.os.Build
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.runtime.getValue
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import ru.homepharmacy.ui.AppNavigation
import ru.homepharmacy.ui.AppTheme
import ru.homepharmacy.ui.LoginScreen

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        // Сервер работает на компьютере в локальной сети. С Android 17 на это нужно разрешение пользователя.
        if (Build.VERSION.SDK_INT >= 37 &&
            checkSelfPermission(Manifest.permission.ACCESS_LOCAL_NETWORK) != PackageManager.PERMISSION_GRANTED
        ) {
            requestPermissions(arrayOf(Manifest.permission.ACCESS_LOCAL_NETWORK), 1)
        }
        val tokenStore = (application as App).tokenStore
        setContent {
            AppTheme {
                // нет токена — показываем вход, есть — основное приложение
                val token by tokenStore.token.collectAsStateWithLifecycle()
                if (token == null) LoginScreen() else AppNavigation()
            }
        }
    }
}
