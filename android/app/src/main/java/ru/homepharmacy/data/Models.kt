package ru.homepharmacy.data

import com.google.gson.annotations.SerializedName

// Модели повторяют JSON сервера (см. http://localhost:8000/docs)

data class RegisterRequest(val email: String, val password: String)

data class TokenResponse(@SerializedName("access_token") val accessToken: String)

data class User(val id: Int, val email: String)

data class Medicine(val id: Int, val name: String, val form: String?, val dosage: String?)

data class MedicineRequest(val name: String, val form: String?, val dosage: String?)

data class PackageItem(
    val id: Int,
    @SerializedName("medicine_id") val medicineId: Int,
    @SerializedName("medicine_name") val medicineName: String,
    @SerializedName("expiry_date") val expiryDate: String, // "ГГГГ-ММ-ДД"
    val quantity: Int,
    val location: String?,
    @SerializedName("days_left") val daysLeft: Int,
    val status: String, // ok, expiring, expired
)

data class PackageRequest(
    @SerializedName("medicine_id") val medicineId: Int,
    @SerializedName("expiry_date") val expiryDate: String,
    val quantity: Int,
    val location: String?,
)

data class PackageUpdateRequest(
    @SerializedName("expiry_date") val expiryDate: String,
    val quantity: Int,
    val location: String?,
)

data class Settings(
    @SerializedName("threshold_days") val thresholdDays: Int,
    @SerializedName("notifications_enabled") val notificationsEnabled: Boolean,
)
