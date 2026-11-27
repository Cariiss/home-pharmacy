package ru.homepharmacy.data

import com.google.gson.JsonParser
import retrofit2.HttpException
import java.io.IOException

// Превращает ошибку запроса в текст для пользователя
fun errorMessage(e: Throwable): String = when (e) {
    is HttpException -> detailFromBody(e.response()?.errorBody()?.string()) ?: "Ошибка сервера (код ${e.code()})"
    is IOException -> "Нет связи с сервером. Проверьте, что сервер запущен и приложению разрешён доступ к устройствам в сети."
    else -> "Что-то пошло не так: ${e.message}"
}

// Сервер присылает ошибки в виде {"detail": "текст"}
fun detailFromBody(body: String?): String? = try {
    JsonParser.parseString(body).asJsonObject.get("detail")?.asString
} catch (e: Exception) {
    null
}
