[app]
title = Neon Brick Breaker
package.name = neonbrickbreaker
package.domain = org.braia

source.dir = .
source.include_exts = py,png,jpg,kv,atlas
version = 0.3
source.exclude_dirs = tests,__pycache__

requirements = python3==3.11.9, kivy

# Recreate the build venv cleanly and avoid a mixed pip installation.
# p4a.branch = develop
# p4a.commit = 0382d27de2f7315ed98e74884bafb30365decdee

orientation = portrait

#
# Android specific
#

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
