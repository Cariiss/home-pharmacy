package ru.homepharmacy.ui

import android.app.Application
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.DateRange
import androidx.compose.material3.Button
import androidx.compose.material3.DatePicker
import androidx.compose.material3.DatePickerDialog
import androidx.compose.material3.DropdownMenu
import androidx.compose.material3.DropdownMenuItem
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.material3.rememberDatePickerState
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.input.KeyboardType
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.SavedStateHandle
import androidx.lifecycle.viewModelScope
import androidx.lifecycle.viewmodel.compose.viewModel
import kotlinx.coroutines.launch
import ru.homepharmacy.App
import ru.homepharmacy.data.Medicine
import ru.homepharmacy.data.PackageRequest
import ru.homepharmacy.data.PackageUpdateRequest
import ru.homepharmacy.data.errorMessage
import ru.homepharmacy.data.formatDate
import ru.homepharmacy.data.validatePackage
import java.time.Instant
import java.time.LocalDate
import java.time.ZoneOffset

class PackageFormViewModel(app: Application, saved: SavedStateHandle) : AndroidViewModel(app) {
    private val api = (app as App).api
    val id: Int = saved["id"] ?: 0
    val isEdit = id != 0

    var medicines by mutableStateOf<List<Medicine>>(emptyList())
    var medicineId by mutableStateOf<Int?>(null)
    var date by mutableStateOf<LocalDate?>(null)
    var quantity by mutableStateOf("1")
    var location by mutableStateOf("")
    var error by mutableStateOf<String?>(null)
    var saving by mutableStateOf(false)
    var saved by mutableStateOf(false)
    private var filled = false

    fun load() {
        viewModelScope.launch {
            try {
                // справочник обновляем каждый раз: его могли дополнить на соседнем экране
                medicines = api.medicines()
                // данные упаковки подставляем один раз, чтобы не стереть то, что уже ввели
                if (isEdit && !filled) {
                    val item = api.getPackage(id)
                    medicineId = item.medicineId
                    date = LocalDate.parse(item.expiryDate)
                    quantity = item.quantity.toString()
                    location = item.location ?: ""
                    filled = true
                }
            } catch (e: Exception) {
                error = errorMessage(e)
            }
        }
    }

    fun save() {
        error = validatePackage(medicineId, date, quantity)
        if (error != null) return
        val place = location.trim().ifBlank { null }
        viewModelScope.launch {
            saving = true
            try {
                if (isEdit) {
                    api.updatePackage(id, PackageUpdateRequest(date.toString(), quantity.trim().toInt(), place))
                } else {
                    api.addPackage(PackageRequest(medicineId!!, date.toString(), quantity.trim().toInt(), place))
                }
                saved = true
            } catch (e: Exception) {
                error = errorMessage(e)
            }
            saving = false
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun PackageFormScreen(onBack: () -> Unit, onMedicines: () -> Unit, vm: PackageFormViewModel = viewModel()) {
    LaunchedEffect(Unit) { vm.load() }
    LaunchedEffect(vm.saved) { if (vm.saved) onBack() }
    var menuOpen by remember { mutableStateOf(false) }
    var pickDate by remember { mutableStateOf(false) }

    Scaffold(topBar = { BackTopBar(if (vm.isEdit) "Изменить упаковку" else "Новая упаковка", onBack) }) { padding ->
        FormColumn(padding) {
            // Препарат выбирается из справочника. У сохранённой упаковки его не меняем.
            Text("Препарат", style = MaterialTheme.typography.labelLarge)
            if (vm.medicines.isEmpty() && !vm.isEdit) {
                Text("Справочник пуст. Сначала добавьте препарат.")
                OutlinedButton(onClick = onMedicines) { Text("Открыть справочник") }
            } else {
                Box {
                    val selected = vm.medicines.find { it.id == vm.medicineId }
                    OutlinedButton(
                        onClick = { menuOpen = true },
                        enabled = !vm.isEdit,
                        modifier = Modifier.fillMaxWidth(),
                    ) { Text(selected?.let { medicineTitle(it) } ?: "Выберите препарат") }
                    DropdownMenu(expanded = menuOpen, onDismissRequest = { menuOpen = false }) {
                        vm.medicines.forEach { medicine ->
                            DropdownMenuItem(
                                text = { Text(medicineTitle(medicine)) },
                                onClick = { vm.medicineId = medicine.id; menuOpen = false },
                            )
                        }
                    }
                }
            }

            Text("Срок годности", style = MaterialTheme.typography.labelLarge)
            OutlinedButton(onClick = { pickDate = true }, modifier = Modifier.fillMaxWidth()) {
                Icon(Icons.Default.DateRange, null)
                Text(vm.date?.let { "  " + formatDate(it.toString()) } ?: "  Выберите дату")
            }

            OutlinedTextField(
                value = vm.quantity,
                onValueChange = { vm.quantity = it },
                label = { Text("Количество") },
                singleLine = true,
                keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number),
                modifier = Modifier.fillMaxWidth(),
            )
            OutlinedTextField(
                value = vm.location,
                onValueChange = { vm.location = it },
                label = { Text("Где лежит (необязательно)") },
                singleLine = true,
                modifier = Modifier.fillMaxWidth(),
            )

            vm.error?.let { Text(it, color = MaterialTheme.colorScheme.error) }
            Button(onClick = vm::save, enabled = !vm.saving, modifier = Modifier.fillMaxWidth()) {
                Text("Сохранить")
            }
        }
    }

    if (pickDate) {
        // DatePicker работает с миллисекундами в UTC
        val state = rememberDatePickerState(
            initialSelectedDateMillis = vm.date?.atStartOfDay(ZoneOffset.UTC)?.toInstant()?.toEpochMilli(),
        )
        DatePickerDialog(
            onDismissRequest = { pickDate = false },
            confirmButton = {
                TextButton(onClick = {
                    state.selectedDateMillis?.let {
                        vm.date = Instant.ofEpochMilli(it).atZone(ZoneOffset.UTC).toLocalDate()
                    }
                    pickDate = false
                }) { Text("Готово") }
            },
            dismissButton = { TextButton(onClick = { pickDate = false }) { Text("Отмена") } },
        ) { DatePicker(state) }
    }
}

fun medicineTitle(m: Medicine): String = listOfNotNull(m.name, m.form, m.dosage).joinToString(", ")
