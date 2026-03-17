[app]
title = AirSync
package.name = airsync
package.domain = org.airsync
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,tflite
version = 1.0

requirements = python3,kivy,opencv,numpy,tflite-runtime,plyer

android.permissions = CAMERA,ACCESS_WIFI_STATE,CHANGE_WIFI_STATE,\
    ACCESS_FINE_LOCATION,READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE,INTERNET

android.minapi = 26
android.ndk = 25b
android.archs = arm64-v8a, armeabi-v7a
