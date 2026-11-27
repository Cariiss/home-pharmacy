package ru.homepharmacy.ui

import android.app.Application
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxHeight
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.grid.GridCells
import androidx.compose.foundation.lazy.grid.LazyVerticalGrid
import androidx.compose.foundation.lazy.grid.items
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.IntrinsicSize
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Add
import androidx.compose.material.icons.filled.List
import androidx.compose.material.icons.filled.Search
import androidx.compose.material.icons.filled.Settings
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.FilterChip
import androidx.compose.material3.FloatingActionButton
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
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
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch
import ru.homepharmacy.App
import ru.homepharmacy.data.PackageItem
import ru.homepharmacy.data.errorMessage
import ru.homepharmacy.data.formatDate
import ru.homepharmacy.data.statusText

class PackagesViewModel(app: Application) : AndroidViewModel(app) {
    private val api = (app as App).api

    var items by mutableStateOf<List<PackageItem>>(emptyList())
    var query by mutableStateOf("")
    var filter by mutableStateOf<String?>(null) // null — все, "expiring", "expired"
    var loading by mutableStateOf(false)
    var error by mutableStateOf<String?>(null)

    fun load() {
        viewModelScope.launch {
            loading = true
            error = null
            try {
                items = api.packages(filter, query.trim().ifBlank { null })
            } catch (e: Exception) {
                error = errorMessage(e)
            }
            loading = false
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun PackagesScreen(
    onOpen: (Int) -> Unit,
    onAdd: () -> Unit,
    onMedicines: () -> Unit,
    onSettings: () -> Unit,
    vm: PackagesViewModel = viewModel(),
) {
    // загружаем при открытии экрана и при смене поиска или фильтра (с небольшой паузой при наборе)
    LaunchedEffect(vm.query, vm.filter) {
        delay(300)
        vm.load()
    }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("Мои упаковки") },
                actions = {
                    IconButton(onClick = onMedicines) { Icon(Icons.Default.List, "Справочник") }
                    IconButton(onClick = onSettings) { Icon(Icons.Default.Settings, "Настройки") }
                },
            )
        },
        floatingActionButton = {
            FloatingActionButton(onClick = onAdd) { Icon(Icons.Default.Add, "Добавить упаковку") }
        },
    ) { padding ->
        Column(Modifier.fillMaxSize().padding(padding)) {
            OutlinedTextField(
                value = vm.query,
                onValueChange = { vm.query = it },
                placeholder = { Text("Поиск по названию") },
                leadingIcon = { Icon(Icons.Default.Search, null) },
                singleLine = true,
                modifier = Modifier.fillMaxWidth().padding(horizontal = 16.dp),
            )
            Row(Modifier.padding(horizontal = 16.dp), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                FilterChip(vm.filter == null, onClick = { vm.filter = null }, label = { Text("Все") })
                FilterChip(vm.filter == "expiring", onClick = { vm.filter = "expiring" }, label = { Text("Истекают") })
                FilterChip(vm.filter == "expired", onClick = { vm.filter = "expired" }, label = { Text("Просрочены") })
            }

            val error = vm.error
            when {
                error != null -> ErrorWithRetry(error, vm::load)
                vm.loading && vm.items.isEmpty() ->
                    Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) { CircularProgressIndicator() }
                vm.items.isEmpty() -> EmptyList(searching = vm.query.isNotBlank() || vm.filter != null, onAdd = onAdd)
                // на широком экране карточки встают в несколько колонок
                else -> LazyVerticalGrid(
                    columns = GridCells.Adaptive(minSize = 320.dp),
                    contentPadding = PaddingValues(start = 16.dp, end = 16.dp, top = 8.dp, bottom = 88.dp),
                    horizontalArrangement = Arrangement.spacedBy(12.dp),
                    verticalArrangement = Arrangement.spacedBy(12.dp),
                ) {
                    items(vm.items, key = { it.id }) { item -> PackageCard(item, onClick = { onOpen(item.id) }) }
                }
            }
        }
    }
}

@Composable
private fun PackageCard(item: PackageItem, onClick: () -> Unit) {
    Card(onClick = onClick, modifier = Modifier.fillMaxWidth()) {
        Row(Modifier.height(IntrinsicSize.Min)) {
            // цветная полоска слева показывает состояние срока
            Box(Modifier.width(6.dp).fillMaxHeight().background(statusColor(item.status)))
            Column(Modifier.padding(12.dp)) {
                Text(item.medicineName, style = MaterialTheme.typography.titleMedium)
                Text("Годен до ${formatDate(item.expiryDate)}")
                Text(statusText(item.status, item.daysLeft), color = statusColor(item.status))
                val place = item.location?.let { " · $it" } ?: ""
                Text("Количество: ${item.quantity}$place", style = MaterialTheme.typography.bodySmall)
            }
        }
    }
}

@Composable
private fun EmptyList(searching: Boolean, onAdd: () -> Unit) {
    Column(
        Modifier.fillMaxSize().padding(24.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.Center,
    ) {
        if (searching) {
            Text("Ничего не найдено")
        } else {
            Text("Упаковок пока нет")
            Button(onClick = onAdd, modifier = Modifier.padding(top = 12.dp)) { Text("Добавить упаковку") }
        }
    }
}
