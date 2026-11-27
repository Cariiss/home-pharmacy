package ru.homepharmacy.ui

import android.app.Application
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.grid.GridCells
import androidx.compose.foundation.lazy.grid.LazyVerticalGrid
import androidx.compose.foundation.lazy.grid.items
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Add
import androidx.compose.material.icons.filled.Delete
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Card
import androidx.compose.material3.FloatingActionButton
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Scaffold
import androidx.compose.material3.SnackbarHost
import androidx.compose.material3.SnackbarHostState
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
import androidx.lifecycle.viewModelScope
import androidx.lifecycle.viewmodel.compose.viewModel
import kotlinx.coroutines.launch
import ru.homepharmacy.App
import ru.homepharmacy.data.Medicine
import ru.homepharmacy.data.MedicineRequest
import ru.homepharmacy.data.errorMessage

class MedicinesViewModel(app: Application) : AndroidViewModel(app) {
    private val api = (app as App).api

    var items by mutableStateOf<List<Medicine>>(emptyList())
    var message by mutableStateOf<String?>(null) // короткое сообщение внизу экрана

    // диалог добавления или изменения: editing = null — диалог закрыт, id = 0 — новый препарат
    var editing by mutableStateOf<Medicine?>(null)
    var name by mutableStateOf("")
    var form by mutableStateOf("")
    var dosage by mutableStateOf("")

    fun load() {
        viewModelScope.launch {
            try {
                items = api.medicines()
            } catch (e: Exception) {
                message = errorMessage(e)
            }
        }
    }

    fun openDialog(medicine: Medicine?) {
        editing = medicine ?: Medicine(0, "", null, null)
        name = medicine?.name ?: ""
        form = medicine?.form ?: ""
        dosage = medicine?.dosage ?: ""
    }

    fun save() {
        val current = editing ?: return
        if (name.isBlank()) {
            message = "Введите название"
            return
        }
        val body = MedicineRequest(name.trim(), form.trim().ifBlank { null }, dosage.trim().ifBlank { null })
        viewModelScope.launch {
            try {
                if (current.id == 0) api.addMedicine(body) else api.updateMedicine(current.id, body)
                editing = null
                load()
            } catch (e: Exception) {
                message = errorMessage(e)
            }
        }
    }

    fun delete(medicine: Medicine) {
        viewModelScope.launch {
            try {
                api.deleteMedicine(medicine.id)
                load()
            } catch (e: Exception) {
                message = errorMessage(e) // например, у препарата ещё есть упаковки (409)
            }
        }
    }
}

@Composable
fun MedicinesScreen(onBack: () -> Unit, vm: MedicinesViewModel = viewModel()) {
    LaunchedEffect(Unit) { vm.load() }
    val snackbar = remember { SnackbarHostState() }
    LaunchedEffect(vm.message) {
        vm.message?.let { snackbar.showSnackbar(it) }
        vm.message = null
    }
    var toDelete by remember { mutableStateOf<Medicine?>(null) }

    Scaffold(
        topBar = { BackTopBar("Справочник препаратов", onBack) },
        snackbarHost = { SnackbarHost(snackbar) },
        floatingActionButton = {
            FloatingActionButton(onClick = { vm.openDialog(null) }) { Icon(Icons.Default.Add, "Добавить препарат") }
        },
    ) { padding ->
        if (vm.items.isEmpty()) {
            Column(Modifier.padding(padding).padding(24.dp)) { Text("В справочнике пока пусто. Нажмите «+», чтобы добавить препарат.") }
        }
        LazyVerticalGrid(
            columns = GridCells.Adaptive(minSize = 320.dp),
            modifier = Modifier.padding(padding),
            contentPadding = PaddingValues(start = 16.dp, end = 16.dp, top = 8.dp, bottom = 88.dp),
            horizontalArrangement = Arrangement.spacedBy(12.dp),
            verticalArrangement = Arrangement.spacedBy(12.dp),
        ) {
            items(vm.items, key = { it.id }) { medicine ->
                Card(onClick = { vm.openDialog(medicine) }, modifier = Modifier.fillMaxWidth()) {
                    Row(Modifier.padding(start = 12.dp), verticalAlignment = Alignment.CenterVertically) {
                        Column(Modifier.weight(1f).padding(vertical = 12.dp)) {
                            Text(medicine.name, style = MaterialTheme.typography.titleMedium)
                            val details = listOfNotNull(medicine.form, medicine.dosage).joinToString(", ")
                            if (details.isNotEmpty()) Text(details)
                        }
                        IconButton(onClick = { toDelete = medicine }) { Icon(Icons.Default.Delete, "Удалить") }
                    }
                }
            }
        }
    }

    vm.editing?.let { current ->
        AlertDialog(
            onDismissRequest = { vm.editing = null },
            title = { Text(if (current.id == 0) "Новый препарат" else "Изменить препарат") },
            text = {
                Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    OutlinedTextField(vm.name, { vm.name = it }, label = { Text("Название") }, singleLine = true)
                    OutlinedTextField(vm.form, { vm.form = it }, label = { Text("Форма (таблетки, сироп…)") }, singleLine = true)
                    OutlinedTextField(vm.dosage, { vm.dosage = it }, label = { Text("Дозировка") }, singleLine = true)
                }
            },
            confirmButton = { TextButton(onClick = vm::save) { Text("Сохранить") } },
            dismissButton = { TextButton(onClick = { vm.editing = null }) { Text("Отмена") } },
        )
    }

    toDelete?.let { medicine ->
        AlertDialog(
            onDismissRequest = { toDelete = null },
            title = { Text("Удалить «${medicine.name}»?") },
            confirmButton = { TextButton(onClick = { toDelete = null; vm.delete(medicine) }) { Text("Удалить") } },
            dismissButton = { TextButton(onClick = { toDelete = null }) { Text("Отмена") } },
        )
    }
}
