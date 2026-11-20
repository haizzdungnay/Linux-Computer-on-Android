plugins { id("com.android.application") }

android {
    namespace = "dev.local.linuxdesktop.launcher"
    compileSdk = 36
    defaultConfig {
        applicationId = "dev.local.linuxdesktop.launcher"
        minSdk = 23
        targetSdk = 36
        versionCode = 1
        versionName = "1.0"
    }
}

dependencies { testImplementation("junit:junit:4.13.2") }
