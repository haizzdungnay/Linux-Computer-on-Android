plugins { id("com.android.application") }

android {
    namespace = "dev.local.linuxdesktop.launcher"
    compileSdk = 36
    defaultConfig {
        applicationId = "dev.local.linuxdesktop.launcher"
        minSdk = 26
        targetSdk = 28
        versionCode = 2
        versionName = "2.0"
        ndk {
            abiFilters += "arm64-v8a"
        }
    }
    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_11
        targetCompatibility = JavaVersion.VERSION_11
    }
    packaging {
        jniLibs {
            useLegacyPackaging = true
        }
    }
}

dependencies {
    implementation(project(":lorie"))
    implementation("androidx.appcompat:appcompat:1.7.0")
    implementation("org.apache.commons:commons-compress:1.27.1")
    implementation("org.tukaani:xz:1.10")
    testImplementation("junit:junit:4.13.2")
}
