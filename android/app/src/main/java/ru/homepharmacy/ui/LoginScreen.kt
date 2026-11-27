package ru.homepharmacy.ui

import android.app.Application
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material3.Button
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.unit.dp
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import androidx.lifecycle.viewmodel.compose.viewModel
import kotlinx.coroutines.launch
import ru.homepharmacy.App
import ru.homepharmacy.data.RegisterRequest
import ru.homepharmacy.data.errorMessage
import ru.homepharmacy.data.validateLogin

class LoginViewModel(app: Application) : AndroidViewModel(app) {
    private val api = (app as App).api
    private val tokenStore = (app as App).tokenStore

    var email by mutableStateOf("")
    var password by mutableStateOf("")
    var isRegister by mutableStateOf(false)
    var loading by mutableStateOf(false)
    var error by mutableStateOf<String?>(null)

    fun submit() {
        error = validateLogin(email.trim(), password)
        if (error != null) return
        viewModelScope.launch {
            loading = true
            try {
                if (isRegister) api.register(RegisterRequest(email.trim(), password))
                val result = api.login(email.trim(), password)
                tokenStore.save(result.accessToken) // после этого откроется список упаковок
            } catch (e: Exception) {
                error = errorMessage(e)
            }
            loading = false
        }
    }
}

@Composable
fun LoginScreen(vm: LoginViewModel = viewModel()) {
    Scaffold { padding ->
        FormColumn(PaddingValues(top = padding.calculateTopPadding() + 48.dp)) {
            Text("Домашняя аптека", style = MaterialTheme.typography.headlineMedium)
            Text(if (vm.isRegister) "Регистрация" else "Вход", style = MaterialTheme.typography.titleMedium)
            OutlinedTextField(
                value = vm.email,
                onValueChange = { vm.email = it },
                label = { Text("Email") },
                singleLine = true,
                keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Email),
                modifier = Modifier.fillMaxWidth(),
            )
            OutlinedTextField(
                value = vm.password,
                onValueChange = { vm.password = it },
                label = { Text("Пароль") },
                singleLine = true,
                visualTransformation = PasswordVisualTransformation(),
                keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Password),
                modifier = Modifier.fillMaxWidth(),
            )
            vm.error?.let { Text(it, color = MaterialTheme.colorScheme.error) }
            Button(onClick = vm::submit, enabled = !vm.loading, modifier = Modifier.fillMaxWidth()) {
                if (vm.loading) CircularProgressIndicator(Modifier.padding(2.dp))
                else Text(if (vm.isRegister) "Зарегистрироваться" else "Войти")
            }
            TextButton(onClick = { vm.isRegister = !vm.isRegister; vm.error = null }) {
                Text(if (vm.isRegister) "Уже есть аккаунт? Войти" else "Нет аккаунта? Зарегистрироваться")
            }
        }
    }
}
