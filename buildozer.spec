[app]
title = Neon Brick Breaker
package.name = neonbrickbreaker
package.domain = org.braia

source.dir = .
source.include_exts = py,png,jpg,kv,atlas
version = 0.1

requirements = python3, kivy

orientation = portrait

osx.python_version = 3
osx.kivy_version = 1.9.1

fullscreen = 1

android.permissions = INTERNET
android.api = 33
android.minapi = 31
android.ndk = 25b

android.accept_sdk_license = True
android.archs = arm64-v8a, armeabi-v7a

[buildozer]
log_level = 2
warn_on_root = 1
