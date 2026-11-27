package ru.homepharmacy.ui

import android.app.Application
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.material3.FilterChip
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Switch
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import androidx.lifecycle.viewmodel.compose.viewModel
import kotlinx.coroutines.launch
import ru.homepharmacy.App
import ru.homepharmacy.BuildConfig
import ru.homepharmacy.data.Settings
import ru.homepharmacy.data.errorMessage

class SettingsViewModel(app: Application) : AndroidViewModel(app) {
    private val api = (app as App).api
    private val tokenStore = (app as App).tokenStore

    var email by mutableStateOf("")
    var settings by mutableStateOf<Settings?>(null)
    var error by mutableStateOf<String?>(null)

    fun load() {
        viewModelScope.launch {
            try {
                email = api.me().email
                settings = api.settings()
            } catch (e: Exception) {
                error = errorMessage(e)
            }
        }
    }

    // каждое изменение сразу сохраняем на сервере
    fun update(newSettings: Settings) {
        viewModelScope.launch {
            try {
                settings = api.updateSettings(newSettings)
                error = null
            } catch (e: Exception) {
                error = errorMessage(e)
            }
        }
    }

    fun logout() {
        viewModelScope.launch { tokenStore.clear() }
    }
}

@Composable
fun SettingsScreen(onBack: () -> Unit, vm: SettingsViewModel = viewModel()) {
    LaunchedEffect(Unit) { vm.load() }

    Scaffold(topBar = { BackTopBar("Настройки", onBack) }) { padding ->
        FormColumn(padding) {
            if (vm.email.isNotEmpty()) Text("Вы вошли как ${vm.email}")

            vm.settings?.let { s ->
                Text("Предупреждать о конце срока за", style = MaterialTheme.typography.titleMedium)
                Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    listOf(7, 14, 30).forEach { days ->
                        FilterChip(
                            selected = s.thresholdDays == days,
                            onClick = { vm.update(s.copy(thresholdDays = days)) },
                            label = { Text("$days дней") },
                        )
                    }
                }
                Row(Modifier.fillMaxWidth(), verticalAlignment = Alignment.CenterVertically) {
                    Text("Уведомления", Modifier.weight(1f), style = MaterialTheme.typography.titleMedium)
                    Switch(
                        checked = s.notificationsEnabled,
                        onCheckedChange = { vm.update(s.copy(notificationsEnabled = it)) },
                    )
                }
            }

            vm.error?.let { Text(it, color = MaterialTheme.colorScheme.error) }
            OutlinedButton(onClick = vm::logout, modifier = Modifier.fillMaxWidth()) { Text("Выйти") }
            Text("Сервер: ${BuildConfig.API_URL}", style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.outline)
        }
    }
}
