plugins {
    alias(libs.plugins.android.application)
    alias(libs.plugins.kotlin.compose)
}

android {
    namespace = "ru.homepharmacy"
    // Compose требует платформу Android 37.2
    compileSdk {
        version = release(37) { minorApiLevel = 2 }
    }

    defaultConfig {
        applicationId = "ru.homepharmacy"
        minSdk = 26
        targetSdk = 37
        versionCode = 1
        versionName = "1.0"

        // Адрес сервера. По умолчанию — компьютер, если смотреть из эмулятора.
        // Для телефона: ./gradlew installDebug -PapiUrl=http://<IP компьютера>:8000/
        val apiUrl = project.findProperty("apiUrl") as String? ?: "http://10.0.2.2:8000/"
        buildConfigField("String", "API_URL", "\"$apiUrl\"")
    }

    buildFeatures {
        compose = true
        buildConfig = true
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
}

dependencies {
    implementation(libs.androidx.core.ktx)
    implementation(libs.androidx.activity.compose)
    implementation(libs.androidx.lifecycle.viewmodel.compose)
    implementation(libs.androidx.lifecycle.runtime.compose)
    implementation(libs.androidx.navigation.compose)
    implementation(libs.androidx.datastore.preferences)
    implementation(platform(libs.compose.bom))
    implementation(libs.compose.ui)
    implementation(libs.compose.material3)
    implementation(libs.compose.material.icons)
    implementation(libs.retrofit)
    implementation(libs.retrofit.gson)

    testImplementation(libs.junit)
}
