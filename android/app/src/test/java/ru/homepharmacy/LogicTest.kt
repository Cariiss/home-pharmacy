package ru.homepharmacy

import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Test
import ru.homepharmacy.data.detailFromBody
import ru.homepharmacy.data.formatDate
import ru.homepharmacy.data.statusText
import ru.homepharmacy.data.validateLogin
import ru.homepharmacy.data.validatePackage
import java.time.LocalDate

class LogicTest {

    @Test
    fun detailIsTakenFromServerError() {
        assertEquals("Лекарство не найдено", detailFromBody("""{"detail":"Лекарство не найдено"}"""))
        assertNull(detailFromBody("<html>Bad Gateway</html>"))
        assertNull(detailFromBody(null))
    }

    @Test
    fun dateIsShownInRussianFormat() {
        assertEquals("16.12.2026", formatDate("2026-12-16"))
    }

    @Test
    fun statusTextDependsOnStatus() {
        assertEquals("Просрочено", statusText("expired", -3))
        assertEquals("Истекает сегодня", statusText("expiring", 0))
        assertEquals("Истекает через 20 дн.", statusText("expiring", 20))
        assertEquals("Годен ещё 90 дн.", statusText("ok", 90))
    }

    @Test
    fun loginFormIsChecked() {
        assertEquals("Введите email", validateLogin("anna", "Secret123"))
        assertEquals("Пароль — не меньше 8 символов", validateLogin("anna@test.ru", "123"))
        assertNull(validateLogin("anna@test.ru", "Secret123"))
    }

    @Test
    fun packageFormIsChecked() {
        val date = LocalDate.of(2027, 1, 1)
        assertEquals("Выберите препарат", validatePackage(null, date, "1"))
        assertEquals("Укажите срок годности", validatePackage(1, null, "1"))
        assertEquals("Количество — целое число", validatePackage(1, date, "два"))
        assertEquals("Количество — от 1 до 10 000", validatePackage(1, date, "0"))
        assertEquals("Количество — от 1 до 10 000", validatePackage(1, date, "10001"))
        assertNull(validatePackage(1, date, " 5 "))
    }
}
