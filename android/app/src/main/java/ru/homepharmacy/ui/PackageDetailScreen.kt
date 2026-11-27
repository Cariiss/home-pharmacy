package ru.homepharmacy.ui

import android.app.Application
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Button
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.SavedStateHandle
import androidx.lifecycle.viewModelScope
import androidx.lifecycle.viewmodel.compose.viewModel
import kotlinx.coroutines.launch
import ru.homepharmacy.App
import ru.homepharmacy.data.PackageItem
import ru.homepharmacy.data.errorMessage
import ru.homepharmacy.data.formatDate
import ru.homepharmacy.data.statusText

class PackageDetailViewModel(app: Application, saved: SavedStateHandle) : AndroidViewModel(app) {
    private val api = (app as App).api
    val id: Int = saved["id"] ?: 0

    var item by mutableStateOf<PackageItem?>(null)
    var error by mutableStateOf<String?>(null)
    var deleted by mutableStateOf(false)

    fun load() {
        viewModelScope.launch {
            error = null
            try {
                item = api.getPackage(id)
            } catch (e: Exception) {
                error = errorMessage(e)
            }
        }
    }

    fun delete() {
        viewModelScope.launch {
            try {
                api.deletePackage(id)
                deleted = true
            } catch (e: Exception) {
                error = errorMessage(e)
            }
        }
    }
}

@Composable
fun PackageDetailScreen(onBack: () -> Unit, onEdit: (Int) -> Unit, vm: PackageDetailViewModel = viewModel()) {
    LaunchedEffect(Unit) { vm.load() }
    LaunchedEffect(vm.deleted) { if (vm.deleted) onBack() }
    var askDelete by remember { mutableStateOf(false) }

    Scaffold(topBar = { BackTopBar("Упаковка", onBack) }) { padding ->
        val item = vm.item
        val error = vm.error
        when {
            error != null -> Box(Modifier.padding(padding)) { ErrorWithRetry(error, vm::load) }
            item == null -> Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) { CircularProgressIndicator() }
            else -> FormColumn(padding) {
                Text(item.medicineName, style = MaterialTheme.typography.headlineSmall)
                Text(statusText(item.status, item.daysLeft), color = statusColor(item.status),
                    style = MaterialTheme.typography.titleMedium)
                Field("Срок годности", formatDate(item.expiryDate))
                Field("Количество", item.quantity.toString())
                Field("Где лежит", item.location ?: "не указано")
                Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                    Button(onClick = { onEdit(item.id) }) { Text("Изменить") }
                    OutlinedButton(onClick = { askDelete = true }) { Text("Удалить") }
                }
            }
        }
    }

    if (askDelete) {
        AlertDialog(
            onDismissRequest = { askDelete = false },
            title = { Text("Удалить упаковку?") },
            text = { Text("Упаковка пропадёт из списка. Это действие нельзя отменить.") },
            confirmButton = { TextButton(onClick = { askDelete = false; vm.delete() }) { Text("Удалить") } },
            dismissButton = { TextButton(onClick = { askDelete = false }) { Text("Отмена") } },
        )
    }
}

@Composable
private fun Field(label: String, value: String) {
    Text(label, style = MaterialTheme.typography.labelMedium, color = MaterialTheme.colorScheme.outline)
    Text(value, style = MaterialTheme.typography.bodyLarge)
}
