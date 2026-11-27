package ru.homepharmacy.data

import java.time.LocalDate
import java.time.format.DateTimeFormatter

// Простые функции без Android — их удобно проверять JUnit-тестами

private val dateFormat = DateTimeFormatter.ofPattern("dd.MM.yyyy")

fun formatDate(iso: String): String = LocalDate.parse(iso).format(dateFormat)

fun statusText(status: String, daysLeft: Int): String = when (status) {
    "expired" -> "Просрочено"
    "expiring" -> if (daysLeft == 0) "Истекает сегодня" else "Истекает через $daysLeft дн."
    else -> "Годен ещё $daysLeft дн."
}

fun validateLogin(email: String, password: String): String? = when {
    !email.contains("@") -> "Введите email"
    password.length < 8 -> "Пароль — не меньше 8 символов"
    else -> null
}

fun validatePackage(medicineId: Int?, date: LocalDate?, quantity: String): String? {
    val number = quantity.trim().toIntOrNull()
    return when {
        medicineId == null -> "Выберите препарат"
        date == null -> "Укажите срок годности"
        number == null -> "Количество — целое число"
        number !in 1..10000 -> "Количество — от 1 до 10 000"
        else -> null
    }
}
