package ru.homepharmacy.data

import com.google.gson.GsonBuilder
import kotlinx.coroutines.runBlocking
import okhttp3.OkHttpClient
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory
import retrofit2.http.Body
import retrofit2.http.DELETE
import retrofit2.http.Field
import retrofit2.http.FormUrlEncoded
import retrofit2.http.GET
import retrofit2.http.POST
import retrofit2.http.PUT
import retrofit2.http.Path
import retrofit2.http.Query
import java.util.concurrent.TimeUnit

interface Api {
    @POST("auth/register")
    suspend fun register(@Body body: RegisterRequest): User

    // вход принимает форму, а не JSON
    @FormUrlEncoded
    @POST("auth/login")
    suspend fun login(@Field("username") email: String, @Field("password") password: String): TokenResponse

    @GET("auth/me")
    suspend fun me(): User

    @GET("medicines")
    suspend fun medicines(): List<Medicine>

    @POST("medicines")
    suspend fun addMedicine(@Body body: MedicineRequest): Medicine

    @PUT("medicines/{id}")
    suspend fun updateMedicine(@Path("id") id: Int, @Body body: MedicineRequest): Medicine

    @DELETE("medicines/{id}")
    suspend fun deleteMedicine(@Path("id") id: Int)

    @GET("packages")
    suspend fun packages(@Query("status") status: String?, @Query("q") query: String?): List<PackageItem>

    @GET("packages/{id}")
    suspend fun getPackage(@Path("id") id: Int): PackageItem

    @POST("packages")
    suspend fun addPackage(@Body body: PackageRequest): PackageItem

    @PUT("packages/{id}")
    suspend fun updatePackage(@Path("id") id: Int, @Body body: PackageUpdateRequest): PackageItem

    @DELETE("packages/{id}")
    suspend fun deletePackage(@Path("id") id: Int)

    @GET("settings")
    suspend fun settings(): Settings

    @PUT("settings")
    suspend fun updateSettings(@Body body: Settings): Settings
}

fun createApi(baseUrl: String, tokenStore: TokenStore): Api {
    val client = OkHttpClient.Builder()
        .connectTimeout(15, TimeUnit.SECONDS)
        .readTimeout(15, TimeUnit.SECONDS)
        .addInterceptor { chain ->
            // к каждому запросу добавляем токен, если пользователь вошёл
            val token = tokenStore.token.value
            val request = if (token == null) chain.request()
            else chain.request().newBuilder().header("Authorization", "Bearer $token").build()
            val response = chain.proceed(request)
            // токен истёк или недействителен — выходим, приложение покажет экран входа
            if (response.code == 401 && token != null) runBlocking { tokenStore.clear() }
            response
        }
        .build()

    // serializeNulls: чтобы пустое место хранения уходило на сервер как null и стиралось
    val gson = GsonBuilder().serializeNulls().create()

    return Retrofit.Builder()
        .baseUrl(baseUrl)
        .client(client)
        .addConverterFactory(GsonConverterFactory.create(gson))
        .build()
        .create(Api::class.java)
}
